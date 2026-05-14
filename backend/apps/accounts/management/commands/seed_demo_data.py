"""Seed the 48 Karnataka State Secretariat departments and demo user accounts.

Idempotent — safe to re-run. Updates existing records by `code`.

Usage:
    python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Department, User


# Canonical 48-department taxonomy. Tuples: (code, name, sector, keywords).
# Keywords are matched case-insensitively against (case_text + entities + parties)
# by apps.cases.services.dept_classifier.
DEPARTMENTS = [
    # ── Finance, Law & Core Administration ──
    ("FINANCE", "Finance Department", "Finance, Law & Core Administration",
        ["finance department", "finance secretary", "budget", "treasury", "consolidated fund",
         "revenue allocation", "financial sanction", "budgetary clearance", "expenditure"]),
    ("DPAR", "Department of Personnel & Administrative Reforms", "Finance, Law & Core Administration",
        ["personnel", "administrative reforms", "dpar", "civil services", "kcsr",
         "cadre", "deputation", "departmental promotion committee", "dpc", "service rules"]),
    ("LAW", "Department of Law, Justice & Parliamentary Affairs", "Finance, Law & Core Administration",
        ["law department", "law secretary", "parliamentary affairs", "law commission",
         "legislative drafting", "advocate general", "legal opinion"]),
    ("E_GOV", "Department of e-Governance", "Finance, Law & Core Administration",
        ["e-governance", "digital governance", "e-office", "ccms", "centre for e-governance"]),
    ("TREASURIES", "Department of Treasuries", "Finance, Law & Core Administration",
        ["treasury", "treasuries", "khajane", "treasury officer", "bills section"]),
    ("REVENUE", "Revenue Department", "Finance, Law & Core Administration",
        ["revenue department", "deputy commissioner", "tahsildar", "tehsildar", "land records",
         "rtc", "mutation", "land revenue", "patta", "khata", "village accountant",
         "sub-registrar", "stamp duty", "assistant commissioner"]),
    ("PLANNING", "Planning, Programme Monitoring & Statistics Department", "Finance, Law & Core Administration",
        ["planning department", "programme monitoring", "statistics", "five year plan",
         "annual plan", "programme implementation"]),
    ("IPR", "Information & Public Relations Department", "Finance, Law & Core Administration",
        ["information and public relations", "ipr department", "press accreditation",
         "varthe", "public relations officer"]),
    ("GAZETTEER", "Gazetteer Department", "Finance, Law & Core Administration",
        ["gazetteer", "state gazetteer", "district gazetteer"]),

    # ── Agriculture, Food & Rural Development ──
    ("AGRICULTURE", "Agriculture Department", "Agriculture, Food & Rural Development",
        ["agriculture", "farmer", "crop", "seed", "fertilizer", "pmkisan",
         "raita", "krishi", "agricultural extension"]),
    ("AHVS", "Animal Husbandry & Veterinary Services Department", "Agriculture, Food & Rural Development",
        ["animal husbandry", "veterinary", "livestock", "dairy", "cattle",
         "poultry", "fodder", "passu sangrakshana"]),
    ("FISHERIES", "Fisheries Department", "Agriculture, Food & Rural Development",
        ["fisheries", "fishermen", "marine fishing", "inland fisheries", "fish farming"]),
    ("HORTICULTURE", "Horticulture Department", "Agriculture, Food & Rural Development",
        ["horticulture", "floriculture", "fruit", "vegetable cultivation", "coconut development"]),
    ("AG_MARKETING", "Agricultural Marketing Department", "Agriculture, Food & Rural Development",
        ["agricultural marketing", "apmc", "mandi", "krishi marata", "marketing committee"]),
    ("RDPR", "Rural Development & Panchayat Raj Department", "Agriculture, Food & Rural Development",
        ["rural development", "panchayat raj", "rdpr", "gram panchayat", "zilla panchayat",
         "taluk panchayat", "mgnrega", "nrega", "rural employment", "village development"]),
    ("FOOD_CIVIL", "Food, Civil Supplies & Consumer Affairs Department", "Agriculture, Food & Rural Development",
        ["food and civil supplies", "civil supplies", "consumer affairs", "ration shop",
         "pds", "public distribution", "anna bhagya", "essential commodities"]),
    ("COOPERATION", "Co-operation Department", "Agriculture, Food & Rural Development",
        ["co-operation department", "cooperative society", "cooperative bank",
         "registrar of co-operative", "sahakara"]),

    # ── Infrastructure, Utilities & Transport ──
    ("PWD", "Public Works Department", "Infrastructure, Utilities & Transport",
        ["public works", "pwd", "lok karya ilaakhe", "road construction",
         "bridge construction", "buildings department", "national highway", "state highway"]),
    ("ENERGY", "Energy Department", "Infrastructure, Utilities & Transport",
        ["energy department", "kptcl", "bescom", "hescom", "mescom", "gescom", "cescom",
         "kpcl", "kerc", "power generation", "electricity", "transmission", "renewable energy"]),
    ("WATER_RESOURCES", "Water Resources Department", "Infrastructure, Utilities & Transport",
        ["water resources", "irrigation", "dam", "canal", "krishna bhagya jala nigam",
         "cauvery neeravari", "tungabhadra", "tank irrigation"]),
    ("TRANSPORT", "Transport Department", "Infrastructure, Utilities & Transport",
        ["transport department", "rto", "regional transport", "ksrtc", "bmtc",
         "motor vehicles", "driving licence", "registration of motor vehicles", "permit"]),
    ("HOUSING", "Housing Department", "Infrastructure, Utilities & Transport",
        ["housing department", "karnataka housing board", "khb", "rajiv gandhi housing",
         "ashraya scheme", "slum board", "kslcb", "housing scheme"]),
    ("URBAN_DEV", "Urban Development Department", "Infrastructure, Utilities & Transport",
        ["urban development", "bbmp", "bda", "city municipal council", "town panchayat",
         "udyogamitra", "metropolitan planning", "town planning", "bwssb", "kuwsdb"]),
    ("INFRA_DEV", "Infrastructure Development Department", "Infrastructure, Utilities & Transport",
        ["infrastructure development department", "kiadb", "kssidc", "infrastructure project",
         "ppp project", "industrial corridor"]),

    # ── Education & Skill Development ──
    ("SCHOOL_EDU", "Department of School Education & Literacy", "Education & Skill Development",
        ["school education", "primary education", "secondary education", "literacy",
         "sarva shiksha", "rmsa", "ssa", "midday meal", "bele bagina",
         "department of public instruction", "dpi"]),
    ("HIGHER_EDU", "Higher Education Department", "Education & Skill Development",
        ["higher education", "university", "college education", "ugc", "aicte",
         "collegiate education", "private aided"]),
    ("MED_EDU", "Medical Education Department", "Education & Skill Development",
        ["medical education", "medical college", "rajiv gandhi university of health sciences",
         "rguhs", "mbbs", "post graduate medical", "dental college"]),
    ("TECH_EDU", "Department of Technical Education", "Education & Skill Development",
        ["technical education", "polytechnic", "engineering college", "iti",
         "directorate of technical education", "dte"]),
    ("SKILL_DEV", "Skill Development, Entrepreneurship & Livelihood Department", "Education & Skill Development",
        ["skill development", "entrepreneurship", "livelihood", "nsdc",
         "kaushal", "skill mission"]),

    # ── Social Welfare & Empowerment ──
    ("SOCIAL_WELFARE", "Social Welfare Department", "Social Welfare & Empowerment",
        ["social welfare", "scheduled caste", "sc/st", "samaja kalyana", "sc welfare",
         "scheduled tribe welfare", "post matric scholarship"]),
    ("BCWD", "Backward Classes Welfare Department", "Social Welfare & Empowerment",
        ["backward classes welfare", "obc welfare", "hindulida varga", "bcwd"]),
    ("MINORITIES", "Minorities Welfare Department", "Social Welfare & Empowerment",
        ["minorities welfare", "alpasankhyataru", "minority development", "wakf board"]),
    ("TRIBAL", "Tribal Welfare Department", "Social Welfare & Empowerment",
        ["tribal welfare", "scheduled tribe", "girijana kalyana", "soliga", "jenu kuruba"]),
    ("WCD", "Women & Child Development Department", "Social Welfare & Empowerment",
        ["women and child development", "wcd", "anganwadi", "icds",
         "bhagyalakshmi", "stree shakti", "child protection"]),
    ("DA_SC", "Empowerment of Differently Abled and Senior Citizens Department", "Social Welfare & Empowerment",
        ["differently abled", "senior citizen", "persons with disability", "pwd act",
         "vikalachetanaru", "old age home"]),
    ("LABOUR", "Labour Department", "Social Welfare & Empowerment",
        ["labour department", "labour commissioner", "factories inspector",
         "industrial dispute", "workman", "minimum wages", "epf", "esi", "kar shrama",
         "contract labour", "bonded labour", "labour enforcement officer"]),
    ("YOUTH_SPORTS", "Youth Empowerment & Sports Department", "Social Welfare & Empowerment",
        ["youth empowerment", "sports department", "yuvajana", "yuva sashakthikarana",
         "stadium", "sports authority"]),

    # ── Commerce, Industry & Technology ──
    ("INDUSTRIES", "Industries & Commerce Department", "Commerce, Industry & Technology",
        ["industries department", "industries and commerce", "kiadb", "kssidc", "msme",
         "industrial policy", "single window clearance", "udyog mitra"]),
    ("IT_BT", "Information Technology, Biotechnology and Science & Technology Department", "Commerce, Industry & Technology",
        ["it/bt department", "information technology", "biotechnology", "science and technology",
         "startup karnataka", "bengaluru it", "esdm"]),
    ("HANDLOOMS", "Handlooms & Textiles Department", "Commerce, Industry & Technology",
        ["handlooms", "textiles", "khadi", "powerloom", "weaver", "silk textile"]),
    ("TOURISM", "Tourism Department", "Commerce, Industry & Technology",
        ["tourism department", "karnataka tourism", "ktdc", "monument", "heritage site",
         "hotel licence", "tourist circuit"]),
    ("EXCISE", "Excise Department", "Commerce, Industry & Technology",
        ["excise department", "abkari", "liquor licence", "wine shop", "bar and restaurant",
         "country liquor", "imfl"]),

    # ── Health, Environment & Culture ──
    ("HEALTH", "Health & Family Welfare Department", "Health, Environment & Culture",
        ["health and family welfare", "health department", "hospital", "primary health centre",
         "phc", "chc", "district hospital", "medical officer", "ayushman", "drug controller",
         "vaccination", "family welfare", "national health mission"]),
    ("FOREST", "Forest, Ecology & Environment Department", "Health, Environment & Culture",
        ["forest department", "ecology", "environment", "ksbb", "kspcb",
         "wildlife sanctuary", "national park", "conservator of forests", "deputy conservator",
         "forest land diversion", "crz", "environmental clearance"]),
    ("KANNADA_CULTURE", "Kannada & Culture Department", "Health, Environment & Culture",
        ["kannada and culture", "kannada sahitya", "rangayana", "lalitha kala academy",
         "drama academy", "dasara"]),
    ("AYUSH", "AYUSH Department", "Health, Environment & Culture",
        ["ayush", "ayurveda", "yoga", "unani", "siddha", "homoeopathy", "naturopathy"]),
    ("MUZRAI", "Muzrai (Religious and Charitable Endowments) Department", "Health, Environment & Culture",
        ["muzrai", "religious endowments", "charitable endowments", "temple administration",
         "endowment commissioner", "devasthana"]),
    ("HOME", "Home Department", "Health, Environment & Culture",
        ["home department", "police", "law and order", "fire force", "prison", "jail",
         "civil defence", "sp", "dgp", "cid", "lokayukta", "cbi", "passport verification",
         "internal security"]),
]


DEMO_USERS = [
    # username, email, password, role, dept_code
    ("health_hlc", "health_hlc@demo.local", "demo123", "head_legal_cell", "HEALTH"),
    ("transport_hlc", "transport_hlc@demo.local", "demo123", "head_legal_cell", "TRANSPORT"),
    ("education_hlc", "education_hlc@demo.local", "demo123", "head_legal_cell", "SCHOOL_EDU"),
    ("labour_hlc", "labour_hlc@demo.local", "demo123", "head_legal_cell", "LABOUR"),
    ("revenue_hlc", "revenue_hlc@demo.local", "demo123", "head_legal_cell", "REVENUE"),
    # LCO demo accounts — Execution dashboard is their landing view.
    ("health_lco", "health_lco@demo.local", "demo123", "lco", "HEALTH"),
    ("finance_lco", "finance_lco@demo.local", "demo123", "lco", "FINANCE"),
    ("energy_lco", "energy_lco@demo.local", "demo123", "lco", "ENERGY"),
    # Nodal Officer demo accounts — Deadlines view is their landing.
    ("health_nodal", "health_nodal@demo.local", "demo123", "nodal_officer", "HEALTH"),
    ("finance_nodal", "finance_nodal@demo.local", "demo123", "nodal_officer", "FINANCE"),
    ("energy_nodal", "energy_nodal@demo.local", "demo123", "nodal_officer", "ENERGY"),
    ("central_law_admin", "central_law@demo.local", "demo123", "central_law", None),
    ("state_monitoring", "monitoring@demo.local", "demo123", "state_monitoring", None),
]


class Command(BaseCommand):
    help = "Seed the 48 Karnataka secretariat departments and demo users."

    @transaction.atomic
    def handle(self, *args, **options):
        created_depts = 0
        updated_depts = 0
        for code, name, sector, keywords in DEPARTMENTS:
            dept, was_created = Department.objects.update_or_create(
                code=code,
                defaults={"name": name, "sector": sector,
                          "keywords": keywords, "is_active": True},
            )
            if was_created:
                created_depts += 1
            else:
                updated_depts += 1

        self.stdout.write(self.style.SUCCESS(
            f"Departments: {created_depts} created, {updated_depts} updated, "
            f"total now = {Department.objects.count()}"
        ))

        created_users = 0
        for username, email, password, role, dept_code in DEMO_USERS:
            dept = Department.objects.filter(code=dept_code).first() if dept_code else None
            user = User.objects.filter(username=username).first()
            if user:
                user.role = role
                user.department = dept
                user.set_password(password)
                user.save()
                self.stdout.write(f"  Updated demo user: {username} ({role}, dept={dept_code})")
            else:
                User.objects.create_user(
                    email=email, password=password,
                    username=username, role=role, department=dept,
                )
                created_users += 1
                self.stdout.write(f"  Created demo user: {username} ({role}, dept={dept_code})")

        self.stdout.write(self.style.SUCCESS(
            f"Demo users: {created_users} created. Default password for all: 'demo123'"
        ))
