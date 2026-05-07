from django.contrib import admin

from .models import ReviewLog, TrainingPair


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ("action_plan", "reviewer", "review_level", "action", "created_at")
    list_filter = ("review_level", "action")


@admin.register(TrainingPair)
class TrainingPairAdmin(admin.ModelAdmin):
    list_display = ("case", "judgment", "field_name", "used_for_training", "created_at")
    list_filter = ("used_for_training",)
