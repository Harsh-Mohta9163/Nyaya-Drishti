from rest_framework import serializers

from .models import ActionPlan, CourtCalendar, LimitationRule


class CourtCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtCalendar
        fields = "__all__"


class LimitationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = LimitationRule
        fields = "__all__"


class ActionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionPlan
        fields = [
            "id",
            "judgment",
            "recommendation",
            "recommendation_reasoning",
            "compliance_actions",
            "compliance_deadline",
            "compliance_action",
            "statutory_appeal_deadline",
            "statutory_period_type",
            "internal_compliance_deadline",
            "internal_appeal_deadline",
            "responsible_departments",
            "ccms_stage",
            "similar_cases",
            "verification_status",
            "appeal_viability",
            "appeal_strategy",
            "appeal_precedents",
            "full_rag_recommendation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
