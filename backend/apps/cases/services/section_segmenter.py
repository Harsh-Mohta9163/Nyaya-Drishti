"""
Structure-aware judgment segmenter.

Splits a Karnataka HC judgment into: header, facts, analysis, operative_order.
The operative order is where 95 % of actionable directives live.
"""
import re

# Patterns that signal the start of the operative/order section
_OPERATIVE_PATTERNS = [
    r"\bORDER\b",
    r"\bORDERED\b",
    r"\bO\s*R\s*D\s*E\s*R\b",
    r"\bDIRECTIONS?\b",
    r"\boperative\s+portion\b",
    r"\boperative\s+part\b",
    r"\bhence[,;:\s]",
    r"\btherefore[,;:\s]",
    r"\bfor\s+the\s+reasons\s+(stated|mentioned|aforesaid)\b",
    r"\bin\s+the\s+result\b",
    r"\baccordingly[,;:\s]",
    r"\bpetition\s+is\s+(allowed|dismissed|disposed)\b",
    r"\bappeal\s+is\s+(allowed|dismissed|disposed)\b",
    r"\bwrit\s+petition\s+is\s+(allowed|dismissed|disposed)\b",
    r"\bthe\s+following\s+order\s+is\s+made\b",
    r"\bi\s+pass\s+the\s+following\s+order\b",
]

_OPERATIVE_RE = re.compile("|".join(_OPERATIVE_PATTERNS), re.IGNORECASE)

# Header patterns (case number, bench, parties)
_HEADER_END_PATTERNS = [
    r"\bTHIS\s+(WRIT\s+)?PETITION\b",
    r"\bTHIS\s+APPEAL\b",
    r"\bPRAYER\b",
    r"\bBACKGROUND\b",
    r"\bFACTS\b",
    r"\bBRIEF\s+FACTS\b",
    r"\bHaving\s+heard\b",
    r"\bHaving\s+considered\b",
]

_HEADER_END_RE = re.compile("|".join(_HEADER_END_PATTERNS), re.IGNORECASE)


def segment_judgment(text: str) -> dict:
    """
    Split judgment text into structured sections.

    Returns dict with keys: header, facts, analysis, operative_order, full_text
    """
    normalized = (text or "").strip()
    if not normalized:
        return {
            "header": "",
            "facts": "",
            "analysis": "",
            "operative_order": "",
            "full_text": "",
        }

    # --- Find header end ---
    header_end = min(len(normalized), 2000)  # Default: first 2000 chars
    for match in _HEADER_END_RE.finditer(normalized[:5000]):
        header_end = match.start()
        break

    # --- Find operative order start ---
    # Search from the LAST 60% of the document (operative orders are near the end)
    search_start = max(0, int(len(normalized) * 0.4))
    operative_start = len(normalized)

    # Find ALL matches and pick the LAST major one
    matches = list(_OPERATIVE_RE.finditer(normalized[search_start:]))
    if matches:
        # Prefer matches that look like standalone "ORDER" headings
        for m in reversed(matches):
            line_start = normalized.rfind("\n", 0, search_start + m.start()) + 1
            line_text = normalized[line_start:search_start + m.end()].strip()
            # Standalone heading (short line with ORDER/DIRECTIONS)
            if len(line_text) < 40:
                operative_start = line_start
                break
        else:
            # Fall back to last match
            operative_start = search_start + matches[-1].start()

    # --- Build sections ---
    header = normalized[:header_end].strip()
    operative_order = normalized[operative_start:].strip() if operative_start < len(normalized) else ""

    # Everything between header and operative order is facts + analysis
    middle = normalized[header_end:operative_start].strip()

    # Split middle roughly: first half = facts, second half = analysis
    mid_point = len(middle) // 2
    facts = middle[:mid_point].strip()
    analysis = middle[mid_point:].strip()

    # If no operative order found, use last 30% of text as fallback
    if not operative_order:
        fallback_start = int(len(normalized) * 0.7)
        operative_order = normalized[fallback_start:].strip()

    return {
        "header": header,
        "facts": facts,
        "analysis": analysis,
        "operative_order": operative_order,
        "full_text": normalized,
    }