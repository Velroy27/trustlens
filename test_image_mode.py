"""
Test for the new Image / Screenshot mode (analyze_image).
Runs a real Gemini Vision call with a synthetic test image.
"""
from PIL import Image, ImageDraw
import io
import sys
from backend.analyzer import analyze_image

print("=" * 70)
print("TEST: Image / Screenshot Mode (analyze_image)")
print("=" * 70)

# Build a synthetic test image
img = Image.new("RGB", (600, 300), color="#0d1117")
draw = ImageDraw.Draw(img)
draw.text((30, 50), "SYNTHETIC TEST IMAGE", fill="white")
draw.text((30, 100), "For TrustLens Image Authenticity Check", fill="#94a3b8")
draw.rectangle([20, 40, 580, 260], outline="#3b82f6", width=2)
buf = io.BytesIO()
img.save(buf, format="PNG")
img_bytes = buf.getvalue()

print(f"Image: {len(img_bytes)} bytes, 600x300 px, PNG")
print("Running analyze_image (calls Gemini Vision)...")

result = analyze_image(image_bytes=img_bytes, mime_type="image/png")

verdict = result.get("verdict", "N/A")
risk_level = result.get("risk_level", "N/A")
risk_score = result.get("risk_score", 0)
summary = result.get("summary", "")
verification_id = result.get("verification_id", "N/A")
auth = result.get("image_authenticity", {})

print(f"Verdict: {verdict}")
print(f"Risk Level: {risk_level}")
print(f"Risk Score: {risk_score}")
print(f"Summary: {summary[:120]}...")
print(f"Assessment: {auth.get('assessment', 'N/A')}")
print(f"Confidence: {auth.get('confidence', 'N/A')}")
signals = auth.get("signals", [])
limitations = auth.get("limitations", [])
print(f"Signals ({len(signals)}): {signals[:2]}")
print(f"Limitations ({len(limitations)}): {limitations[:1]}")
print(f"Verification ID: {verification_id}")

# Assertions
assert verdict, "FAIL: verdict is empty"
assert risk_level, "FAIL: risk_level is empty"
assert isinstance(risk_score, int), "FAIL: risk_score should be int"
assert summary, "FAIL: summary is empty"
assert verification_id and verification_id.startswith("TL-"), "FAIL: bad verification_id"
assert isinstance(auth, dict), "FAIL: image_authenticity should be a dict"
assert auth.get("assessment") in (
    "LIKELY_ORIGINAL", "LIKELY_MANIPULATED", "LIKELY_AI_GENERATED", "UNCERTAIN"
), f"FAIL: unexpected assessment: {auth.get('assessment')}"

# Make sure dangerous certainty claims are not present
dangerous = ["100% fake", "100% ai", "definitely a deepfake", "definitively"]
for d in dangerous:
    assert d.lower() not in summary.lower(), f"FAIL: overconfident claim found: {d}"

print()
print("=" * 70)
print("SUCCESS: Image / Screenshot mode works correctly.")
print("=" * 70)
sys.exit(0)
