from datetime import timedelta

LIMITATION_PERIODS = {
    "slp": {"days": 90, "basis": "Article 136, Constitution + Article 116, Limitation Act"},
    "lpa": {"days": 30, "basis": "Letters Patent / High Court practice"},
    "review": {"days": 30, "basis": "Order 47 Rule 1 CPC"},
    "writ_appeal": {"days": 30, "basis": "High Court writ appeal practice"},
    "compliance": {"days": 30, "basis": "Administrative compliance window"},
}


def compute_deadlines(judgment_date, order_type: str = "", recommendation: str = "comply"):
    key = (order_type or recommendation or "compliance").lower()
    period = LIMITATION_PERIODS.get(key, LIMITATION_PERIODS["compliance"])
    legal_deadline = judgment_date + timedelta(days=period["days"])
    internal_deadline = judgment_date + timedelta(days=max(7, period["days"] - 14))
    return {
        "legal_deadline": legal_deadline,
        "internal_deadline": internal_deadline,
        "basis": period["basis"],
    }
