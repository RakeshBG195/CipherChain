"""Real-time inference using the SAVED model + vectorizer. No hard-coded predictions."""
import json
import re
import threading
from pathlib import Path
from typing import Optional

import joblib
import numpy as np

from backend.config import MODEL_DIR
from backend.ai.preprocess import preprocess_text  # noqa: F401  (needed so joblib can unpickle the vectorizer)


class ModelNotLoaded(RuntimeError):
    pass


_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.I)
_SUSPICIOUS_TLD = re.compile(r"\.(xyz|top|tk|ru|biz|info|click|work)\b", re.I)
_URGENCY = ("urgent", "immediately", "within 24 hours", "suspended", "expires", "act now", "final notice", "locked")
_CREDENTIAL = ("password", "verify your", "confirm your identity", "social security", "card number", "pin", "login", "log in")


def indicators(text: str) -> list:
    """Human-readable surface cues. Shown beside (NOT used by) the ML prediction."""
    low = text.lower(); out = []
    urls = _URL_RE.findall(text)
    if urls:
        out.append(f"Contains {len(urls)} link(s)")
    if _SUSPICIOUS_TLD.search(text):
        out.append("Link uses a domain extension often abused in phishing")
    if any(w in low for w in _URGENCY):
        out.append("Urgency / threat language")
    if any(w in low for w in _CREDENTIAL):
        out.append("Requests credentials or personal data")
    if re.search(r"[$£€]\s?\d|\bfree\b|\bwon\b|\bprize\b", low):
        out.append("Money / prize wording")
    return out


class Predictor:
    def __init__(self, model_dir: Path = MODEL_DIR):
        self.model_dir = Path(model_dir)
        mp, vp = self.model_dir / "spam_phishing_model.joblib", self.model_dir / "tfidf_vectorizer.joblib"
        if not mp.exists() or not vp.exists():
            raise ModelNotLoaded(f"Model files not found in {self.model_dir}. Run: python -m scripts.train_model --synthetic "
                                 "(demo only) or supply real datasets.")
        try:
            self.model = joblib.load(mp)
            self.vectorizer = joblib.load(vp)
        except Exception as exc:  # e.g. pickle saved with a different scikit-learn version
            raise ModelNotLoaded(f"Could not load model files ({type(exc).__name__}: {exc}). Retrain locally: "
                                 "python -m scripts.train_model --synthetic (demo) or with real datasets.") from exc
        self.classes = list(self.model.classes_)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())
        mj = self.model_dir / "metrics.json"
        self.metrics = json.loads(mj.read_text()) if mj.exists() else None

    def predict(self, text: str) -> dict:
        X = self.vectorizer.transform([text])
        proba = self.model.predict_proba(X)[0]
        idx = int(np.argmax(proba)); label = self.classes[idx]
        p_safe = float(proba[self.classes.index("SAFE")]) if "SAFE" in self.classes else 0.0
        # contribution of each TF-IDF feature to the predicted class logit
        coefs = self.model.coef_[idx] if self.model.coef_.shape[0] > 1 else (self.model.coef_[0] if idx == 1 else -self.model.coef_[0])
        row = X.tocoo()
        contrib = sorted(((float(coefs[c] * v), self.feature_names[c]) for c, v in zip(row.col, row.data)), reverse=True)
        top = [{"term": t, "weight": round(w, 4)} for w, t in contrib if w > 0][:6]
        ind = indicators(text)
        if label == "SAFE":
            expl = "The model found no strong spam or phishing patterns."
        else:
            expl = f"Classified as {label}: " + (", ".join(f"'{t['term']}'" for t in top[:4]) or "overall wording pattern") + \
                   " pushed the score toward this class."
        return {
            "category": label, "confidence": round(float(proba[idx]), 4), "risk_score": round((1.0 - p_safe) * 100, 1),
            "probabilities": {c: round(float(p), 4) for c, p in zip(self.classes, proba)},
            "top_terms": top, "indicators": ind, "explanation": expl,
        }


_lock = threading.Lock()
_instance: Optional[Predictor] = None


def get_predictor(reload: bool = False) -> Predictor:
    global _instance
    with _lock:
        if _instance is None or reload:
            _instance = Predictor()
        return _instance
