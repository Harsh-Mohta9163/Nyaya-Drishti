from rest_framework import serializers

from apps.action_plans.serializers import ActionPlanSerializer
from apps.action_plans.models import ActionPlan

from .models import Case, ExtractedData


class ExtractedDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedData
        fields = [
            "id",
            "case",
            "header_data",
            "operative_order",
            "court_directions",
            "order_type",
            "entities",
            "extraction_confidence",
            "source_references",
        ]


class CaseSerializer(serializers.ModelSerializer):
    extracted_data = serializers.SerializerMethodField()
    action_plan = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = [
            "id",
            "case_number",
            "court",
            "bench",
            "petitioner",
            "respondent",
            "case_type",
            "judgment_date",
            "pdf_file",
            "status",
            "ocr_confidence",
            "uploaded_by",
            "created_at",
            "updated_at",
            "extracted_data",
            "action_plan",
        ]
        read_only_fields = ["uploaded_by", "status", "ocr_confidence", "created_at", "updated_at"]

    def get_extracted_data(self, obj):
        try:
            extracted_data = obj.extracted_data
        except ExtractedData.DoesNotExist:
            return None
        return ExtractedDataSerializer(extracted_data).data

    def get_action_plan(self, obj):
        try:
            action_plan = obj.action_plan
        except ActionPlan.DoesNotExist:
            return None
        return ActionPlanSerializer(action_plan).data


class CaseStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["status"]
