from django.contrib import admin

from .models import Case, Judgment, Citation


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "court_name", "case_type", "status", "created_at")
    search_fields = ("case_number", "court_name", "petitioner_name", "respondent_name")
    list_filter = ("status", "case_type", "court_name")


@admin.register(Judgment)
class JudgmentAdmin(admin.ModelAdmin):
    list_display = ("case", "document_type", "disposition", "winning_party_type", "date_of_order")
    search_fields = ("case__case_number", "document_type")


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ("citing_judgment", "cited_case_name_raw", "citation_context")
    search_fields = ("cited_case_name_raw",)
