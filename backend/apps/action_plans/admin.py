from django.contrib import admin

from .models import ActionPlan, LimitationRule, CourtCalendar


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ("judgment", "recommendation", "ccms_stage", "verification_status", "updated_at")
    list_filter = ("recommendation", "verification_status")
    search_fields = ("judgment__case__case_number", "ccms_stage")


@admin.register(LimitationRule)
class LimitationRuleAdmin(admin.ModelAdmin):
    list_display = ("action_type", "statutory_days", "condonable", "is_active")
    list_filter = ("condonable", "is_active")


@admin.register(CourtCalendar)
class CourtCalendarAdmin(admin.ModelAdmin):
    list_display = ("date", "court_name", "is_working_day", "entry_type", "holiday_reason")
    list_filter = ("is_working_day", "entry_type", "court_name")
