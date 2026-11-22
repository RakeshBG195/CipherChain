# Datasets (not included - download them yourself)

| Dataset | Where | Put it here |
|---|---|---|
| UCI SMS Spam Collection (5,574 labeled SMS; ham/spam) | https://archive.ics.uci.edu/dataset/228/sms+spam+collection | `datasets/SMSSpamCollection` (the tab-separated file inside the zip) |
| A labeled phishing e-mail/message CSV (e.g. Kaggle "Phishing Email Dataset") | https://www.kaggle.com (search "phishing email dataset") | `datasets/phishing_email.csv` |

`python -m scripts.train_model --sms datasets/SMSSpamCollection --phishing datasets/phishing_email.csv`

Notes: the SMS set has no PHISHING class, so a phishing dataset is required for the full 3-class model. Public
datasets are SMS/e-mail, not chat messages - expect a domain gap. Check each dataset's licence before redistributing.
Nothing in this repository downloads data automatically.
