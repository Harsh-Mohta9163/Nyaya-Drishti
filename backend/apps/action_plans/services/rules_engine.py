from datetime import date, timedelta
from typing import Optional

from django.utils import timezone
from apps.action_plans.models import LimitationRule, CourtCalendar

def _is_holiday(check_date: date, court_name: str) -> bool:
    """
    Check if the given date is a holiday or non-working day for the specified court
    using the Postgres CourtCalendar table.
    """
    try:
        cal = CourtCalendar.objects.get(date=check_date, court_name=court_name)
        return not cal.is_working_day
    except CourtCalendar.DoesNotExist:
        # Fallback to simple weekends if not in DB
        return check_date.weekday() >= 5  # Saturday or Sunday

def _get_next_working_day(target_date: date, court_name: str) -> date:
    """
    Limitation Act, Section 4: If period expires on a closed day,
    it is extended to the next working day.
    """
    current_date = target_date
    while _is_holiday(current_date, court_name):
        current_date += timedelta(days=1)
    return current_date

def compute_deadlines(
    judgment_date: str | date, 
    document_type: str, 
    recommendation: str = "comply",
    court_name: str = "Karnataka High Court"
) -> dict:
    """
    Compute deadlines using deterministic rules engine querying Postgres DB.
    """
    if isinstance(judgment_date, str):
        try:
            judgment_date = date.fromisoformat(judgment_date[:10])
        except Exception:
            judgment_date = timezone.now().date()
            
    if not judgment_date:
        judgment_date = timezone.now().date()

    # Section 12(1) - Exclude the day from which the period is to be reckoned
    base_date = judgment_date + timedelta(days=1)

    result = {
        "legal_deadline": None,
        "internal_deadline": None,
        "basis": "Fallback (30 days)",
        "condonable": False,
        "section": "General"
    }

    try:
        # Map document type to limitation rule
        rule_type = "appeal_hc"
        if recommendation.lower() == "appeal":
            if "supreme court" in court_name.lower():
                rule_type = "slp"
            elif "writ appeal" in document_type.lower():
                rule_type = "writ_appeal"
            else:
                rule_type = "appeal_hc"
        else:
            rule_type = "compliance"
            
        rule = LimitationRule.objects.filter(action_type=rule_type, is_active=True).first()
        
        if rule:
            days = rule.statutory_days
            result["basis"] = rule.legal_basis
            result["condonable"] = rule.condonable
            result["section"] = rule.section_reference
        else:
            days = 90 if recommendation.lower() == "appeal" else 30
            
        # Add 10 days for certified copy buffer (Section 12(2) buffer)
        # Real-world this would be dynamically tracked
        time_for_certified_copy = 10
        total_days = days + time_for_certified_copy
        
        target_date = base_date + timedelta(days=total_days - 1)
        
        # Section 4: Extend to next working day if expires on a holiday
        final_legal_date = _get_next_working_day(target_date, court_name)
        result["legal_deadline"] = final_legal_date.isoformat()
        
        # Internal buffer for govt departments
        internal_date = final_legal_date - timedelta(days=15 if days >= 60 else 7)
        # Ensure internal deadline doesn't land on a weekend
        while internal_date.weekday() >= 5:
            internal_date -= timedelta(days=1)
            
        result["internal_deadline"] = internal_date.isoformat()

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error computing deadlines: {e}")
        # Extreme fallback
        fallback = base_date + timedelta(days=30)
        result["legal_deadline"] = fallback.isoformat()
        result["internal_deadline"] = (fallback - timedelta(days=7)).isoformat()
        
    return result
