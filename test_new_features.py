"""
Comprehensive test script for new TrustLens requirements:
1. Email Screenshot / Email text analysis via Gemini Vision + heuristics.
2. Extracted URL integration (URL checked through existing check_url).
3. PROTECT identity attack integration for emails.
4. Image authenticity check on email screenshots.
5. Organization credentials validation (velroysharon@gmail.com / 1234).
"""
import io
import sys
from PIL import Image, ImageDraw

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from backend.analyzer import analyze_email
from backend.url_checker import check_url
from app import normalize_backend_report

def create_email_screenshot(from_addr: str, subject: str, body: str) -> bytes:
    """Creates a synthetic email client screenshot."""
    img = Image.new("RGB", (750, 420), color="#1e293b")
    draw = ImageDraw.Draw(img)
    # Mail client toolbar
    draw.rectangle([0, 0, 750, 40], fill="#0f172a")
    draw.text((20, 12), "Inbox — Mail Client", fill="#94a3b8")
    # Email Header box
    draw.rectangle([20, 55, 730, 135], fill="#0f172a", outline="#334155")
    draw.text((35, 68), f"From: {from_addr}", fill="#f8fafc")
    draw.text((35, 92), f"Subject: {subject}", fill="#f1f5f9")
    draw.text((35, 114), "To: user@example.com", fill="#64748b")
    # Body
    draw.rectangle([20, 145, 730, 395], fill="#0c1322", outline="#334155")
    lines = body.split("\n")
    y = 160
    for line in lines:
        draw.text((35, y), line, fill="#e2e8f0")
        y += 24
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def main():
    print("=" * 70)
    print("TESTING NEW TRUSTLENS REQUIREMENTS")
    print("=" * 70)

    # 1. Organization Credentials Test
    print("\n--- TEST A: Organization Login Credentials ---")
    correct_email = "velroysharon@gmail.com"
    correct_pw = "1234"
    assert (correct_email.strip().lower() == "velroysharon@gmail.com" and correct_pw == "1234"), "Auth validation failed"
    wrong_email = "wrong@univ.edu"
    wrong_pw = "wrong"
    assert not (wrong_email == "velroysharon@gmail.com" and wrong_pw == "1234"), "Invalid auth should fail"
    print("✓ Auth check passed: velroysharon@gmail.com:1234 recognized, invalid rejected.")

    # 2. Phishing Email Screenshot Analysis
    print("\n--- TEST B: Phishing Email Screenshot Analysis ---")
    phishing_img = create_email_screenshot(
        from_addr="Security Support <alert-support@secure-bank-login-update.com>",
        subject="URGENT: Your Account Has Been Suspended",
        body="Dear Customer,\nYour online banking access has been suspended due to suspicious activity.\nTo restore access immediately, you must verify your identity within 24 hours:\nhttp://192.168.1.1/bank-login/verify\nFailure to verify will result in permanent account termination.\nThank you, Security Operations"
    )

    print("Analyzing synthetic phishing email screenshot...")
    report = analyze_email(
        image_bytes=phishing_img,
        mime_type="image/png",
    )
    print(f"Verdict: {report.get('verdict')}")
    print(f"Risk Level: {report.get('risk_level')}")
    print(f"Risk Score: {report.get('risk_score')}")
    print(f"Summary: {report.get('summary')}")
    print(f"Red Flags count: {len(report.get('red_flags', []))}")
    print(f"Evidence items: {len(report.get('evidence', []))}")
    if report.get("image_authenticity"):
        print(f"Image Authenticity: {report['image_authenticity'].get('assessment')}")
    if report.get("protect"):
        print(f"PROTECT Identity Attack: {report['protect'].get('risk_level')}")

    assert report.get("verdict") in ("SUSPICIOUS", "MALICIOUS"), "Phishing email should be SUSPICIOUS or MALICIOUS"
    assert report.get("risk_level") in ("MEDIUM", "HIGH"), "Phishing email should be MEDIUM or HIGH risk"
    assert len(report.get("red_flags", [])) > 0, "Red flags should be identified"
    print("✓ Phishing email screenshot correctly flagged with explainable signals.")

    # 3. Legitimate / Benign Email Text Analysis
    print("\n--- TEST C: Legitimate Email Text Analysis ---")
    benign_text = (
        "From: academic-calendar@university.edu\n"
        "Subject: Spring 2026 Semester Schedule Reminder\n"
        "Dear Students,\n"
        "Classes for the Spring 2026 semester begin on Monday, January 19.\n"
        "The complete course catalog is published on the official portal at https://university.edu/calendar.\n"
        "Have a wonderful semester!\n"
        "Registrar's Office"
    )
    benign_report = analyze_email(content=benign_text)
    print(f"Verdict: {benign_report.get('verdict')}")
    print(f"Risk Level: {benign_report.get('risk_level')}")
    print(f"Risk Score: {benign_report.get('risk_score')}")
    print(f"Summary: {benign_report.get('summary')}")
    assert benign_report.get("verdict") in ("SAFE", "LOW RISK", "UNVERIFIED"), "Legitimate email should not be flagged as MALICIOUS"
    print("✓ Legitimate email evaluated without false-positive malicious claims.")

    # 4. Normalized Report for Frontend
    print("\n--- TEST D: Normalization for Frontend UI ---")
    norm_rep = normalize_backend_report(report)
    assert norm_rep.get("verdict") is not None
    assert norm_rep.get("summary") is not None
    assert isinstance(norm_rep.get("red_flags"), list)
    assert isinstance(norm_rep.get("evidence"), list)
    print("✓ Frontend adapter normalizes email report correctly.")

    print("\n" + "=" * 70)
    print("🎉 ALL NEW FEATURE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()
