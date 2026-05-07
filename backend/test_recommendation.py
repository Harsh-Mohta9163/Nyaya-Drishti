import os
import django
import sys
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.action_plans.services.recommendation_pipeline import generate_recommendation

def test_pipeline():
    print("=== Testing Recommendation Pipeline ===\n")
    
    # Mock case input that a user might upload
    test_case_text = """
    The petitioner, a government employee working as a Junior Engineer, was dismissed from service 
    without a formal departmental inquiry after being accused of taking a bribe. The petitioner 
    claims this violates Article 311(2) of the Constitution of India and the principles of natural justice.
    The government argues that the evidence was caught on tape and an inquiry was unnecessary.
    """
    
    print("1. Querying RAG and calling LLM Agents... (This may take ~30 seconds)")
    try:
        # We pass area_of_law="service_law" to pre-filter, but it will fall back gracefully if no cases match
        result = generate_recommendation(
            case_id="TEST_CASE_001",
            case_text=test_case_text,
            area_of_law="service_law",
            court="Supreme Court of India"
        )
        
        print("\n=== Pipeline Succeeded! Final Recommendation ===")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pipeline()
