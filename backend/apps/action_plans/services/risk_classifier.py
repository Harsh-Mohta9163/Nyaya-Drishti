HIGH_RISK_PHRASES = [
    "failing which",
    "shall comply",
    "threat of contempt",
    "coercive action",
    "personal appearance",
    "immediate compliance",
    "without fail",
]

MEDIUM_RISK_PHRASES = [
    "directed to",
    "respond within",
    "consider the representation",
    "take appropriate action",
]


def classify_contempt_risk(text: str) -> str:
    lowered = (text or "").lower()
    if any(phrase in lowered for phrase in HIGH_RISK_PHRASES):
        return "High"
    if any(phrase in lowered for phrase in MEDIUM_RISK_PHRASES):
        return "Medium"
    return "Low"
