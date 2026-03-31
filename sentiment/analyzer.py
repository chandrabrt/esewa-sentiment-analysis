from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def analyze(text: str) -> dict:
    """Return sentiment label and compound score for the given text."""
    if not text or not text.strip():
        return {"sentiment": "neutral", "score": 0.0}

    scores = _analyzer.polarity_scores(text)
    compound = round(scores["compound"], 4)

    if compound >= 0.05:
        label = "positive"
    elif compound <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {"sentiment": label, "score": compound}
