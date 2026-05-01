from rest_framework import serializers

from .models import ActionPlan


class ActionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionPlan
        fields = [
            "id",
            "case",
            "recommendation",
            "recommendation_reasoning",
            "compliance_actions",
            "legal_deadline",
            "internal_deadline",
            "responsible_departments",
            "ccms_stage",
            "contempt_risk",
            "similar_cases",
            "verification_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
