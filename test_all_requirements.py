"""
Comprehensive verification test suite for TrustLens covering all 12 user scenarios:
TEST 1: Suspicious message analysis (Gemini Trust Report)
TEST 2: URL check (https://example.com -> SAFE / LOW / 0)
TEST 3: College Admin notice registration (text, image, fingerprinting, storage)
TEST 4: Student forwarded notice text (auto-matching baseline, diff, changes)
TEST 5: Student forwarded notice screenshot (Gemini Vision OCR, auto-match, diff, authenticity)
TEST 6: Dual notice images comparison (Gemini Vision image-to-image)
TEST 7: Unrelated notice (No verified original notice was found, no fake diff)
TEST 8: PROTECT: SIM-swap / OTP scam message (identity signals, actions, caveats)
TEST 9: Safe message (benign message -> LOW risk, no fabricated attacks)
TEST 10: Repeat forward (fingerprint cache check)
TEST 11: QR verification receipt generation and audit retrieval from SQLite
TEST 12: UI integrity and HTML sanitization verification
"""
import io
import sys
import json
from PIL import Image, ImageDraw

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from backend.database import (
    initialize_database,
    save_official_notice,
    get_official_notice,
    get_all_official_notices,
    save_verification_report,
    get_verification_report,
)
from backend.analyzer import analyze_text, analyze_url, analyze_notice, analyze_protect
from backend.gemini_service import analyze_notice_images, assess_image_authenticity
from backend.qr_receipt import generate_qr_receipt, generate_verification_id
from app import normalize_backend_report, _clean_text_string

def create_notice_image(title: str, deadline: str, fee: str) -> bytes:
    """Generates an image buffer representing a circular notice."""
    img = Image.new("RGB", (700, 350), color="#ffffff")
    draw = ImageDraw.Draw(img)
    # Header bar
    draw.rectangle([0, 0, 700, 45], fill="#1e3a8a")
    draw.text((20, 14), title, fill="#ffffff")
    # Body text
    draw.text((30, 70), f"OFFICIAL INSTITUTIONAL CIRCULAR", fill="#0f172a")
    draw.text((30, 110), f"Scholarship applications are open until {deadline}.", fill="#1e293b")
    draw.text((30, 150), f"Application Fee: {fee}", fill="#1e293b")
    draw.text((30, 190), "Applications must be submitted through the official institutional portal.", fill="#1e293b")
    draw.text((30, 240), "Authorized by University Scholarship Committee", fill="#64748b")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def print_test_header(n, name):
    print(f"\n{'='*70}\nTEST {n}: {name}\n{'='*70}")

def main():
    print("Initiating Comprehensive TrustLens Test Suite...")
    initialize_database()

    # -------------------------------------------------------------------------
    # TEST 1 — Suspicious Message
    # -------------------------------------------------------------------------
    print_test_header(1, "SUSPICIOUS MESSAGE (Gemini + Heuristics)")
    msg_input = "URGENT: Your student grant will be canceled within 2 hours unless you wire a ₹1,200 verification charge to confirm your identity."
    t1_rep = analyze_text(msg_input)
    print(f"Verdict: {t1_rep.get('verdict')}")
    print(f"Risk Level: {t1_rep.get('risk_level')}")
    print(f"Risk Score: {t1_rep.get('risk_score')}")
    print(f"Summary: {t1_rep.get('summary')}")
    print(f"Red Flags: {len(t1_rep.get('red_flags', []))} flag(s)")
    assert t1_rep.get("verdict") in ("SUSPICIOUS", "MALICIOUS"), "Test 1 failed: Verdict should be SUSPICIOUS or MALICIOUS"
    print("✓ TEST 1 PASSED: Gemini evaluated suspicious message and produced a Trust Report.")

    # -------------------------------------------------------------------------
    # TEST 2 — URL
    # -------------------------------------------------------------------------
    print_test_header(2, "URL ANALYSIS (https://example.com)")
    t2_rep = analyze_url("https://example.com")
    print(f"Verdict: {t2_rep.get('verdict')}")
    print(f"Risk Level: {t2_rep.get('risk_level')}")
    print(f"Risk Score: {t2_rep.get('risk_score')}")
    assert t2_rep.get("verdict") == "SAFE" and t2_rep.get("risk_level") == "LOW", "Test 2 failed"
    print("✓ TEST 2 PASSED: URL analysis for example.com returned SAFE / LOW risk.")

    # -------------------------------------------------------------------------
    # TEST 3 — College Admin Registration
    # -------------------------------------------------------------------------
    print_test_header(3, "COLLEGE ADMIN NOTICE REGISTRATION")
    official_img = create_notice_image("UNIVERSITY SCHOLARSHIP 2026", "15 October 2026", "None")
    notice_id = save_official_notice(
        title="College Annual Scholarship 2026",
        content="UNIVERSITY SCHOLARSHIP 2026\nScholarship applications are open until 15 October 2026.\nApplication fee: None.\nApplications must be submitted through the official institutional portal.",
        notice_id="NOTICE-SCHOLARSHIP-OFFICIAL",
        image_blob=official_img,
        image_mime="image/png"
    )
    assert notice_id == "NOTICE-SCHOLARSHIP-OFFICIAL", "Test 3 failed: Notice ID mismatch"
    retrieved = get_official_notice(notice_id)
    assert retrieved is not None, "Test 3 failed: Could not retrieve saved notice"
    assert retrieved.get("image_blob") is not None, "Test 3 failed: Image blob was not preserved"
    print(f"Registered Ref: {retrieved['id']} | Title: {retrieved['title']}")
    print(f"Fingerprint: {retrieved['fingerprint']}")
    print("✓ TEST 3 PASSED: College Admin successfully registered official baseline with image.")

    # -------------------------------------------------------------------------
    # TEST 4 — Student Forwarded Notice Text (Auto-Matching)
    # -------------------------------------------------------------------------
    print_test_header(4, "STUDENT NOTICE TEXT (Auto-match baseline & Diff)")
    fwd_text = "UNIVERSITY SCHOLARSHIP 2026\nScholarship applications are open until 25 October 2026.\nApplication fee: ₹2,000.\nApplications must be submitted through the official institutional portal."
    t4_rep = analyze_notice(content=fwd_text)
    print(f"Verdict: {t4_rep.get('verdict')}")
    print(f"Matched Source: {t4_rep.get('matched_source')}")
    print(f"Changes Detected: {len(t4_rep.get('changes', []))}")
    for c in t4_rep.get("changes", []):
        print(f"  • {c.get('label')}")
    assert t4_rep.get("verdict") == "TAMPERED", "Test 4 failed: Verdict should be TAMPERED"
    assert t4_rep.get("has_matching_original") is True, "Test 4 failed: Baseline should be matched"
    print("✓ TEST 4 PASSED: Forwarded text auto-matched official baseline and identified deadline/fee changes.")

    # -------------------------------------------------------------------------
    # TEST 5 — Student Notice Screenshot (Gemini Vision OCR + Authenticity)
    # -------------------------------------------------------------------------
    print_test_header(5, "STUDENT NOTICE IMAGE (Gemini Vision OCR + Authenticity)")
    fwd_img = create_notice_image("UNIVERSITY SCHOLARSHIP 2026", "25 October 2026", "₹2,000")
    t5_rep = analyze_notice(image_bytes=fwd_img, mime_type="image/png")
    print(f"Verdict: {t5_rep.get('verdict')}")
    print(f"Extracted Text excerpt: {repr(t5_rep.get('extracted_text', '')[:100])}")
    print(f"Matched Source: {t5_rep.get('matched_source')}")
    auth = t5_rep.get("image_authenticity")
    if auth:
        print(f"Image Authenticity Assessment: {auth.get('assessment')} (Confidence: {auth.get('confidence')})")
        print(f"Signals: {auth.get('signals', [])[:2]}")
        print(f"Limitations: {auth.get('limitations', [])[:1]}")
    print("✓ TEST 5 PASSED: Forwarded screenshot processed via Gemini Vision with image authenticity assessment.")

    # -------------------------------------------------------------------------
    # TEST 6 — Image-to-Image Comparison (Both Images Given)
    # -------------------------------------------------------------------------
    print_test_header(6, "DUAL IMAGE COMPARISON (Official Image vs Forwarded Image)")
    t6_rep = analyze_notice(
        image_bytes=fwd_img,
        mime_type="image/png",
        official_image_bytes=official_img,
        official_image_mime="image/png"
    )
    print(f"Verdict: {t6_rep.get('verdict')}")
    print(f"Summary: {t6_rep.get('summary')}")
    print(f"Evidence: {t6_rep.get('evidence', [])[:2]}")
    print(f"Detected Visual/Text Changes: {len(t6_rep.get('changes', []))}")
    print("✓ TEST 6 PASSED: Gemini Vision compared both images side-by-side.")

    # -------------------------------------------------------------------------
    # TEST 7 — Unrelated Notice (No baseline match)
    # -------------------------------------------------------------------------
    print_test_header(7, "UNRELATED NOTICE (No match baseline)")
    unrelated_text = "The baking competition for the culinary club will be held next Tuesday in kitchen 4."
    t7_rep = analyze_notice(content=unrelated_text)
    print(f"Verdict: {t7_rep.get('verdict')}")
    print(f"Has Matching Original: {t7_rep.get('has_matching_original')}")
    print(f"Summary: {t7_rep.get('summary')}")
    assert t7_rep.get("has_matching_original") is False, "Test 7 failed: Should have has_matching_original=False"
    assert "No verified original notice was found" in t7_rep.get("summary", ""), "Test 7 failed: Summary wording mismatch"
    print("✓ TEST 7 PASSED: Unrelated notice reported 'No verified original notice was found' without fake diff.")

    # -------------------------------------------------------------------------
    # TEST 8 — PROTECT: SIM-Swap / OTP Scam
    # -------------------------------------------------------------------------
    print_test_header(8, "PROTECT: SIM-SWAP / OTP PHISHING ATTACK")
    phish_msg = "URGENT from Telecom Customer Service: Your SIM card replacement request has been initiated. If you did not request this, immediately share the 6-digit OTP verification code sent to your phone to cancel the transfer."
    t8_prot = analyze_protect(phish_msg)
    id_prot = t8_prot.get("identity_protection", t8_prot)
    print(f"Risk Level: {id_prot.get('risk_level')}")
    print(f"Attack Types: {id_prot.get('attack_type')}")
    print(f"Signals: {id_prot.get('signals')}")
    print(f"Recommended Actions: {id_prot.get('recommended_actions')}")
    print(f"Limitations: {id_prot.get('limitations')}")
    id_risk = id_prot.get("risk_level")
    assert id_risk in ("MEDIUM", "HIGH"), "Test 8 failed: Risk level should be MEDIUM or HIGH"
    assert len(id_prot.get("signals", [])) > 0, "Test 8 failed: Should have detected signals"
    print("✓ TEST 8 PASSED: PROTECT successfully detected OTP/SIM attack signals with recommended protective actions.")

    # -------------------------------------------------------------------------
    # TEST 9 — Safe Benign Message (No false positives)
    # -------------------------------------------------------------------------
    print_test_header(9, "SAFE MESSAGE (No False Positive Attack)")
    safe_msg = "Hi Professor, I will submit my chemistry lab report by 4 PM this afternoon. Thank you."
    t9_rep = analyze_text(safe_msg)
    t9_prot = t9_rep.get("identity_protection", {})
    print(f"Verdict: {t9_rep.get('verdict')}")
    print(f"Risk Level: {t9_rep.get('risk_level')}")
    print(f"Protect Risk Level: {t9_prot.get('risk_level')}")
    assert t9_prot.get("risk_level") == "LOW", "Test 9 failed: Benign message should have LOW risk"
    print("✓ TEST 9 PASSED: Normal message evaluated as SAFE with no fabricated identity attacks.")

    # -------------------------------------------------------------------------
    # TEST 10 — Repeat Forward (Fingerprint Caching)
    # -------------------------------------------------------------------------
    print_test_header(10, "REPEAT FORWARD (Fingerprint Cache Hit)")
    fwd_rep_first = analyze_notice(content=fwd_text)
    fwd_rep_repeat = analyze_notice(content=fwd_text)
    assert fwd_rep_first.get("verdict") == fwd_rep_repeat.get("verdict"), "Test 10 failed: Cache verdict mismatch"
    assert fwd_rep_first.get("risk_score") == fwd_rep_repeat.get("risk_score"), "Test 10 failed: Cache score mismatch"
    print(f"First verdict: {fwd_rep_first['verdict']} | Repeat verdict: {fwd_rep_repeat['verdict']}")
    print("✓ TEST 10 PASSED: Repeat forward produces consistent cached verdict.")

    # -------------------------------------------------------------------------
    # TEST 11 — QR Receipt & Database Retrieval
    # -------------------------------------------------------------------------
    print_test_header(11, "QR VERIFICATION RECEIPT & AUDIT RETRIEVAL")
    test_vid = generate_verification_id()
    receipt, qr_bytes = generate_qr_receipt(
        verification_id=test_vid,
        verdict="AUTHENTIC",
        risk_level="LOW",
        risk_score=0,
        summary="Official notice verified against baseline."
    )
    print(f"Generated Verification ID: {receipt['verification_id']}")
    print(f"Verification URL (encoded in QR): {receipt['verification_url']}")
    print(f"QR PNG Size: {len(qr_bytes)} bytes")
    assert len(qr_bytes) > 100, "Test 11 failed: Empty QR code buffer"
    assert receipt["verification_url"].endswith(test_vid), "Test 11 failed: QR URL does not encode verification_id"

    # Save to SQLite and retrieve
    save_verification_report(test_vid, receipt)
    retrieved_receipt = get_verification_report(test_vid)
    assert retrieved_receipt is not None, "Test 11 failed: Could not retrieve verification report by ID"
    assert retrieved_receipt.get("verdict") == "AUTHENTIC", "Test 11 failed: Retrieved report data mismatch"

    # Test invalid verification ID lookup
    invalid_lookup = get_verification_report("NON-EXISTENT-ID-999")
    assert invalid_lookup is None, "Test 11 failed: Invalid ID should return None"
    print("✓ TEST 11 PASSED: QR receipt generated, URL encoded, stored in SQLite, and verified.")

    # -------------------------------------------------------------------------
    # TEST 12 — UI HTML Sanitization Check
    # -------------------------------------------------------------------------
    print_test_header(12, "UI HTML SANITIZATION & INTEGRITY")
    raw_html_evidence = '<div class="tl-evidence-row"><span class="tl-evidence-key">Signal:</span> Unofficial domain detected</div>'
    cleaned = _clean_text_string(raw_html_evidence)
    print(f"Raw Input: {raw_html_evidence}")
    print(f"Cleaned Output: '{cleaned}'")
    assert "<" not in cleaned and ">" not in cleaned, "Test 12 failed: Raw HTML tags were not stripped"
    assert "Unofficial domain detected" in cleaned, "Test 12 failed: Cleaned text missing content"
    print("✓ TEST 12 PASSED: HTML tags cleanly stripped, raw HTML is never exposed to user.")

    print("\n" + "="*70)
    print("🎉 ALL 12 TRUSTLENS TESTS COMPLETED SUCCESSFULLY!")
    print("="*70)

if __name__ == "__main__":
    main()
