from django.conf import settings
from django.db import models

from apps.action_plans.models import ActionPlan
from apps.cases.models import Case, Judgment


class ReviewLog(models.Model):
    action_plan = models.ForeignKey(ActionPlan, on_delete=models.CASCADE, related_name="review_logs")
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    review_level = models.CharField(max_length=20)
    action = models.CharField(max_length=20)
    changes = models.JSONField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.action_plan.judgment.case.case_number} - {self.review_level} - {self.action}"


class TrainingPair(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, null=True, blank=True)
    judgment = models.ForeignKey(Judgment, on_delete=models.CASCADE, null=True, blank=True)
    field_name = models.CharField(max_length=100)
    ai_output = models.TextField()
    human_correction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    used_for_training = models.BooleanField(default=False)
