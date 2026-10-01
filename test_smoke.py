"""Quick smoke test of all modules."""
from backend.analyzer import analyze_text, analyze_url, analyze_notice, analyze_protect, analyze_email, analyze_image
from app import normalize_backend_report, _clean_text_string

r = analyze_url("https://example.com")
assert r["verdict"] == "SAFE", f"URL fail: {r['verdict']}"
print("URL check: OK")

r2 = analyze_image(image_bytes=b"")
assert r2["verdict"] == "UNKNOWN"
print("analyze_image(empty guard): OK")

raw = {"verdict": "SAFE", "risk_level": "LOW", "risk_score": 0, "summary": "ok", "red_flags": [], "evidence": [], "next_action": "ok"}
n = normalize_backend_report(raw)
assert n["verdict"] == "SAFE"
print("normalize_backend_report: OK")

cleaned = _clean_text_string("<div class='x'>hello</div>")
assert cleaned == "hello", f"HTML strip failed: {cleaned}"
print("_clean_text_string: OK")

print("All smoke tests passed.")
