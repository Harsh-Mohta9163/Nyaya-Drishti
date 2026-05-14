from rest_framework import serializers

from apps.accounts.serializers import DepartmentSerializer
from apps.action_plans.serializers import ActionPlanSerializer
from apps.action_plans.models import ActionPlan

from .models import Case, Judgment, Citation


class CitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Citation
        fields = [
            "id",
            "citing_judgment",
            "cited_case",
            "cited_case_name_raw",
            "citation_id_raw",
            "citation_context",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class JudgmentSerializer(serializers.ModelSerializer):
    outgoing_citations = CitationSerializer(many=True, read_only=True)
    action_plan = serializers.SerializerMethodField()

    class Meta:
        model = Judgment
        fields = [
            "id",
            "case",
            "date_of_order",
            "document_type",
            "presiding_judges",
            "disposition",
            "winning_party_type",
            "operative_order_text",
            "summary_of_facts",
            "issues_framed",
            "ratio_decidendi",
            "court_directions",
            "entities",
            "contempt_indicators",
            "contempt_risk",
            "financial_implications",
            "appeal_type",
            "extraction_confidence",
            "ocr_confidence",
            "pdf_file",
            "pdf_storage_url",
            "processing_status",
            "outgoing_citations",
            "action_plan",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_action_plan(self, obj):
        try:
            action_plan = obj.action_plan
        except ActionPlan.DoesNotExist:
            return None
        return ActionPlanSerializer(action_plan).data


class CaseSerializer(serializers.ModelSerializer):
    judgments = JudgmentSerializer(many=True, read_only=True)
    appeals = serializers.SerializerMethodField()
    incoming_citations = CitationSerializer(many=True, read_only=True)
    primary_department = DepartmentSerializer(read_only=True)
    secondary_departments = DepartmentSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "matter_id",
            "cnr_number",
            "court_name",
            "case_type",
            "case_number",
            "case_year",
            "petitioner_name",
            "respondent_name",
            "status",
            "area_of_law",
            "primary_statute",
            "primary_department",
            "secondary_departments",
            "appealed_from_case",
            "uploaded_by",
            "judgments",
            "appeals",
            "incoming_citations",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uploaded_by", "created_at", "updated_at"]

    def get_appeals(self, obj):
        return CaseSerializer(obj.appeals.all(), many=True).data


class CaseStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = ["status"]
