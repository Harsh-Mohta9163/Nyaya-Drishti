"""Full end-to-end API test."""
import requests
import json

BASE = "http://127.0.0.1:8000/api"

def test():
    # 1. Login
    print("=" * 60)
    print("1. LOGIN")
    r = requests.post(f"{BASE}/auth/login/", json={
        "email": "reviewer1@nyayadrishti.gov.in",
        "password": "NyayaDrishti@123",
    })
    print(f"   Status: {r.status_code}")
    data = r.json()
    token = data.get("access", "")
    print(f"   User: {data.get('user', {}).get('email')}")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Dashboard stats
    print("=" * 60)
    print("2. DASHBOARD STATS")
    r = requests.get(f"{BASE}/dashboard/stats/", headers=headers)
    print(f"   {json.dumps(r.json(), indent=4)}")

    # 3. Cases list
    print("=" * 60)
    print("3. CASES LIST")
    r = requests.get(f"{BASE}/cases/", headers=headers)
    cases = r.json().get("results", r.json())
    for c in (cases if isinstance(cases, list) else []):
        print(f"   {c['case_number']} | {c['status']} | {c['case_type']}")

    # 4. Case detail (first case)
    print("=" * 60)
    print("4. CASE DETAIL")
    r = requests.get(f"{BASE}/cases/1/", headers=headers)
    case = r.json()
    print(f"   Case: {case.get('case_number')}")
    ed = case.get("extracted_data")
    if ed:
        print(f"   Order type: {ed.get('order_type')}")
        print(f"   Directions: {len(ed.get('court_directions', []))}")
        print(f"   Confidence: {ed.get('extraction_confidence')}")
    ap = case.get("action_plan")
    if ap:
        print(f"   Recommendation: {ap.get('recommendation')}")
        print(f"   Contempt risk: {ap.get('contempt_risk')}")
        print(f"   Legal deadline: {ap.get('legal_deadline')}")
        print(f"   Verification: {ap.get('verification_status')}")

    # 5. Deadlines
    print("=" * 60)
    print("5. UPCOMING DEADLINES")
    r = requests.get(f"{BASE}/dashboard/deadlines/", headers=headers)
    for d in r.json():
        print(f"   {d['case_number']} | Deadline: {d['legal_deadline']} | Risk: {d['contempt_risk']}")

    # 6. High risk cases
    print("=" * 60)
    print("6. HIGH RISK CASES")
    r = requests.get(f"{BASE}/dashboard/high-risk/", headers=headers)
    for h in r.json():
        print(f"   {h['case_number']} | {h['recommendation']} | Deadline: {h['legal_deadline']}")

    # 7. Pending reviews
    print("=" * 60)
    print("7. PENDING REVIEWS")
    r = requests.get(f"{BASE}/reviews/pending/", headers=headers)
    rdata = r.json()
    pending = rdata.get("results", rdata) if isinstance(rdata, dict) else rdata
    print(f"   Count: {len(pending) if isinstance(pending, list) else 'N/A'}")

    # 8. Notifications
    print("=" * 60)
    print("8. NOTIFICATIONS")
    # Login as dept_head to see high-risk notifications
    r2 = requests.post(f"{BASE}/auth/login/", json={
        "email": "depthead1@nyayadrishti.gov.in",
        "password": "NyayaDrishti@123",
    })
    h2 = {"Authorization": f"Bearer {r2.json().get('access', '')}"}
    r = requests.get(f"{BASE}/notifications/", headers=h2)
    for n in r.json():
        print(f"   [{n['notification_type']}] {n['message'][:60]}...")

    # 9. Translation test
    print("=" * 60)
    print("9. TRANSLATION (EN -> Kannada)")
    r = requests.post(f"{BASE}/translation/", headers=headers, json={
        "text": "The petition is allowed. Pay compensation within 30 days.",
        "source_lang": "eng_Latn",
        "target_lang": "kan_Knda",
    })
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        translated = r.json().get("translated_text", "")
        try:
            print(f"   Translated: {translated[:100]}")
        except UnicodeEncodeError:
            print(f"   Translated: [Kannada text received, {len(translated)} chars - cannot display in Windows console]")

    print("=" * 60)
    print("ALL API TESTS COMPLETE!")


if __name__ == "__main__":
    test()
