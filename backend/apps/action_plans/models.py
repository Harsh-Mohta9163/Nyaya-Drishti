import uuid
from django.db import models
from apps.cases.models import Judgment

class CourtCalendar(models.Model):
    class EntryType(models.TextChoices):
        HOLIDAY = "holiday", "Public Holiday"
        VACATION_START = "vacation_start", "Vacation Start"
        VACATION_END = "vacation_end", "Vacation End"
        SECOND_SATURDAY = "second_saturday", "Second Saturday"

    date = models.DateField(db_index=True)
    court_name = models.CharField(max_length=200,
        help_text="'Karnataka HC' or 'Supreme Court' etc.")
    is_working_day = models.BooleanField()
    entry_type = models.CharField(max_length=30, choices=EntryType.choices,
        null=True, blank=True)
    holiday_reason = models.CharField(max_length=200, blank=True,
        help_text="e.g. Vijayadashami, Summer Vacation, Sunday")

    class Meta:
        unique_together = ["date", "court_name"]
        ordering = ["date"]

    def __str__(self):
        return f"{self.date} — {self.court_name} — {'Working' if self.is_working_day else self.holiday_reason}"

class LimitationRule(models.Model):
    action_type = models.CharField(max_length=100, unique=True,
        help_text="e.g. writ_appeal, slp, review")
    statutory_days = models.IntegerField()
    legal_basis = models.TextField()
    section_reference = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    condonable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.action_type} ({self.statutory_days}d)"

class ActionPlan(models.Model):
    judgment = models.OneToOneField(Judgment, on_delete=models.CASCADE, related_name="action_plan")
    recommendation = models.CharField(max_length=20)
    recommendation_reasoning = models.TextField(blank=True)
    compliance_actions = models.JSONField(default=list)
    
    # Pipeline 1 Output — Compliance deadline (from LLM + Python math)
    compliance_deadline = models.DateField(null=True, blank=True,
        help_text="Explicit court-ordered compliance date")
    compliance_action = models.TextField(blank=True,
        help_text="What must be done (e.g. pay fine, reinstate employee)")
    
    # Pipeline 2 Output — Statutory appeal deadline (from Rules Engine)
    statutory_appeal_deadline = models.DateField(null=True, blank=True,
        help_text="Limitation Act deadline for filing appeal")
    statutory_period_type = models.CharField(max_length=100, blank=True,
        help_text="e.g. writ_appeal (30d), slp (90d)")
    
    # Internal buffers (14 days before each)
    internal_compliance_deadline = models.DateField(null=True, blank=True)
    internal_appeal_deadline = models.DateField(null=True, blank=True)
    
    responsible_departments = models.JSONField(default=list)
    ccms_stage = models.CharField(max_length=100)
    similar_cases = models.JSONField(default=list)
    verification_status = models.CharField(max_length=20, default="pending")
    
    # Appeal Strategy
    appeal_viability = models.CharField(max_length=10, blank=True)  # High/Med/Low
    appeal_strategy = models.TextField(blank=True)
    appeal_precedents = models.JSONField(default=list)
    
    # RAG Pipeline output cache
    full_rag_recommendation = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.judgment.case.case_number} - {self.recommendation}"
