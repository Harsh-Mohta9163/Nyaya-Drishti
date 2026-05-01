from django.conf import settings
from django.db import models


class Case(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        EXTRACTED = "extracted", "Extracted"
        REVIEW_PENDING = "review_pending", "Review Pending"
        VERIFIED = "verified", "Verified"
        ACTION_CREATED = "action_created", "Action Plan Created"

    case_number = models.CharField(max_length=100, unique=True)
    court = models.CharField(max_length=200)
    bench = models.CharField(max_length=300, blank=True)
    petitioner = models.TextField()
    respondent = models.TextField()
    case_type = models.CharField(max_length=50)
    judgment_date = models.DateField()
    pdf_file = models.FileField(upload_to="judgments/")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.UPLOADED)
    ocr_confidence = models.FloatField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="uploaded_cases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.case_number


class ExtractedData(models.Model):
    case = models.OneToOneField(Case, on_delete=models.CASCADE, related_name="extracted_data")
    header_data = models.JSONField(default=dict)
    operative_order = models.TextField()
    court_directions = models.JSONField(default=list)
    order_type = models.CharField(max_length=50)
    entities = models.JSONField(default=list)
    extraction_confidence = models.FloatField(default=0.0)
    source_references = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
