from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.action_plans.models import ActionPlan
from apps.action_plans.serializers import ActionPlanSerializer

from .models import ReviewLog, TrainingPair
from .serializers import ReviewLogSerializer, ReviewSubmitSerializer, TrainingPairSerializer


class PendingReviewsView(APIView):
    """Returns pending reviews in the PendingReview shape the frontend expects."""
    def get(self, request):
        plans = ActionPlan.objects.select_related("case").filter(
            verification_status="pending"
        ).order_by("-updated_at")

        data = []
        for plan in plans:
            # Determine the current review level based on verification_status
            review_level = "field"  # default
            if plan.verification_status == "field_approved":
                review_level = "directive"
            elif plan.verification_status == "directive_approved":
                review_level = "case"

            data.append({
                "case_id": plan.case_id,
                "case_number": plan.case.case_number,
                "court": plan.case.court,
                "contempt_risk": plan.contempt_risk,
                "review_level": review_level,
                "created_at": plan.updated_at,
            })
        return Response(data)


class SubmitReviewView(APIView):
    def post(self, request, pk):
        action_plan = ActionPlan.objects.select_related("case").get(pk=pk)
        serializer = ReviewSubmitSerializer(data={**request.data, "action_plan": action_plan.pk})
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        ReviewLog.objects.create(
            action_plan=action_plan,
            reviewer=request.user,
            review_level=payload["review_level"],
            action=payload["action"],
            changes=payload.get("changes"),
            notes=payload.get("notes", ""),
        )

        if payload["action"] == "approve":
            action_plan.verification_status = "approved"
        elif payload["action"] == "reject":
            action_plan.verification_status = "rejected"
        else:
            action_plan.verification_status = "edited"
        action_plan.save(update_fields=["verification_status", "updated_at"])

        human_correction = payload.get("human_correction", "").strip()
        field_name = payload.get("field_name", "").strip() or payload["review_level"]
        if human_correction and payload["action"] in {"edit", "reject"}:
            TrainingPair.objects.create(
                case=action_plan.case,
                field_name=field_name,
                ai_output=str(payload.get("changes") or {}),
                human_correction=human_correction,
            )

        return Response({"action_plan": action_plan.pk, "verification_status": action_plan.verification_status}, status=status.HTTP_200_OK)


class ExportTrainingDataView(APIView):
    def get(self, request):
        pairs = TrainingPair.objects.filter(used_for_training=False).order_by("created_at")
        data = TrainingPairSerializer(pairs, many=True).data
        pairs.update(used_for_training=True)
        return Response(data)
