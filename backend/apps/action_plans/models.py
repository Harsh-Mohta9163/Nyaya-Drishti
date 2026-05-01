from django.db import models

from apps.cases.models import Case


class ActionPlan(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name="action_plan")
    recommendation = models.CharField(max_length=20)
    recommendation_reasoning = models.TextField(blank=True)
    compliance_actions = models.JSONField(default=list)
    legal_deadline = models.DateField(null=True, blank=True)
    internal_deadline = models.DateField(null=True, blank=True)
    responsible_departments = models.JSONField(default=list)
    ccms_stage = models.CharField(max_length=100)
    contempt_risk = models.CharField(max_length=10)
    similar_cases = models.JSONField(default=list)
    verification_status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.case.case_number} - {self.recommendation}"
