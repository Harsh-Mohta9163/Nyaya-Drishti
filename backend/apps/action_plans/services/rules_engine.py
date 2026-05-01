"""
Deterministic Rules Engine — Limitation Act 1963 + Karnataka HC Court Calendar.

Implements:
  - Full Schedule (Articles 114-117) limitation periods
  - Section 4:  Expiry on court holiday → extend to next working day
  - Section 5:  Condonation of delay flag
  - Section 12: Exclusion of first day + time for obtaining certified copy
  - Karnataka HC vacation periods (Summer, Dasara, Winter) 2024-2026
  - Karnataka state public holidays 2024-2026
  - Second Saturdays and Sundays
  - Internal buffer deadlines for government departments
"""
from datetime import date, timedelta
from typing import Optional

# ============================================================
# 1. LIMITATION PERIODS — Schedule to the Limitation Act, 1963
# ============================================================
# Article Number → description, days, applicable court, legal_basis

LIMITATION_PERIODS = {
    # --- Appeals to Supreme Court (Articles 112-114) ---
    "slp": {
        "days": 90,
        "basis": "Article 136, Constitution + Supreme Court Rules, Order XXI Rule 15",
        "section": "Art. 136",
        "description": "Special Leave Petition to Supreme Court",
        "condonable": True,
    },
    "slp_certificate_refused": {
        "days": 60,
        "basis": "Article 112, Limitation Act — Appeal after refusal of certificate of fitness",
        "section": "Art. 112",
        "description": "SLP after High Court refuses certificate",
        "condonable": True,
    },
    "appeal_death_sentence": {
        "days": 60,
        "basis": "Article 114, Limitation Act — Appeal from death sentence",
        "section": "Art. 114",
        "description": "Appeal against death sentence to SC",
        "condonable": True,
    },

    # --- Appeals to High Court (Articles 116-117) ---
    "appeal_hc": {
        "days": 90,
        "basis": "Article 116, Limitation Act — Appeal to High Court from any decree or order",
        "section": "Art. 116",
        "description": "Appeal to High Court",
        "condonable": True,
    },
    "lpa": {
        "days": 30,
        "basis": "Letters Patent Appeal, Clause 15 — Appeal within HC from Single Judge to Division Bench",
        "section": "Clause 15 LP",
        "description": "Letters Patent Appeal within High Court",
        "condonable": True,
    },
    "writ_appeal": {
        "days": 30,
        "basis": "Section 4, Karnataka High Court Act + High Court Rules — Writ Appeal",
        "section": "S.4 KHC Act",
        "description": "Writ Appeal to Division Bench",
        "condonable": True,
    },

    # --- Appeals to Other Courts (Article 116 proviso) ---
    "appeal_lower_court": {
        "days": 30,
        "basis": "Article 116, Limitation Act — Appeal to court other than High Court",
        "section": "Art. 116",
        "description": "Appeal to District/Sessions Court",
        "condonable": True,
    },

    # --- Criminal Appeals ---
    "criminal_appeal_hc": {
        "days": 60,
        "basis": "Article 115, Limitation Act — Criminal appeal to High Court from sentence/order",
        "section": "Art. 115",
        "description": "Criminal appeal to High Court",
        "condonable": True,
    },
    "criminal_appeal_other": {
        "days": 30,
        "basis": "Article 115, Limitation Act — Criminal appeal to court other than HC",
        "section": "Art. 115",
        "description": "Criminal appeal to Sessions Court",
        "condonable": True,
    },

    # --- Review and Revision ---
    "review": {
        "days": 30,
        "basis": "Article 114, Limitation Act + Order 47 Rule 1 CPC — Review of judgment",
        "section": "O.47 R.1 CPC",
        "description": "Review petition",
        "condonable": False,  # Review has stricter limits
    },
    "revision": {
        "days": 90,
        "basis": "Section 115 CPC — Revision to High Court",
        "section": "S.115 CPC",
        "description": "Revision petition",
        "condonable": True,
    },

    # --- Execution and Compliance ---
    "execution": {
        "days": 365 * 12,  # 12 years
        "basis": "Article 136, Limitation Act — Execution of decree",
        "section": "Art. 136",
        "description": "Execution of decree (12 years)",
        "condonable": False,
    },
    "compliance": {
        "days": 30,
        "basis": "Administrative compliance window — Karnataka Government Order practice",
        "section": "Administrative",
        "description": "Default compliance period",
        "condonable": False,
    },
    "contempt": {
        "days": 365,
        "basis": "Section 20, Contempt of Courts Act, 1971 — Contempt within 1 year",
        "section": "S.20 CCA",
        "description": "Contempt petition (1 year limitation)",
        "condonable": False,
    },
}


# ============================================================
# 2. KARNATAKA HIGH COURT HOLIDAYS & VACATIONS
# ============================================================

# Public holidays (dates common or adjusted by year)
# Source: Karnataka DPAR Circulars + HC Calendar Notifications
KARNATAKA_PUBLIC_HOLIDAYS = {
    2024: [
        date(2024, 1, 15),   # Sankranti
        date(2024, 1, 17),   # Kanuma
        date(2024, 1, 26),   # Republic Day
        date(2024, 3, 8),    # Maha Shivaratri
        date(2024, 3, 25),   # Holi
        date(2024, 3, 29),   # Good Friday
        date(2024, 4, 11),   # Ugadi
        date(2024, 4, 14),   # Dr. Ambedkar Jayanti
        date(2024, 4, 17),   # Ram Navami
        date(2024, 4, 21),   # Mahaveer Jayanti
        date(2024, 5, 1),    # May Day
        date(2024, 5, 23),   # Buddha Purnima
        date(2024, 6, 17),   # Bakrid
        date(2024, 7, 17),   # Muharram
        date(2024, 8, 15),   # Independence Day
        date(2024, 8, 26),   # Krishna Janmashtami
        date(2024, 9, 16),   # Milad-un-Nabi
        date(2024, 10, 2),   # Gandhi Jayanti
        date(2024, 10, 12),  # Mahanavami
        date(2024, 10, 13),  # Vijayadashami
        date(2024, 11, 1),   # Rajyotsava / Deepavali
        date(2024, 11, 15),  # Guru Nanak Jayanti
        date(2024, 12, 25),  # Christmas
    ],
    2025: [
        date(2025, 1, 14),   # Sankranti
        date(2025, 1, 26),   # Republic Day
        date(2025, 2, 26),   # Maha Shivaratri
        date(2025, 3, 14),   # Holi
        date(2025, 3, 30),   # Ugadi
        date(2025, 4, 6),    # Ram Navami
        date(2025, 4, 10),   # Mahaveer Jayanti
        date(2025, 4, 14),   # Dr. Ambedkar Jayanti
        date(2025, 4, 18),   # Good Friday
        date(2025, 4, 30),   # Basava Jayanti
        date(2025, 5, 1),    # May Day
        date(2025, 5, 12),   # Buddha Purnima
        date(2025, 6, 7),    # Bakrid
        date(2025, 7, 6),    # Muharram
        date(2025, 8, 15),   # Independence Day
        date(2025, 8, 16),   # Krishna Janmashtami
        date(2025, 9, 5),    # Milad-un-Nabi
        date(2025, 10, 1),   # Mahanavami / Ayudha Puja
        date(2025, 10, 2),   # Gandhi Jayanti / Vijayadashami
        date(2025, 10, 7),   # Maharshi Valmiki Jayanti
        date(2025, 10, 20),  # Naraka Chaturdashi
        date(2025, 10, 22),  # Balipadyami
        date(2025, 11, 1),   # Rajyotsava
        date(2025, 11, 5),   # Guru Nanak Jayanti
        date(2025, 12, 25),  # Christmas
    ],
    2026: [
        date(2026, 1, 14),   # Sankranti
        date(2026, 1, 26),   # Republic Day
        date(2026, 2, 16),   # Maha Shivaratri
        date(2026, 3, 4),    # Holi
        date(2026, 3, 19),   # Ugadi
        date(2026, 3, 26),   # Ram Navami
        date(2026, 3, 31),   # Mahaveer Jayanti
        date(2026, 4, 3),    # Good Friday
        date(2026, 4, 14),   # Dr. Ambedkar Jayanti
        date(2026, 5, 1),    # May Day
        date(2026, 5, 2),    # Buddha Purnima
        date(2026, 5, 28),   # Bakrid
        date(2026, 6, 26),   # Muharram
        date(2026, 8, 15),   # Independence Day
        date(2026, 8, 25),   # Milad-un-Nabi
        date(2026, 9, 4),    # Krishna Janmashtami
        date(2026, 10, 2),   # Gandhi Jayanti
        date(2026, 10, 11),  # Vijayadashami
        date(2026, 11, 1),   # Rajyotsava
        date(2026, 11, 9),   # Deepavali
        date(2026, 12, 25),  # Christmas
    ],
}

# HC Vacation periods (court is closed — Section 4 of Limitation Act applies)
# Source: Karnataka HC Registrar General notifications
HC_VACATIONS = {
    2024: [
        (date(2024, 4, 29), date(2024, 5, 25)),   # Summer Vacation
        (date(2024, 10, 3), date(2024, 10, 10)),   # Dasara Vacation
        (date(2024, 12, 21), date(2024, 12, 31)),  # Winter Vacation
    ],
    2025: [
        (date(2025, 5, 5), date(2025, 5, 31)),    # Summer Vacation
        (date(2025, 9, 29), date(2025, 10, 6)),    # Dasara Vacation
        (date(2025, 12, 20), date(2025, 12, 31)),  # Winter Vacation
    ],
    2026: [
        (date(2026, 5, 4), date(2026, 5, 30)),    # Summer Vacation (estimated)
        (date(2026, 10, 5), date(2026, 10, 12)),   # Dasara Vacation (estimated)
        (date(2026, 12, 21), date(2026, 12, 31)),  # Winter Vacation (estimated)
    ],
}


# ============================================================
# 3. COURT CALENDAR UTILITY FUNCTIONS
# ============================================================

def _is_second_saturday(d: date) -> bool:
    """Check if a date is the second Saturday of its month."""
    if d.weekday() != 5:  # Not Saturday
        return False
    # Second Saturday = day 8-14
    return 8 <= d.day <= 14


def _is_court_holiday(d: date) -> bool:
    """
    Check if a given date is a court holiday (court is closed).

    A court is closed on:
      1. Sundays
      2. Second Saturdays (Karnataka HC practice)
      3. Public holidays
      4. HC vacation periods
    """
    # Sunday
    if d.weekday() == 6:
        return True

    # Second Saturday
    if _is_second_saturday(d):
        return True

    # Public holiday
    year_holidays = KARNATAKA_PUBLIC_HOLIDAYS.get(d.year, [])
    if d in year_holidays:
        return True

    # HC Vacation
    year_vacations = HC_VACATIONS.get(d.year, [])
    for vac_start, vac_end in year_vacations:
        if vac_start <= d <= vac_end:
            return True

    return False


def _next_working_day(d: date) -> date:
    """
    Section 4, Limitation Act:
    If deadline falls on a court holiday, extend to the next day the court reopens.
    """
    while _is_court_holiday(d):
        d += timedelta(days=1)
    return d


def _count_working_days(start: date, end: date) -> int:
    """Count the number of working days between two dates."""
    count = 0
    current = start
    while current <= end:
        if not _is_court_holiday(current):
            count += 1
        current += timedelta(days=1)
    return count


# ============================================================
# 4. MAIN DEADLINE COMPUTATION
# ============================================================

def compute_deadlines(
    judgment_date: date,
    order_type: str = "",
    recommendation: str = "comply",
    copy_obtained_date: Optional[date] = None,
    internal_buffer_days: int = 14,
) -> dict:
    """
    Compute legal and internal deadlines per the Limitation Act, 1963.

    Args:
        judgment_date: Date of the judgment/order.
        order_type: Type of appeal/action (key into LIMITATION_PERIODS).
        recommendation: "comply" or "appeal" — determines which period to use.
        copy_obtained_date: Date the certified copy was obtained (Section 12 exclusion).
        internal_buffer_days: Government department internal buffer (days before legal deadline).

    Returns:
        dict with legal_deadline, internal_deadline, basis, section, warnings, etc.
    """
    # Determine the applicable limitation period
    key = (order_type or "").lower().replace(" ", "_")
    if key not in LIMITATION_PERIODS:
        # Try to infer from recommendation
        if recommendation.lower() == "appeal":
            key = "slp"  # Default to SLP if recommending appeal
        elif recommendation.lower() == "comply":
            key = "compliance"
        else:
            key = "compliance"

    period = LIMITATION_PERIODS.get(key, LIMITATION_PERIODS["compliance"])

    # --- Section 12: Exclusion of first day ---
    # "The day from which the period is to be reckoned shall be excluded"
    start_date = judgment_date + timedelta(days=1)

    # --- Section 12: Exclusion of time for obtaining certified copy ---
    if copy_obtained_date and copy_obtained_date > judgment_date:
        # Time between judgment date and copy obtained date is excluded
        copy_days = (copy_obtained_date - judgment_date).days
        start_date = copy_obtained_date + timedelta(days=1)
    else:
        copy_days = 0

    # --- Compute raw deadline ---
    raw_deadline = start_date + timedelta(days=period["days"] - 1)

    # --- Section 4: If deadline falls on court holiday, extend to next working day ---
    legal_deadline = _next_working_day(raw_deadline)

    # --- Internal deadline: buffer before legal deadline ---
    internal_raw = legal_deadline - timedelta(days=internal_buffer_days)
    internal_deadline = _next_working_day(internal_raw)

    # Ensure internal deadline doesn't come after legal deadline
    if internal_deadline >= legal_deadline:
        internal_deadline = legal_deadline - timedelta(days=1)
        internal_deadline = _next_working_day(internal_deadline) if not _is_court_holiday(internal_deadline) else internal_deadline

    # --- Warnings ---
    warnings = []
    remaining_days = (legal_deadline - date.today()).days
    working_days_remaining = _count_working_days(date.today(), legal_deadline)

    if remaining_days <= 0:
        warnings.append("EXPIRED: Legal deadline has already passed!")
    elif remaining_days <= 7:
        warnings.append(f"CRITICAL: Only {remaining_days} calendar days ({working_days_remaining} working days) remaining!")
    elif remaining_days <= 14:
        warnings.append(f"URGENT: {remaining_days} calendar days ({working_days_remaining} working days) remaining.")
    elif remaining_days <= 30:
        warnings.append(f"APPROACHING: {remaining_days} calendar days remaining.")

    if copy_days > 0:
        warnings.append(f"Section 12: {copy_days} days excluded for obtaining certified copy.")

    if raw_deadline != legal_deadline:
        warnings.append(f"Section 4: Deadline extended from {raw_deadline} (court holiday) to {legal_deadline} (next working day).")

    # --- Build response ---
    return {
        "legal_deadline": legal_deadline,
        "internal_deadline": internal_deadline,
        "raw_deadline": raw_deadline,
        "judgment_date": judgment_date,
        "start_date": start_date,
        "limitation_days": period["days"],
        "copy_days_excluded": copy_days,
        "basis": period["basis"],
        "section": period["section"],
        "description": period["description"],
        "condonable": period["condonable"],
        "remaining_calendar_days": max(0, remaining_days),
        "remaining_working_days": max(0, working_days_remaining),
        "deadline_on_holiday": raw_deadline != legal_deadline,
        "warnings": warnings,
    }


def get_all_applicable_deadlines(judgment_date: date, copy_obtained_date: Optional[date] = None) -> list[dict]:
    """
    Compute ALL applicable limitation deadlines for a judgment.

    Useful for showing a complete timeline to the government officer.
    """
    results = []
    for key, period in LIMITATION_PERIODS.items():
        if key == "execution":  # Skip 12-year execution period for brevity
            continue
        deadline_info = compute_deadlines(
            judgment_date=judgment_date,
            order_type=key,
            copy_obtained_date=copy_obtained_date,
        )
        results.append({
            "type": key,
            **deadline_info,
        })

    results.sort(key=lambda x: x["legal_deadline"])
    return results
