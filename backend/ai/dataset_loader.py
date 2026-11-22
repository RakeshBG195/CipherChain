"""
Dataset loading. Produces a pandas DataFrame with columns: text, label (SAFE | SPAM | PHISHING), source.

Supported real datasets (you must download them yourself - nothing is downloaded automatically):
  * UCI SMS Spam Collection  - tab separated file 'SMSSpamCollection' (label \t text), ham->SAFE, spam->SPAM.
                               Also accepts the common Kaggle 'spam.csv' (columns v1, v2; latin-1 encoding).
  * Labeled phishing e-mail CSV (e.g. the Kaggle "Phishing Email Dataset" with 'Email Text','Email Type',
    or any CSV with a text column and a label column). Labels containing 'phish' -> PHISHING,
    'safe'/'ham'/'legit'/'not' -> SAFE, 'spam' -> SPAM, numeric 1 -> PHISHING, 0 -> SAFE.
"""
from pathlib import Path
from typing import Optional

import pandas as pd

LABELS = ["SAFE", "SPAM", "PHISHING"]
TEXT_COLS = ["text", "email text", "email_text", "body", "message", "content", "v2", "sms", "email"]
LABEL_COLS = ["label", "email type", "email_type", "type", "class", "category", "v1", "target"]


def _norm_label(v) -> Optional[str]:
    s = str(v).strip().lower()
    if "phish" in s or "smish" in s:
        return "PHISHING"
    if s in ("spam", "junk"):
        return "SPAM"
    if s in ("ham", "safe", "safe email", "legit", "legitimate", "not spam", "benign", "0", "0.0"):
        return "SAFE"
    if s in ("1", "1.0"):
        return "PHISHING"
    return None


def _pick(columns, candidates):
    lower = {c.lower().strip(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


def load_sms_spam(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"SMS dataset not found: {p}")
    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p, encoding="latin-1")
        lc, tc = _pick(df.columns, ["v1", "label"]), _pick(df.columns, ["v2", "text"])
        df = df[[lc, tc]].rename(columns={lc: "label", tc: "text"})
    else:  # original UCI format: "<ham|spam>\t<text>"
        df = pd.read_csv(p, sep="\t", header=None, names=["label", "text"], encoding="latin-1", quoting=3)
    df["label"] = df["label"].map(lambda v: {"ham": "SAFE", "spam": "SPAM"}.get(str(v).strip().lower()))
    df["source"] = "uci_sms_spam"
    return df


def load_phishing_csv(path: str, text_col: Optional[str] = None, label_col: Optional[str] = None) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Phishing dataset not found: {p}")
    df = pd.read_csv(p, encoding="utf-8", encoding_errors="replace")
    tc = text_col or _pick(df.columns, TEXT_COLS)
    lc = label_col or _pick(df.columns, LABEL_COLS)
    if tc is None or lc is None:
        raise ValueError(f"Could not detect text/label columns in {list(df.columns)}; pass --text-col/--label-col")
    out = pd.DataFrame({"text": df[tc], "label": df[lc].map(_norm_label)})
    out["source"] = f"phishing_csv:{p.name}"
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.dropna(subset=["text", "label"]).copy()

    df["text"] = df["text"].astype(str).str.strip()

    df = df[
        (df["text"].str.len() > 0) &
        (df["label"].isin(LABELS))
    ].copy()

    # Find messages that have multiple different labels
    label_counts = df.groupby("text")["label"].nunique()
    conflicting_texts = label_counts[label_counts > 1].index

    # Remove all conflicting messages
    df = df[~df["text"].isin(conflicting_texts)].copy()

    # Remove remaining duplicate messages
    df = df.drop_duplicates(subset=["text"])

    return df.reset_index(drop=True)