"""
Structure-aware judgment segmenter — Bi-directional Scanning.

Splits a Karnataka HC judgment into: header, body, operative_order.

Algorithm:
  1. HEADER END (top-down): Scan from top until first narrative trigger
     ("This petition is filed...", "Heard learned counsel...", etc.)
  2. OPERATIVE START (bottom-up): Scan from bottom until disposal trigger
     ("For the foregoing reasons...", "ORDER", "Petition is allowed...", etc.)
  3. BODY: Everything between header_end and operative_start.
  4. OVERLAP: 10% bidirectional so no reasoning is lost at boundaries.
"""
import re

# ─── NARRATIVE TRIGGERS (top-down: marks where the facts/body begins) ───
_NARRATIVE_TRIGGERS = [
    r"This\s+(writ\s+)?petition\s+is\s+filed",
    r"This\s+appeal\s+is\s+(filed|preferred|directed|directed\s+against)",
    r"The\s+(brief\s+)?facts\s+(of\s+the\s+case|leading\s+to\s+this)",
    r"The\s+petitioner\s+(herein\s+)?has\s+filed",
    r"The\s+appellant\s+(herein\s+)?has\s+preferred",
    r"Heard\s+(the\s+)?learned\s+(counsel|senior\s+counsel|advocate|Sr\.\s*Counsel)",
    r"Having\s+heard\s+(the\s+)?learned",
    r"Having\s+considered",
    r"The\s+case\s+of\s+the\s+(petitioner|appellant|prosecution|respondent)",
    r"The\s+(brief\s+)?background\s+of\s+the\s+case",
    r"Sri\.?\s+\w+.*learned\s+(counsel|advocate)\s+for",
    r"The\s+learned\s+(counsel|advocate)\s+for\s+the",
    r"PRAYER\b",
    r"FACTS\b",
    r"BRIEF\s+FACTS",
    r"BACKGROUND\b",
    r"Factual\s+matrix\s+of\s+the\s+case",
    r"The\s+short\s+facts\s+are",
    r"It\s+is\s+the\s+case\s+of\s+the",
]

# ─── DISPOSAL TRIGGERS (bottom-up: marks where the order begins) ───
_DISPOSAL_TRIGGERS = [
    # Strong standalone headings (most reliable)
    r"^\s*\**\s*ORDER\s*\**\s*$",
    r"^\s*\**\s*DIRECTIONS?\s*\**\s*$",
    r"^\s*\**\s*OPERATIVE\s+PORTION\s*\**\s*$",
    r"^\s*\**\s*FINAL\s+ORDER\s*\**\s*$",
    r"^\s*\**\s*SENTENCE\s*\**\s*$",
    # Formulaic preamble to the order
    r"For\s+the\s+(foregoing|above|aforesaid)\s+reasons",
    r"For\s+the\s+aforesaid\s+reasons",
    r"In\s+view\s+of\s+the\s+(above|foregoing|discussions?|observations?)",
    r"In\s+the\s+result",
    r"For\s+these\s+reasons",
    r"For\s+the\s+reasons\s+stated\s+above",
    r"I\s+(therefore\s+)?pass\s+the\s+following",
    r"The\s+following\s+order\s+is\s+(made|passed)",
    r"We\s+are\s+of\s+the\s+considered\s+view",
    r"Consequently,?\s+the\s+(following|writ)",
    # Criminal appeal / sentencing triggers
    r"We\s+now\s+proceed\s+to\s+sentence",
    r"we\s+proceed\s+to\s+(pass\s+the\s+following|sentence|hear)",
    r"The\s+sentence\s+is\s+as\s+follows",
    r"we\s+sentence\s+(each|the|accused)",
    r"(is|are)\s+sentenced\s+to\s+(life|death|rigorous|simple)",
    r"(convicted|acquitted)\s+(under|of\s+the\s+offences?)",
    r"Having\s+heard\s+the\s+arguments.*we\s+(are|hold|direct|order)",
    r"In\s+view\s+of\s+the\s+above\s+discussions?",
    # Disposition sentences
    r"(Petition|Appeal|Writ\s+petition|W\.?P\.?|Application)\s+is\s+(hereby\s+)?(allowed|dismissed|disposed\s+of|partly\s+allowed|rejected)",
    r"(Hence|Therefore|Accordingly),?\s+(this\s+|the\s+)?(petition|appeal|writ|application|W\.?P\.?)",
    r"Accordingly,?\s+I\s+(pass|make|direct)",
    r"Subject\s+to\s+the\s+above\s+(observations?|directions?)",
    r"With\s+the\s+above\s+observations?",
    r"The\s+writ\s+petition\s+stands\s+(dismissed|allowed|disposed)",
    r"The\s+appeal\s+stands\s+(dismissed|allowed|disposed)",
    r"The\s+appeal\s+(against\s+the\s+)?(acquittal|conviction)\s+(is|stands)",
]

_NARRATIVE_RE = re.compile("|".join(_NARRATIVE_TRIGGERS), re.IGNORECASE)
_DISPOSAL_RE = re.compile("|".join(_DISPOSAL_TRIGGERS), re.IGNORECASE | re.MULTILINE)


def segment_judgment(text: str) -> dict:
    """
    Split judgment text into structured sections using bi-directional scanning.

    Returns dict with keys: header, middle, operative_order, full_text
    """
    normalized = (text or "").strip()
    if not normalized:
        return {
            "header": "",
            "middle": "",
            "operative_order": "",
            "full_text": "",
        }

    doc_len = len(normalized)

    # ─── PHASE 1: Find header end (top-down) ───
    # Scan the first 30% of the document for the first narrative trigger
    scan_limit_header = min(doc_len, int(doc_len * 0.30))
    header_end = min(doc_len, 2000)  # default fallback

    for match in _NARRATIVE_RE.finditer(normalized[:scan_limit_header]):
        # Take the FIRST match — this is where the body starts
        # Back up to the start of the line containing the match
        line_start = normalized.rfind("\n", 0, match.start())
        header_end = max(0, line_start + 1) if line_start >= 0 else match.start()
        break

    # ─── PHASE 2: Find operative start (bottom-up) ───
    # Scan the last 50% of the document for the LAST disposal trigger
    scan_start_operative = max(0, int(doc_len * 0.50))
    operative_start = doc_len  # default: no operative section found

    # Find ALL matches and pick the best one
    matches = list(_DISPOSAL_RE.finditer(normalized[scan_start_operative:]))
    if matches:
        # Strategy: prefer standalone ORDER/DIRECTIONS headings (short lines)
        # Then fall back to the last formulaic trigger
        best_match = None

        # First pass: look for standalone headings
        for m in reversed(matches):
            abs_start = scan_start_operative + m.start()
            line_start = normalized.rfind("\n", 0, abs_start)
            line_end = normalized.find("\n", abs_start)
            if line_end == -1:
                line_end = doc_len
            line_text = normalized[line_start + 1:line_end].strip()

            # Standalone heading: short line, typically just "ORDER" or "**ORDER**"
            if len(line_text) < 50 and re.match(r"^\**\s*(ORDER|DIRECTIONS?)\s*\**$", line_text, re.IGNORECASE):
                best_match = max(0, line_start + 1)
                break

        # Second pass: if no standalone heading, use the last disposition sentence
        if best_match is None:
            for m in reversed(matches):
                abs_start = scan_start_operative + m.start()
                line_start = normalized.rfind("\n", 0, abs_start)
                best_match = max(0, line_start + 1) if line_start >= 0 else abs_start
                break

        if best_match is not None:
            operative_start = best_match

    # ─── PHASE 3: Build sections WITH OVERLAP ───
    # 10% bidirectional overlap ensures no reasoning/directives lost at boundary.
    # Each LLM agent's prompt asks for SPECIFIC things, so it ignores irrelevant overlap.

    header = normalized[:header_end].strip()

    # Core boundaries
    body_len = operative_start - header_end

    # If no operative section found, use last 20% as fallback
    if operative_start >= doc_len:
        operative_start = int(doc_len * 0.80)
        body_len = operative_start - header_end

    # Overlap size: 20% of body length for operative section, minimum 500 chars.
    # Increased from 10% to capture complete operative sections in complex judgments
    # (e.g., criminal appeals with sentencing + procedural orders spanning multiple pages).
    overlap_chars = max(500, int(body_len * 0.20))

    # Body (middle) extends 10% INTO operative zone
    middle_end = min(doc_len, operative_start + overlap_chars)
    middle = normalized[header_end:middle_end].strip()

    # Operative extends 10% BACK into body zone
    operative_begin = max(header_end, operative_start - overlap_chars)
    operative_order = normalized[operative_begin:].strip()

    return {
        "header": header,
        "middle": middle,
        "operative_order": operative_order,
        "full_text": normalized,
    }