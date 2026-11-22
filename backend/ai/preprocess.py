"""Text normalisation used by BOTH training and inference (it is pickled inside the saved vectorizer)."""
import re

_URL = re.compile(r"(https?://\S+|www\.\S+|\b[\w-]+\.(?:com|net|org|info|biz|xyz|top|ru|tk|ly|co)\b/?\S*)", re.I)
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_NUM = re.compile(r"\d+")
_CUR = re.compile(r"[$£€]")
_NONWORD = re.compile(r"[^a-z\s]")
_WS = re.compile(r"\s+")


def preprocess_text(text: str) -> str:
    t = (text or "").lower()
    t = _URL.sub(" urltoken ", t)
    t = _EMAIL.sub(" emailtoken ", t)
    t = _CUR.sub(" currencytoken ", t)
    t = _NUM.sub(" numtoken ", t)
    t = _NONWORD.sub(" ", t)
    return _WS.sub(" ", t).strip()
