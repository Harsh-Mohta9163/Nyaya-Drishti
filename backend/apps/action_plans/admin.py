from django.contrib import admin

from .models import ActionPlan


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ("case", "recommendation", "ccms_stage", "contempt_risk", "verification_status", "updated_at")
    list_filter = ("recommendation", "contempt_risk", "verification_status")
    search_fields = ("case__case_number", "ccms_stage")
