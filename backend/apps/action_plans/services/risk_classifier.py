"""
Contempt Risk Classifier — Hybrid: InLegalBERT (if available) + Keyword Fallback.

If the fine-tuned InLegalBERT model exists at ml_models/contempt_classifier/,
it will be loaded and used for inference. Otherwise, falls back to the
deterministic keyword-based classifier.
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================
# 1. Try to load InLegalBERT fine-tuned model
# ============================================================
_bert_classifier = None
_bert_available = False

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "ml_models",
    "contempt_classifier",
)

try:
    if os.path.exists(os.path.join(MODEL_PATH, "config.json")):
        from transformers import pipeline

        _bert_classifier = pipeline(
            "text-classification",
            model=MODEL_PATH,
            tokenizer=MODEL_PATH,
            device=-1,  # CPU (use 0 for GPU)
        )
        _bert_available = True
        logger.info("InLegalBERT contempt classifier loaded from %s", MODEL_PATH)
    else:
        logger.info("InLegalBERT model not found at %s — using keyword fallback", MODEL_PATH)
except Exception as e:
    logger.warning("Failed to load InLegalBERT: %s — using keyword fallback", e)


# ============================================================
# 2. Keyword-based fallback classifier (deterministic)
# ============================================================

HIGH_RISK_PHRASES = [
    "failing which",
    "shall comply",
    "threat of contempt",
    "coercive action",
    "personal appearance",
    "immediate compliance",
    "without fail",
    "contempt proceedings",
    "contempt of court",
    "willful disobedience",
    "personal affidavit",
    "appear in person",
    "benchwarrant",
    "civil prison",
    "attachment of property",
    "penal interest",
    "show cause",
    "last opportunity",
    "serious note",
    "defiant attitude",
    "personally liable",
    "personally ensure",
    "constrained to initiate",
]

MEDIUM_RISK_PHRASES = [
    "directed to",
    "respond within",
    "consider the representation",
    "take appropriate action",
    "shall pay",
    "shall deposit",
    "shall complete",
    "shall ensure",
    "within 30 days",
    "within 60 days",
    "within 4 weeks",
    "with interest",
    "reinstate the petitioner",
    "restore the",
    "comply with",
    "pass appropriate orders",
    "spot inspection",
    "file report",
    "submit compliance",
]


def _keyword_classify(text: str) -> str:
    """Deterministic keyword-based classification (fallback)."""
    lowered = (text or "").lower()

    # Count matches for scoring
    high_matches = sum(1 for phrase in HIGH_RISK_PHRASES if phrase in lowered)
    medium_matches = sum(1 for phrase in MEDIUM_RISK_PHRASES if phrase in lowered)

    if high_matches >= 2:
        return "High"
    if high_matches == 1:
        return "High"
    if medium_matches >= 2:
        return "Medium"
    if medium_matches == 1:
        return "Medium"
    return "Low"


# ============================================================
# 3. Main classifier function
# ============================================================

def classify_contempt_risk(text: str) -> str:
    """
    Classify contempt risk level from operative order text.

    Returns: "High", "Medium", or "Low"

    Uses InLegalBERT if the fine-tuned model is available,
    otherwise falls back to deterministic keyword matching.
    """
    if not text or not text.strip():
        return "Low"

    # Try BERT first
    if _bert_available and _bert_classifier:
        try:
            result = _bert_classifier(text[:512])[0]
            label = result["label"]
            confidence = result["score"]

            # Map BERT output labels
            if "2" in label or "High" in label:
                risk = "High"
            elif "1" in label or "Medium" in label:
                risk = "Medium"
            else:
                risk = "Low"

            logger.debug("BERT classified as %s (confidence: %.3f)", risk, confidence)
            return risk
        except Exception as e:
            logger.warning("BERT inference failed: %s — using keyword fallback", e)

    # Keyword fallback
    return _keyword_classify(text)
