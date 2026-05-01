from django.contrib import admin

from .models import Case, ExtractedData


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "court", "case_type", "status", "judgment_date", "created_at")
    search_fields = ("case_number", "court", "petitioner", "respondent")
    list_filter = ("status", "case_type", "court")


@admin.register(ExtractedData)
class ExtractedDataAdmin(admin.ModelAdmin):
    list_display = ("case", "order_type", "extraction_confidence", "updated_at")
    search_fields = ("case__case_number", "order_type")
