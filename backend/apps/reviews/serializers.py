from rest_framework import serializers

from apps.action_plans.models import ActionPlan

from .models import ReviewLog, TrainingPair


class ReviewLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewLog
        fields = [
            "id",
            "action_plan",
            "reviewer",
            "review_level",
            "action",
            "changes",
            "notes",
            "created_at",
        ]
        read_only_fields = ["reviewer", "created_at"]


class TrainingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingPair
        fields = [
            "id",
            "case",
            "field_name",
            "ai_output",
            "human_correction",
            "used_for_training",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ReviewSubmitSerializer(serializers.Serializer):
    action_plan = serializers.PrimaryKeyRelatedField(queryset=ActionPlan.objects.all())
    review_level = serializers.CharField()
    action = serializers.ChoiceField(choices=["approve", "edit", "reject"])
    changes = serializers.JSONField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    field_name = serializers.CharField(required=False, allow_blank=True)
    human_correction = serializers.CharField(required=False, allow_blank=True)
