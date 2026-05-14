from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class Department(models.Model):
    """A Karnataka State Secretariat administrative department.

    Seeded with the 48 canonical departments from the Karnataka Government
    (Allocation of Business) Rules 1977. Each department carries a keyword
    list used by dept_classifier.classify() to map judgment text to the
    responsible department automatically.
    """

    code = models.SlugField(unique=True, max_length=40,
        help_text="Stable code e.g. HEALTH, PWD, DPAR — never changes")
    name = models.CharField(max_length=200,
        help_text="Display name e.g. 'Health & Family Welfare Department'")
    sector = models.CharField(max_length=120,
        help_text="Category bucket e.g. 'Health, Environment & Culture'")
    keywords = models.JSONField(default=list,
        help_text="Lower-case keywords for the dept_classifier")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Roles.CENTRAL_LAW)
        extra_fields.setdefault("username", email.split("@")[0])
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Roles(models.TextChoices):
        # Statutory roles from Karnataka Conduct of Government Litigation Rules 2025
        HEAD_LEGAL_CELL = "head_legal_cell", "Head of Legal Cell"
        NODAL_OFFICER = "nodal_officer", "Nodal Officer"
        LCO = "lco", "Litigation Conducting Officer"
        PRINCIPAL_SECRETARY = "principal_secretary", "Principal Secretary"
        CENTRAL_LAW = "central_law", "Central Law Department"
        STATE_MONITORING = "state_monitoring", "State Monitoring Committee"
        # Legacy roles (kept so existing users still load — do not use in new UI)
        REVIEWER = "reviewer", "Reviewer"
        DEPT_OFFICER = "dept_officer", "Dept Officer"
        DEPT_HEAD = "dept_head", "Dept Head"
        LEGAL_ADVISOR = "legal_advisor", "Legal Advisor"

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=30, choices=Roles.choices, default=Roles.HEAD_LEGAL_CELL)
    department = models.ForeignKey(
        Department, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="users",
        help_text="The administrative department this user belongs to. "
                  "Null for CENTRAL_LAW / STATE_MONITORING roles (global access).",
    )
    language = models.CharField(max_length=5, default="en")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.email

    @property
    def has_global_access(self) -> bool:
        return self.role in {self.Roles.CENTRAL_LAW, self.Roles.STATE_MONITORING}
