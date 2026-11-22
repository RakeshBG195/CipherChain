"""Training pipeline: preprocess -> TF-IDF -> Logistic Regression -> honest held-out evaluation -> save artifacts."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

from backend.ai.preprocess import preprocess_text

SYNTHETIC_WARNING = ("These metrics were computed on SYNTHETIC template-generated data. They are NOT indicative of "
                     "real-world spam/phishing detection performance. Retrain with real labeled datasets.")


def train(df, out_dir: Path, test_size: float = 0.2, seed: int = 42, synthetic: bool = False,
          dataset_description: Optional[str] = None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=test_size, random_state=seed, stratify=df["label"])

    vectorizer = TfidfVectorizer(preprocessor=preprocess_text, ngram_range=(1, 2), min_df=2 if len(df) > 1000 else 1,
                                 sublinear_tf=True, max_features=50000)
    Xtr = vectorizer.fit_transform(X_train)          # fitted on TRAIN only -> no test leakage
    Xte = vectorizer.transform(X_test)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=5.0, random_state=seed)
    clf.fit(Xtr, y_train)

    pred = clf.predict(Xte)
    labels = list(clf.classes_)
    p, r, f, s = precision_recall_fscore_support(y_test, pred, labels=labels, zero_division=0)
    mp, mr, mf, _ = precision_recall_fscore_support(y_test, pred, average="macro", zero_division=0)
    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_data": bool(synthetic),
        "warning": SYNTHETIC_WARNING if synthetic else None,
        "dataset": dataset_description or "unspecified",
        "sources": df["source"].value_counts().to_dict(),
        "classes": labels,
        "class_distribution_total": df["label"].value_counts().to_dict(),
        "n_train": int(len(X_train)), "n_test": int(len(X_test)), "test_size": test_size, "seed": seed,
        "accuracy": float(accuracy_score(y_test, pred)),
        "macro_precision": float(mp), "macro_recall": float(mr), "macro_f1": float(mf),
        "per_class": {l: {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i]), "support": int(s[i])}
                      for i, l in enumerate(labels)},
        "confusion_matrix": {"labels": labels, "matrix": confusion_matrix(y_test, pred, labels=labels).tolist()},
        "n_features": int(Xtr.shape[1]),
        "model": "TfidfVectorizer(1-2gram, sublinear_tf) + LogisticRegression(class_weight=balanced)",
        "limitations": [
            "Evaluated on a single stratified hold-out split, not cross-validated.",
            "Spam/phishing language drifts over time; accuracy on new campaigns will be lower.",
            "Messages are short chat texts; most public datasets are SMS or long e-mails (domain mismatch).",
        ],
    }
    joblib.dump(clf, out_dir / "spam_phishing_model.joblib")
    joblib.dump(vectorizer, out_dir / "tfidf_vectorizer.joblib")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics
