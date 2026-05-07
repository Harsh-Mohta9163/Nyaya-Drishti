import uuid
from django.db import models
from django.conf import settings

class Case(models.Model):
    """The abstract legal case (the 'folder'). Tracks appeal lineage."""
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DISPOSED = "disposed", "Disposed"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matter_id = models.UUIDField(default=uuid.uuid4, db_index=True,
        help_text="Groups trial court + HC appeal + SC appeal together")
    cnr_number = models.CharField(max_length=20, unique=True, null=True, blank=True,
        help_text="16-digit eCourts Case Record Number")
    court_name = models.CharField(max_length=200)
    case_type = models.CharField(max_length=100)
    case_number = models.CharField(max_length=255)
    case_year = models.IntegerField()
    petitioner_name = models.TextField()
    respondent_name = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    area_of_law = models.CharField(max_length=100, blank=True)
    primary_statute = models.CharField(max_length=300, blank=True)
    
    # Appeal graph — self-referential FK
    appealed_from_case = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="appeals"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="uploaded_cases"
    )

    class Meta:
        unique_together = ["court_name", "case_number", "case_year"]

    def __str__(self):
        return f"{self.case_type} {self.case_number}/{self.case_year}"


class Judgment(models.Model):
    """A specific PDF document belonging to a Case."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="judgments")
    date_of_order = models.DateField()
    document_type = models.CharField(max_length=50, default="Final Judgment",
        help_text="Final Judgment, Interim Stay, Notice, etc.")
    presiding_judges = models.JSONField(default=list)
    
    # Outcome tracking
    disposition = models.CharField(max_length=30, blank=True,
        help_text="Allowed, Dismissed, Partly Allowed, Remanded")
    winning_party_type = models.CharField(max_length=30, blank=True,
        help_text="Petitioner, Respondent")
    
    # Extracted content
    operative_order_text = models.TextField(blank=True)
    summary_of_facts = models.TextField(blank=True)
    issues_framed = models.JSONField(default=list)
    ratio_decidendi = models.TextField(blank=True,
        help_text="Judge's legal reasoning / analysis")
    court_directions = models.JSONField(default=list)
    
    # Full LLM output backup
    raw_extracted_json = models.JSONField(default=dict)
    
    # Metadata
    entities = models.JSONField(default=list)
    contempt_indicators = models.JSONField(default=list)
    contempt_risk = models.CharField(max_length=20, default="Low",
        help_text="High, Medium, Low")
    financial_implications = models.JSONField(default=dict)
    appeal_type = models.CharField(max_length=30, blank=True, default="none")
    extraction_confidence = models.FloatField(default=0.0)
    ocr_confidence = models.FloatField(null=True, blank=True)
    
    # Precedent validity tracking
    precedent_status = models.CharField(max_length=20, default="good_law",
        choices=[
            ("good_law", "Good Law"),
            ("reversed", "Reversed"),
            ("modified", "Modified"),
            ("overruled", "Overruled"),
            ("unknown", "Unknown"),
        ],
        help_text="Whether this judgment is still valid law for precedent use")
    
    # File storage
    pdf_file = models.FileField(upload_to="judgments/")
    pdf_storage_url = models.URLField(blank=True)
    
    # Processing status
    processing_status = models.CharField(max_length=20, default="uploaded",
        choices=[
            ("uploaded", "Uploaded"),
            ("parsing", "Parsing PDF"),
            ("extracting", "LLM Extracting"),
            ("vectorizing", "Vectorizing"),
            ("complete", "Complete"),
            ("failed", "Failed"),
        ])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.case} — {self.document_type} ({self.date_of_order})"


class Citation(models.Model):
    """Links between judgments (the precedent web)."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    citing_judgment = models.ForeignKey(
        Judgment, on_delete=models.CASCADE, related_name="outgoing_citations")
    cited_case = models.ForeignKey(
        Case, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="incoming_citations",
        help_text="NULL = ghost node (case not yet in DB)")
    cited_case_name_raw = models.CharField(max_length=500)
    citation_id_raw = models.CharField(max_length=200, blank=True,
        help_text="e.g. (2010) 5 SCC 186")
    citation_context = models.CharField(max_length=30, blank=True,
        choices=[
            ("Relied upon", "Relied upon"),
            ("Distinguished", "Distinguished"),
            ("Overruled", "Overruled"),
            ("Referred", "Referred"),
        ],
        help_text="How the citing court used this precedent")
    principle_extracted = models.TextField(blank=True,
        help_text="The legal principle for which this case was cited")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.citing_judgment} → {self.cited_case_name_raw}"
