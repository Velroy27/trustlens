import json
import sys
from backend.url_checker import check_url
from backend.notice_compare import compare_notices
from backend.fingerprint import generate_fingerprint
from backend.database import initialize_database, save_analysis, get_analysis
from backend.gemini_service import analyze_with_gemini
from backend.analyzer import analyze_text, analyze_url, analyze_notice

# Ensure print statements can handle Unicode characters (like ₹) on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def print_section(title):
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")

def main():
    print("Starting TrustLens Backend Tests...")
    initialize_database()

    # 1. Test URL analysis (Direct)
    print_section("1. Direct URL Analysis Test")
    test_url = "https://bit.ly/free-money.xyz"
    print(f"Testing URL: {test_url}")
    url_result = check_url(test_url)
    print(json.dumps(url_result, indent=2))

    # 2. Test notice comparison (Direct)
    print_section("2. Direct Notice Comparison Test")
    original_text = "Workshop on 15 October at 10 AM"
    modified_text = "Workshop on 25 October at 10 AM"
    print(f"Original: '{original_text}'")
    print(f"Modified: '{modified_text}'")
    notice_result = compare_notices(original_text, modified_text)
    print(json.dumps(notice_result, indent=2))

    # 3. Test fingerprint generation
    print_section("3. Fingerprint Generation Test")
    scam_text = "  Congratulations!   Pay ₹1500 to confirm your internship.  "
    print(f"Content: '{scam_text}'")
    fingerprint = generate_fingerprint(scam_text)
    print(f"Generated Normalized Fingerprint: {fingerprint}")

    # 4. Test database storage and retrieval
    print_section("4. Database Storage and Retrieval Test")
    mock_db_result = {
        "text": scam_text,
        "type": "internship_scam",
        "flagged": True
    }
    
    print(f"Saving mock result for fingerprint: {fingerprint}...")
    save_success = save_analysis(fingerprint, mock_db_result)
    print(f"Save successful: {save_success}")
    
    print(f"Retrieving analysis for fingerprint: {fingerprint}...")
    retrieved_analysis = get_analysis(fingerprint)
    print("Retrieved Analysis (with timestamp):")
    print(json.dumps(retrieved_analysis, indent=2))

    # 5. Analyzer Functions
    print_section("5. Analyzer - URL")
    analyzer_url_res = analyze_url(test_url)
    print(json.dumps(analyzer_url_res, indent=2))

    print_section("6. Analyzer - Notice")
    analyzer_notice_res = analyze_notice(original_text, modified_text)
    print(json.dumps(analyzer_notice_res, indent=2))

    print_section("7. Analyzer - Text (Gemini fallback)")
    analyzer_text_res = analyze_text(scam_text)
    print(json.dumps(analyzer_text_res, indent=2))

    print("\nAll backend tests completed.")

if __name__ == "__main__":
    main()
