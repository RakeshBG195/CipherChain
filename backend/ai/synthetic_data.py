"""
SYNTHETIC DEMO DATA - NOT REAL-WORLD DATA.

Template-generated messages used ONLY so the pipeline can run end-to-end when no real labeled dataset is
supplied. Because the messages come from a small number of templates, any metric computed on them is
artificially high and says NOTHING about real-world spam/phishing detection performance.
"""
import random

SAFE_T = [
    "hey are we still meeting for {meal} at {t}?", "can you send me the notes from {subj} class",
    "i will be late, stuck in traffic, see you in {n} minutes", "thanks for the help with the {subj} assignment",
    "happy birthday {name}! hope you have a great day", "did you finish the {subj} lab report yet",
    "mom said dinner is ready, come home soon", "the project meeting is moved to {t} tomorrow",
    "lol that movie was so funny last night", "please review my pull request when you get a chance",
    "i'm at the library, want to study {subj} together?", "reminder: submit the {subj} slides by friday",
]
SPAM_T = [
    "WINNER! you have won a free {prize}, text CLAIM to {n} now", "congratulations you won ${n} cash prize call {n} today",
    "limited offer buy one get one free on all {prize}, order now", "free entry in our weekly draw to win a {prize}, reply WIN",
    "get cheap pills online no prescription needed discount {n} percent", "you have been selected for an exclusive deal on {prize}, click now",
    "earn ${n} per day working from home, no experience needed, sign up", "hot singles in your area want to chat, call {n} now",
    "urgent! claim your free {prize} before the offer expires tonight", "act now: lowest price guaranteed on {prize}, unsubscribe reply STOP",
]
PHISH_T = [
    "your {bank} account has been suspended, verify your password at http://{dom}.xyz/login immediately",
    "security alert: unusual sign in detected, confirm your identity at www.{dom}-secure.com or your account will be closed",
    "dear customer your {bank} card is locked, update your billing information here http://{dom}.top/verify",
    "we could not process your payment, log in to {bank} at http://{dom}.ru/pay to avoid account termination",
    "your {bank} online banking password expires today, click http://{dom}.tk/reset to keep access",
    "irs tax refund of ${n} pending, submit your social security number and bank details at www.{dom}-refund.net",
    "package delivery failed, confirm your address and card details at http://{dom}.info/track within 24 hours",
    "verify your account now: http://{dom}.biz/confirm failure to respond will result in permanent suspension",
]
FILL = dict(meal=["lunch", "dinner", "coffee"], t=["5pm", "7:30", "noon", "9am"], subj=["physics", "math", "network security", "chemistry", "dbms"],
            n=["5", "10", "500", "1000", "85", "86688", "20"], name=["sam", "priya", "alex", "john"],
            prize=["iphone", "laptop", "gift card", "holiday trip", "tv"], bank=["paypal", "hdfc", "chase", "amazon", "netflix", "apple"],
            dom=["secure-login", "account-verify", "update-info", "support-center", "auth-check"])


def _fill(tpl, rng):
    out = tpl
    for k, vals in FILL.items():
        while "{" + k + "}" in out:
            out = out.replace("{" + k + "}", rng.choice(vals), 1)
    return out


def generate(n_per_class: int = 300, seed: int = 42):
    import pandas as pd
    rng = random.Random(seed)
    rows = []
    for label, tpls in (("SAFE", SAFE_T), ("SPAM", SPAM_T), ("PHISHING", PHISH_T)):
        for _ in range(n_per_class):
            rows.append((_fill(rng.choice(tpls), rng), label, "SYNTHETIC_DEMO"))
    return pd.DataFrame(rows, columns=["text", "label", "source"]).drop_duplicates(subset=["text"]).reset_index(drop=True)
