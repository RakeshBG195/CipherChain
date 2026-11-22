import json, tempfile, unittest
from pathlib import Path
import pandas as pd
from backend.ai.dataset_loader import load_sms_spam, load_phishing_csv, clean
from backend.ai.preprocess import preprocess_text
from backend.ai.predictor import Predictor, ModelNotLoaded
from backend.ai.synthetic_data import generate
from backend.ai.training import train


class AITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.metrics = train(generate(200), cls.dir, synthetic=True, dataset_description="unit-test synthetic")
        cls.pred = Predictor(cls.dir)

    def test_preprocess(self):
        self.assertEqual(preprocess_text("Visit http://evil.xyz/login NOW! Win $500"), "visit urltoken now win currencytoken numtoken")

    def test_artifacts_saved_separately(self):
        for n in ("spam_phishing_model.joblib", "tfidf_vectorizer.joblib", "metrics.json"):
            self.assertTrue((self.dir / n).exists(), n)

    def test_metrics_flagged_synthetic_and_consistent(self):
        m = json.loads((self.dir / "metrics.json").read_text())
        self.assertTrue(m["synthetic_data"]); self.assertIsNotNone(m["warning"])
        cm = m["confusion_matrix"]["matrix"]
        self.assertEqual(sum(map(sum, cm)), m["n_test"])
        acc = sum(cm[i][i] for i in range(len(cm))) / m["n_test"]
        self.assertAlmostEqual(acc, m["accuracy"], places=9)   # accuracy re-derived from the confusion matrix

    def test_no_train_test_overlap(self):
        df = generate(200)
        self.assertEqual(len(df), df["text"].nunique())

    def test_predict_shape_and_ranges(self):
        for text in ("are we still on for lunch at noon?", "WINNER you won a free iphone, text CLAIM now",
                     "your paypal account is suspended verify your password at http://secure-login.xyz/login"):
            r = self.pred.predict(text)
            self.assertIn(r["category"], ("SAFE", "SPAM", "PHISHING"))
            self.assertTrue(0 <= r["risk_score"] <= 100 and 0 <= r["confidence"] <= 1)
            self.assertAlmostEqual(sum(r["probabilities"].values()), 1.0, places=2)
            self.assertTrue(r["explanation"])

    def test_missing_model_raises(self):
        with self.assertRaises(ModelNotLoaded):
            Predictor(self.dir / "nope")

    def test_loaders(self):
        d = self.dir
        (d / "SMSSpamCollection").write_text("ham\tok see you\nspam\tWIN a prize now\nham\tcall me\n", encoding="latin-1")
        df = load_sms_spam(str(d / "SMSSpamCollection"))
        self.assertEqual(list(df["label"]), ["SAFE", "SPAM", "SAFE"])
        pd.DataFrame({"Email Text": ["verify your account", "meeting notes", None], "Email Type": ["Phishing Email", "Safe Email", "Safe Email"]}).to_csv(d / "p.csv", index=False)
        df2 = clean(load_phishing_csv(str(d / "p.csv")))
        self.assertEqual(sorted(df2["label"]), ["PHISHING", "SAFE"])



class CorruptModelTest(unittest.TestCase):
    def test_corrupt_pickle_gives_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "spam_phishing_model.joblib").write_bytes(b"not a pickle")
            (Path(d) / "tfidf_vectorizer.joblib").write_bytes(b"not a pickle")
            with self.assertRaises(ModelNotLoaded):
                Predictor(Path(d))


if __name__ == "__main__":
    unittest.main()
