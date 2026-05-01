"""
Seed script: Creates sample cases and populates the RAG corpus.

Run: python manage.py shell < seed_data.py
  OR: python seed_data.py
"""
import os
import sys
import json
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from datetime import date, timedelta
from apps.accounts.models import User
from apps.cases.models import Case, ExtractedData
from apps.action_plans.models import ActionPlan
from apps.notifications.models import Notification
from apps.action_plans.services.rag_engine import HybridRAGEngine

# ---------- SAMPLE JUDGMENT TEXTS (for RAG corpus) ----------
SAMPLE_JUDGMENTS = [
    {
        "text": (
            "The writ petition is allowed. The impugned order dated 15.06.2023 passed by the "
            "Revenue Department is hereby quashed. The respondent-State is directed to pay "
            "compensation of Rs. 25,00,000/- to the petitioner within 60 days. The Secretary, "
            "Revenue Department shall ensure compliance, failing which contempt proceedings "
            "shall be initiated."
        ),
        "metadata": {"case_number": "WP 9876/2023", "court": "Karnataka HC", "type": "Land Acquisition"},
    },
    {
        "text": (
            "The appeal is dismissed. The impugned order of the learned Single Judge does not "
            "warrant any interference. The appellants are directed to comply with the order "
            "within 30 days. No costs."
        ),
        "metadata": {"case_number": "WA 543/2023", "court": "Karnataka HC", "type": "Writ Appeal"},
    },
    {
        "text": (
            "Having heard the learned counsel for both parties and having perused the records, "
            "this Court finds merit in the petition. The order of transfer is set aside. The "
            "Government is directed to reinstate the petitioner within 15 days with all "
            "consequential benefits including back wages. The respondent shall personally "
            "appear before this Court on the next date of hearing failing which coercive "
            "action will be taken."
        ),
        "metadata": {"case_number": "WP 4567/2024", "court": "Karnataka HC", "type": "Service Matter"},
    },
    {
        "text": (
            "The petition under Article 226 is disposed of. The respondent-Corporation is "
            "directed to consider the representation of the petitioner and pass appropriate "
            "orders within 4 weeks. Liberty is reserved to the petitioner to approach this "
            "Court if the representation is not considered."
        ),
        "metadata": {"case_number": "WP 2345/2024", "court": "Karnataka HC", "type": "Municipal"},
    },
    {
        "text": (
            "The SLP is allowed in part. The High Court order is modified. The State Government "
            "shall pay compensation of Rs. 1,50,00,000/- for land acquisition under the "
            "Right to Fair Compensation and Transparency in Land Acquisition Act, 2013. "
            "The amount shall be deposited within 90 days. In default of payment, the amount "
            "shall carry interest at 9% per annum."
        ),
        "metadata": {"case_number": "SLP 1234/2024", "court": "Supreme Court", "type": "Land Acquisition"},
    },
    {
        "text": (
            "This Court is constrained to observe that the State Government has not complied "
            "with the earlier order dated 10.01.2024. The Chief Secretary is directed to "
            "file a personal affidavit explaining the reasons for non-compliance. In the "
            "event of continued non-compliance, this Court shall be constrained to initiate "
            "contempt proceedings under Section 12 of the Contempt of Courts Act, 1971."
        ),
        "metadata": {"case_number": "WP 7890/2023", "court": "Karnataka HC", "type": "Contempt"},
    },
    {
        "text": (
            "The pension revision application is allowed. The respondent-State is directed to "
            "revise the pension of the petitioner in accordance with the recommendations of "
            "the 7th Pay Commission within 3 months from the date of this order. The arrears "
            "shall be paid with interest at 6% per annum."
        ),
        "metadata": {"case_number": "WP 3456/2024", "court": "Karnataka HC", "type": "Pension"},
    },
    {
        "text": (
            "The environmental clearance granted by MoEFCC is quashed. The mining operations "
            "in the Western Ghats area shall cease forthwith. The District Collector shall "
            "ensure immediate compliance and file a compliance report within 30 days. The "
            "State Pollution Control Board shall monitor the restoration activities."
        ),
        "metadata": {"case_number": "WP 5678/2023", "court": "Karnataka HC", "type": "Environmental"},
    },
]

# ---------- SAMPLE CASES ----------
SAMPLE_CASES = [
    {
        "case_number": "WP 12345/2024",
        "court": "Karnataka High Court",
        "bench": "Hon'ble Mr. Justice A.B. Rao",
        "petitioner": "Sri. Ramesh Kumar",
        "respondent": "State of Karnataka, Revenue Department",
        "case_type": "Writ Petition",
        "judgment_date": date.today() - timedelta(days=5),
        "status": "action_created",
        "extracted_data": {
            "header_data": {"case_number": "WP 12345/2024", "court": "Karnataka HC", "bench": "Single"},
            "operative_order": (
                "The writ petition is ALLOWED. The impugned order is quashed. "
                "The Revenue Department shall pay Rs. 50,00,000/- within 30 days. "
                "The Secretary shall ensure compliance, failing which contempt proceedings will be initiated."
            ),
            "court_directions": [
                {"text": "Impugned order quashed and set aside", "responsible_entity": "Revenue Department", "deadline_mentioned": None, "action_required": "Quash order"},
                {"text": "Pay compensation of Rs. 50,00,000/- within 30 days", "responsible_entity": "Revenue Department", "deadline_mentioned": "30 days", "action_required": "Pay compensation"},
                {"text": "Secretary shall ensure compliance failing which contempt proceedings", "responsible_entity": "Secretary, Revenue Department", "deadline_mentioned": None, "action_required": "Ensure compliance"},
            ],
            "order_type": "Allowed",
            "entities": [
                {"name": "Revenue Department", "role": "respondent"},
                {"name": "Finance Department", "role": "interested_party"},
            ],
            "extraction_confidence": 0.92,
            "source_references": [{"section": "operative_order", "page": 4}],
        },
        "action_plan": {
            "recommendation": "Comply",
            "recommendation_reasoning": "Order is clear and specific with defined timelines. High contempt risk due to coercive language.",
            "compliance_actions": [
                {"step": 1, "action": "Quash impugned order in records", "deadline": "Immediate", "department": "Revenue Department"},
                {"step": 2, "action": "Process compensation payment of Rs. 50,00,000/-", "deadline": "30 days", "department": "Revenue Department"},
                {"step": 3, "action": "Release funds from treasury", "deadline": "15 days", "department": "Finance Department"},
                {"step": 4, "action": "File compliance affidavit", "deadline": "35 days", "department": "Law Department"},
            ],
            "legal_deadline": date.today() + timedelta(days=25),
            "internal_deadline": date.today() + timedelta(days=16),
            "responsible_departments": ["Revenue Department", "Finance Department"],
            "ccms_stage": "Order Compliance Stage",
            "contempt_risk": "High",
            "similar_cases": [],
            "verification_status": "pending",
        },
    },
    {
        "case_number": "WA 6789/2024",
        "court": "Karnataka High Court",
        "bench": "Hon'ble Chief Justice and Hon'ble Mr. Justice C.D. Patil",
        "petitioner": "M/s. ABC Industries Pvt. Ltd.",
        "respondent": "KSPCB and State of Karnataka",
        "case_type": "Writ Appeal",
        "judgment_date": date.today() - timedelta(days=10),
        "status": "action_created",
        "extracted_data": {
            "header_data": {"case_number": "WA 6789/2024", "court": "Karnataka HC", "bench": "Division"},
            "operative_order": (
                "The appeal is disposed of. KSPCB is directed to reconsider the closure notice "
                "within 4 weeks after affording opportunity of hearing to the appellant. "
                "The interim order shall continue till the disposal of the representation."
            ),
            "court_directions": [
                {"text": "KSPCB to reconsider closure notice within 4 weeks", "responsible_entity": "KSPCB", "deadline_mentioned": "4 weeks", "action_required": "Reconsider closure notice"},
                {"text": "Afford opportunity of hearing to appellant", "responsible_entity": "KSPCB", "deadline_mentioned": None, "action_required": "Conduct hearing"},
            ],
            "order_type": "Disposed",
            "entities": [{"name": "KSPCB", "role": "respondent"}, {"name": "State of Karnataka", "role": "respondent"}],
            "extraction_confidence": 0.88,
            "source_references": [{"section": "operative_order", "page": 3}],
        },
        "action_plan": {
            "recommendation": "Comply",
            "recommendation_reasoning": "Directive to reconsider with hearing is standard procedure.",
            "compliance_actions": [
                {"step": 1, "action": "Schedule hearing for appellant", "deadline": "1 week", "department": "KSPCB"},
                {"step": 2, "action": "Issue reconsidered order", "deadline": "4 weeks", "department": "KSPCB"},
            ],
            "legal_deadline": date.today() + timedelta(days=18),
            "internal_deadline": date.today() + timedelta(days=14),
            "responsible_departments": ["KSPCB", "Environment Department"],
            "ccms_stage": "Order Compliance Stage",
            "contempt_risk": "Medium",
            "similar_cases": [],
            "verification_status": "pending",
        },
    },
    {
        "case_number": "WP 3456/2024",
        "court": "Karnataka High Court",
        "bench": "Hon'ble Mr. Justice E.F. Sharma",
        "petitioner": "Smt. Lakshmi Devi",
        "respondent": "Commissioner, BBMP",
        "case_type": "Writ Petition",
        "judgment_date": date.today() - timedelta(days=3),
        "status": "extracted",
        "extracted_data": {
            "header_data": {"case_number": "WP 3456/2024", "court": "Karnataka HC", "bench": "Single"},
            "operative_order": (
                "Petition dismissed. The petitioner has failed to demonstrate any illegality. "
                "No costs. Liberty to the petitioner to avail appropriate legal remedy."
            ),
            "court_directions": [
                {"text": "Petition dismissed", "responsible_entity": "N/A", "deadline_mentioned": None, "action_required": "No action"},
            ],
            "order_type": "Dismissed",
            "entities": [{"name": "BBMP", "role": "respondent"}],
            "extraction_confidence": 0.95,
            "source_references": [{"section": "operative_order", "page": 2}],
        },
        "action_plan": {
            "recommendation": "Appeal",
            "recommendation_reasoning": "Petition dismissed. Evaluate grounds for SLP or LPA.",
            "compliance_actions": [
                {"step": 1, "action": "Review judgment for appeal grounds", "deadline": "7 days", "department": "Law Department"},
                {"step": 2, "action": "Decide on SLP/LPA filing", "deadline": "14 days", "department": "Law Department"},
            ],
            "legal_deadline": date.today() + timedelta(days=87),
            "internal_deadline": date.today() + timedelta(days=76),
            "responsible_departments": ["BBMP", "Law Department"],
            "ccms_stage": "Proposed for Appeal",
            "contempt_risk": "Low",
            "similar_cases": [],
            "verification_status": "approved",
        },
    },
]


def seed():
    print("=" * 60)
    print("SEEDING DATABASE")
    print("=" * 60)

    # 1. Create users
    users = {}
    for user_data in [
        {"username": "reviewer1", "email": "reviewer1@nyayadrishti.gov.in", "role": "reviewer", "department": "Revenue"},
        {"username": "officer1", "email": "officer1@nyayadrishti.gov.in", "role": "dept_officer", "department": "Revenue"},
        {"username": "depthead1", "email": "depthead1@nyayadrishti.gov.in", "role": "dept_head", "department": "Revenue"},
        {"username": "legal1", "email": "legal1@nyayadrishti.gov.in", "role": "legal_advisor", "department": "Law"},
    ]:
        user, created = User.objects.get_or_create(
            email=user_data["email"],
            defaults={**user_data, "password": "pbkdf2_sha256$720000$test$test"},
        )
        if created:
            user.set_password("NyayaDrishti@123")
            user.save()
            print(f"  Created user: {user.email} ({user.role})")
        users[user_data["role"]] = user

    # 2. Create cases with extracted data and action plans
    for case_data in SAMPLE_CASES:
        extracted = case_data.pop("extracted_data")
        plan_data = case_data.pop("action_plan")

        case, created = Case.objects.get_or_create(
            case_number=case_data["case_number"],
            defaults={**case_data, "uploaded_by": users.get("reviewer")},
        )
        if created:
            print(f"  Created case: {case.case_number}")

            ExtractedData.objects.create(case=case, **extracted)
            ActionPlan.objects.create(case=case, **plan_data)

            # Create notification for high-risk cases
            if plan_data["contempt_risk"] == "High":
                Notification.objects.create(
                    user=users["dept_head"],
                    case=case,
                    notification_type="high_risk",
                    message=f"HIGH RISK: Case {case.case_number} has contempt risk. Immediate action required.",
                )
            # Create deadline notification
            Notification.objects.create(
                user=users["reviewer"],
                case=case,
                notification_type="deadline",
                message=f"Deadline approaching for {case.case_number}: {plan_data['legal_deadline']}",
            )

    # 3. Seed RAG corpus
    print("\n  Seeding RAG corpus...")
    rag = HybridRAGEngine()
    rag.add_documents(SAMPLE_JUDGMENTS)
    print(f"  Added {len(SAMPLE_JUDGMENTS)} documents to RAG corpus")

    # 4. Summary
    print()
    print("=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print(f"  Users: {User.objects.count()}")
    print(f"  Cases: {Case.objects.count()}")
    print(f"  Action Plans: {ActionPlan.objects.count()}")
    print(f"  Notifications: {Notification.objects.count()}")
    print()
    print("  Login credentials (all users): NyayaDrishti@123")
    print("  Accounts:")
    for u in User.objects.all():
        print(f"    {u.email} ({u.role})")


if __name__ == "__main__":
    seed()
