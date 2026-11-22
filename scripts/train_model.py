"""
Retrainable training script.   Run from the project root:

  Real data (recommended):
    python -m scripts.train_model --sms datasets/SMSSpamCollection --phishing datasets/phishing_email.csv
  Demo only (SYNTHETIC data, metrics are NOT meaningful):
    python -m scripts.train_model --synthetic
"""
import argparse
import json
import sys

import pandas as pd

from backend.ai import dataset_loader as dl
from backend.ai.synthetic_data import generate
from backend.ai.training import train
from backend.config import MODEL_DIR


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sms", help="UCI SMS Spam Collection file (SMSSpamCollection or spam.csv)")
    ap.add_argument("--phishing", help="labeled phishing CSV")
    ap.add_argument("--text-col"); ap.add_argument("--label-col")
    ap.add_argument("--synthetic", action="store_true", help="use SYNTHETIC demo data (not real-world)")
    ap.add_argument("--synthetic-size", type=int, default=300)
    ap.add_argument("--test-size", type=float, default=0.2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default=str(MODEL_DIR))
    a = ap.parse_args()

    frames, desc = [], []
    if a.sms:
        frames.append(dl.load_sms_spam(a.sms)); desc.append(f"UCI SMS Spam Collection ({a.sms})")
    if a.phishing:
        frames.append(dl.load_phishing_csv(a.phishing, a.text_col, a.label_col)); desc.append(f"phishing CSV ({a.phishing})")
    synthetic = False
    if a.synthetic:
        frames.append(generate(a.synthetic_size, a.seed)); desc.append("SYNTHETIC demo data"); synthetic = True
    if not frames:
        sys.exit("No data given. Use --sms/--phishing with real datasets, or --synthetic for a demo model.")

    df = dl.clean(pd.concat(frames, ignore_index=True))
    classes = sorted(df["label"].unique())
    print("Class distribution:\n", df["label"].value_counts().to_string())
    if set(classes) != set(dl.LABELS):
        print(f"WARNING: dataset only contains classes {classes}; the model will not be able to predict the missing ones. "
              "Provide both --sms and --phishing for the full SAFE/SPAM/PHISHING model.", file=sys.stderr)
    if len(classes) < 2:
        sys.exit("Need at least two classes to train.")
    # any synthetic rows in the mix make the metrics non-real-world
    m = train(df, a.out_dir, a.test_size, a.seed, synthetic=synthetic, dataset_description="; ".join(desc))
    print(json.dumps({k: m[k] for k in ("synthetic_data", "dataset", "n_train", "n_test", "accuracy", "macro_precision",
                                        "macro_recall", "macro_f1")}, indent=2))
    print("Confusion matrix", m["confusion_matrix"])
    if synthetic:
        print("\n*** " + m["warning"] + " ***")
    print(f"Saved model, vectorizer and metrics.json to {a.out_dir}")


if __name__ == "__main__":
    main()
