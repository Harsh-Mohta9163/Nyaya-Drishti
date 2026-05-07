import datetime
from django.core.management.base import BaseCommand
from apps.action_plans.models import CourtCalendar, LimitationRule

class Command(BaseCommand):
    help = "Seeds the CourtCalendar and LimitationRule tables"

    def handle(self, *args, **options):
        self.stdout.write("Seeding Limitation Rules...")
        
        rules = [
            {
                "action_type": "slp",
                "statutory_days": 90,
                "condonable": True,
                "legal_basis": "Article 136, Constitution + Supreme Court Rules",
                "section_reference": "Art. 136",
            },
            {
                "action_type": "appeal_hc",
                "statutory_days": 90,
                "condonable": True,
                "legal_basis": "Article 116, Limitation Act",
                "section_reference": "Art. 116",
            },
            {
                "action_type": "writ_appeal",
                "statutory_days": 30,
                "condonable": True,
                "legal_basis": "Section 4, Karnataka High Court Act",
                "section_reference": "S.4 KHC Act",
            },
            {
                "action_type": "compliance",
                "statutory_days": 30,
                "condonable": False,
                "legal_basis": "General Compliance",
                "section_reference": "General",
            }
        ]
        
        for rule_data in rules:
            LimitationRule.objects.update_or_create(
                action_type=rule_data["action_type"],
                defaults=rule_data
            )
            
        self.stdout.write(self.style.SUCCESS("Limitation Rules seeded."))

        self.stdout.write("Seeding Court Calendar (2024)...")
        # Just a basic example of seeding some holidays for 2024
        
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 12, 31)
        delta = datetime.timedelta(days=1)
        
        holidays_2024 = {
            datetime.date(2024, 1, 15): "Makara Sankranti",
            datetime.date(2024, 1, 26): "Republic Day",
            datetime.date(2024, 3, 8): "Maha Shivaratri",
            datetime.date(2024, 3, 29): "Good Friday",
            datetime.date(2024, 4, 9): "Ugadi",
            datetime.date(2024, 4, 11): "Ramzan",
            datetime.date(2024, 5, 1): "May Day",
            datetime.date(2024, 8, 15): "Independence Day",
            datetime.date(2024, 9, 7): "Ganesha Chaturthi",
            datetime.date(2024, 10, 2): "Gandhi Jayanti",
            datetime.date(2024, 10, 11): "Ayudha Pooja",
            datetime.date(2024, 10, 31): "Naraka Chaturdashi",
            datetime.date(2024, 11, 1): "Kannada Rajyotsava",
            datetime.date(2024, 12, 25): "Christmas",
        }
        
        current_date = start_date
        while current_date <= end_date:
            is_working = True
            entry_type = "working"
            reason = ""
            
            # Weekends
            if current_date.weekday() >= 5:
                is_working = False
                entry_type = "weekend"
                
            # Holidays
            if current_date in holidays_2024:
                is_working = False
                entry_type = "holiday"
                reason = holidays_2024[current_date]
                
            # Vacation (Example: Summer vacation May 1 - May 31)
            if current_date.month == 5:
                is_working = False
                entry_type = "vacation"
                reason = "Summer Vacation"

            CourtCalendar.objects.update_or_create(
                date=current_date,
                court_name="Karnataka High Court",
                defaults={
                    "is_working_day": is_working,
                    "entry_type": entry_type,
                    "holiday_reason": reason
                }
            )
            current_date += delta
            
        self.stdout.write(self.style.SUCCESS("Court Calendar seeded."))
