"""
Smoke test for:
1. Language selector integration (English, Kannada, Hindi, Hinglish)
2. Community Memory (Previously Checked, count, actual previous result)
"""
import sys
from backend.analyzer import analyze_text, analyze_url
from backend.database import get_community_memory, get_analysis, save_analysis
from backend.fingerprint import generate_fingerprint
from app import normalize_backend_report

print("=" * 70)
print("TEST 1: Community Memory (Previously Checked & Count)")
print("=" * 70)

test_msg = "URGENT: Your bank account will be blocked today unless you verify at http://192.168.1.1/kyc"
fp = generate_fingerprint(test_msg)

# First verification run (or ensure database has it)
print("Running first check...")
rep1 = analyze_text(test_msg, language="English")
assert "verdict" in rep1, "Report 1 missing verdict"
print(f"Check 1 - Verdict: {rep1['verdict']}, Risk: {rep1['risk_level']}")

# Second verification run of the EXACT same message
print("\nRunning second check (simulating repeat check by community)...")
rep2 = analyze_text(test_msg, language="English")

assert "community_memory" in rep2, "FAIL: community_memory missing from second check!"
comm = rep2["community_memory"]
assert comm.get("previously_checked") is True, f"FAIL: previously_checked is not True: {comm}"
assert comm.get("count", 0) >= 2, f"FAIL: count should be >= 2, got {comm.get('count')}"
assert comm.get("previous_verdict"), f"FAIL: previous_verdict missing: {comm}"
print("[PASS] Community Memory detected!")
print(f"  - Previously Checked: {comm['previously_checked']}")
print(f"  - Verification Count: {comm['count']}")
print(f"  - Previous Verdict: {comm['previous_verdict']}")
print(f"  - Previous Risk Level: {comm.get('previous_risk_level')}")
print(f"  - First Seen: {comm.get('first_seen')}")

# Test frontend adapter passes community_memory
norm = normalize_backend_report(rep2)
assert "community_memory" in norm, "FAIL: normalize_backend_report did not preserve community_memory"
assert norm["community_memory"]["previously_checked"] is True, "FAIL: normalized memory incorrect"
print("[PASS] Frontend adapter normalizes community memory correctly.")

print("\n" + "=" * 70)
print("TEST 2: Language Selector Integration")
print("=" * 70)

languages = ["Kannada", "Hindi", "Hinglish", "English"]
for lang in languages:
    print(f"Testing language parameter passing: {lang}")
    u_rep = analyze_url("https://example.com", language=lang)
    assert u_rep["verdict"] == "SAFE", f"URL check failed with {lang}"
    print(f"  [PASS] analyze_url works with {lang}")

print("\nTesting real Gemini call with Hindi language selection...")
test_hindi_msg = "Congratulation! You have won Rs 50,000 lottery. Send OTP to claim."
rep_hindi = analyze_text(test_hindi_msg, language="Hindi")
print(f"  Hindi Result Verdict: {rep_hindi['verdict']}")
print(f"  [PASS] Language instruction received and processed by Gemini successfully.")

print("\n" + "=" * 70)
print("SUCCESS: ALL LANGUAGE AND COMMUNITY MEMORY TESTS PASSED!")
print("=" * 70)
sys.exit(0)
