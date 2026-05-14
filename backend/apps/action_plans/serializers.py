from rest_framework import serializers

from .models import ActionPlan, CourtCalendar, DirectiveExecution, LimitationRule


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


class DirectiveExecutionSerializer(serializers.ModelSerializer):
    case_id = serializers.UUIDField(source="action_plan.judgment.case.id", read_only=True)
    case_number = serializers.CharField(source="action_plan.judgment.case.case_number", read_only=True)
    case_title = serializers.SerializerMethodField()
    department_code = serializers.CharField(
        source="action_plan.judgment.case.primary_department.code",
        read_only=True, default=None,
    )
    department_name = serializers.CharField(
        source="action_plan.judgment.case.primary_department.name",
        read_only=True, default=None,
    )
    compliance_deadline = serializers.DateField(
        source="action_plan.compliance_deadline", read_only=True
    )
    executed_by_name = serializers.SerializerMethodField()
    proof_file_url = serializers.SerializerMethodField()

    # Pulled live from action_plan.judgment.court_directions[directive_index]
    # so we get the freshest enrichment without storing it on DirectiveExecution.
    actor_type = serializers.SerializerMethodField()
    gov_action_required = serializers.SerializerMethodField()
    implementation_steps = serializers.SerializerMethodField()
    display_note = serializers.SerializerMethodField()
    govt_summary = serializers.SerializerMethodField()

    class Meta:
        model = DirectiveExecution
        fields = [
            "id", "action_plan", "directive_index",
            "directive_text", "responsible_entity", "action_required",
            "deadline_mentioned", "status",
            "executed_by", "executed_by_name", "completed_at",
            "proof_file", "proof_file_url", "notes",
            "case_id", "case_number", "case_title",
            "department_code", "department_name",
            "compliance_deadline",
            "actor_type", "gov_action_required",
            "implementation_steps", "display_note", "govt_summary",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "action_plan", "directive_index",
            "directive_text", "responsible_entity", "action_required",
            "deadline_mentioned", "executed_by", "executed_by_name",
            "case_id", "case_number", "case_title",
            "department_code", "department_name", "compliance_deadline",
            "proof_file_url", "created_at", "updated_at",
            "actor_type", "gov_action_required",
            "implementation_steps", "display_note", "govt_summary",
        ]

    def _directive_dict(self, obj) -> dict:
        directions = obj.action_plan.judgment.court_directions or []
        if 0 <= obj.directive_index < len(directions):
            d = directions[obj.directive_index]
            return d if isinstance(d, dict) else {}
        return {}

    def get_actor_type(self, obj):
        return self._directive_dict(obj).get("actor_type")

    def get_gov_action_required(self, obj):
        return self._directive_dict(obj).get("gov_action_required")

    def get_implementation_steps(self, obj):
        steps = self._directive_dict(obj).get("implementation_steps") or []
        return [s for s in steps if isinstance(s, str)]

    def get_display_note(self, obj):
        return self._directive_dict(obj).get("display_note", "")

    def get_govt_summary(self, obj):
        return self._directive_dict(obj).get("govt_summary", "")

    def get_case_title(self, obj):
        case = obj.action_plan.judgment.case
        return f"{case.petitioner_name} vs {case.respondent_name}"[:120]

    def get_executed_by_name(self, obj):
        u = obj.executed_by
        if not u:
            return None
        return (u.get_full_name() or u.email or u.username)

    def get_proof_file_url(self, obj):
        if obj.proof_file:
            request = self.context.get("request")
            url = obj.proof_file.url
            return request.build_absolute_uri(url) if request else url
        return None
