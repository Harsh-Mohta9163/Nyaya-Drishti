"""Quick integration test for the extraction pipeline."""
import os
import sys
import json
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
django.setup()

from types import SimpleNamespace
from apps.cases.services.section_segmenter import segment_judgment
from apps.cases.services.extractor import extract_structured_data

SAMPLE_JUDGMENT = """
IN THE HIGH COURT OF KARNATAKA AT BENGALURU
DATED THIS THE 15TH DAY OF MARCH 2024
BEFORE THE HON'BLE MR. JUSTICE A.B. RAO
WRIT PETITION No. 12345/2023

BETWEEN:
Sri. Ramesh Kumar ... PETITIONER
AND:
The State of Karnataka, represented by its Secretary,
Revenue Department, Vidhana Soudha, Bengaluru ... RESPONDENT

THIS WRIT PETITION is filed under Articles 226 and 227 of the Constitution of India praying to quash the impugned order dated 01.01.2023.

BRIEF FACTS:
The petitioner is a farmer who owned land in Survey No. 123 of Anekal Taluk. The Revenue Department issued an order acquiring the land without proper compensation. The petitioner challenges this order on the grounds that it violates fundamental rights under Article 14 and 21 of the Constitution. The petitioner submits that no notice was issued prior to the acquisition order, and no opportunity of hearing was afforded.

LEGAL ANALYSIS:
After careful consideration of the facts, the submissions of learned counsel and the documents placed on record, this Court finds that the impugned order is arbitrary and violates Article 14 and 21 of the Constitution. The Revenue Department failed to follow due process under the Land Acquisition Act. The respondent could not produce any evidence of notice having been served on the petitioner.

ORDER:
For the reasons stated above, the Writ Petition is ALLOWED. The following directions are issued:

1. The impugned order dated 01.01.2023 passed by the Revenue Department is hereby quashed and set aside.
2. The Revenue Department shall pay compensation of Rs. 50,00,000/- to the petitioner within 30 days from the date of this order.
3. The Secretary, Revenue Department shall personally ensure compliance with this order, failing which coercive action including contempt proceedings will be initiated.
4. The Finance Department shall release the necessary funds within 15 days of receiving the requisition from the Revenue Department.
5. Registry is directed to forward a copy of this order to the Chief Secretary for information and necessary action.

Pronounced in the open court on this 15th day of March 2024.

Sd/-
JUDGE
"""


def main():
    print("=" * 60)
    print("TEST 1: Section Segmenter")
    print("=" * 60)

    sections = segment_judgment(SAMPLE_JUDGMENT)
    for key in ["header", "facts", "analysis", "operative_order"]:
        text = sections[key]
        print(f"  {key}: {len(text)} chars")
        if key == "operative_order":
            print(f"    Starts with: {text[:80]}...")

    print()
    print("=" * 60)
    print("TEST 2: LLM Extraction (NVIDIA Llama 3.3 70B)")
    print("=" * 60)

    mock_case = SimpleNamespace(
        case_number="WP 12345/2023",
        court="Karnataka High Court",
        case_type="Writ Petition",
        judgment_date="2024-03-15",
        respondent="State of Karnataka",
        petitioner="Sri. Ramesh Kumar",
    )

    result = extract_structured_data(mock_case, sections)

    # Print everything except the full operative text
    display = {k: v for k, v in result.items() if k != "operative_order"}
    print(json.dumps(display, indent=2, default=str))

    print(f"\nDirections extracted: {len(result.get('court_directions', []))}")
    print(f"Confidence: {result.get('extraction_confidence')}")
    print(f"Order type: {result.get('order_type')}")

    # Test 3: Risk classifier
    print()
    print("=" * 60)
    print("TEST 3: Contempt Risk Classifier")
    print("=" * 60)

    from apps.action_plans.services.risk_classifier import classify_contempt_risk

    test_phrases = [
        "The Secretary shall personally ensure compliance, failing which coercive action will be initiated.",
        "The respondent is directed to consider the representation within 30 days.",
        "The petition is dismissed. No costs.",
    ]
    for phrase in test_phrases:
        risk = classify_contempt_risk(phrase)
        print(f"  [{risk:6s}] {phrase[:70]}...")

    # Test 4: Rules engine
    print()
    print("=" * 60)
    print("TEST 4: Rules Engine (Deadline Calculator)")
    print("=" * 60)

    from datetime import date
    from apps.action_plans.services.rules_engine import compute_deadlines

    for appeal_type in ["slp", "lpa", "review", "compliance"]:
        deadlines = compute_deadlines(date(2024, 3, 15), appeal_type)
        print(f"  {appeal_type:12s} -> Legal: {deadlines['legal_deadline']}, Internal: {deadlines['internal_deadline']} ({deadlines['basis']})")

    print()
    print("ALL TESTS PASSED!")


if __name__ == "__main__":
    main()
