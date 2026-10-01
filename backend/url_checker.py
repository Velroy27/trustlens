"""
URL checker module for TrustLens.
Performs local heuristic checks on URLs to identify potential risks.
"""
import re
from urllib.parse import urlparse

def check_url(url: str) -> dict:
    """
    Analyzes a URL using local heuristics to detect suspicious patterns.

    Args:
        url (str): The URL to check.

    Returns:
        dict: A dictionary containing the risk level, risk score, red flags, and evidence.
    """
    red_flags = []
    evidence = []
    risk_score = 0

    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if not domain and parsed_url.path:
            domain = parsed_url.path.split('/')[0]
    except Exception as e:
        return {
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "red_flags": ["Failed to parse URL"],
            "evidence": [f"Error: {str(e)}"]
        }

    # 1. IP Address URL
    if re.match(r'^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$', domain):
        red_flags.append("IP Address used instead of domain name")
        evidence.append(f"Domain is an IP address: {domain}")
        risk_score += 40

    # 2. Shortened URLs
    shorteners = {"bit.ly", "tinyurl.com", "t.co", "is.gd", "goo.gl", "owl.li", "deck.ly", "t.me"}
    if domain in shorteners or any(domain.endswith(f".{s}") for s in ["bit.ly", "ly"]):
        red_flags.append("URL shortener service used")
        evidence.append(f"Domain belongs to a known URL shortener: {domain}")
        risk_score += 20

    # 3. Excessively long URLs
    if len(url) > 100:
        red_flags.append("Excessively long URL")
        evidence.append(f"URL length is {len(url)} characters (threshold > 100)")
        risk_score += 15

    # 4. Suspicious Keywords in URL
    suspicious_keywords = ["login", "verify", "update", "account", "secure", "banking", "free", "gift", "password", "auth", "confirm"]
    url_lower = url.lower()
    found_keywords = [kw for kw in suspicious_keywords if kw in url_lower]
    if found_keywords:
        red_flags.append("Suspicious keywords found in URL")
        evidence.append(f"Found keywords: {', '.join(found_keywords)}")
        risk_score += (len(found_keywords) * 15)

    # 5. Suspicious TLDs
    suspicious_tlds = [".xyz", ".top", ".tk", ".ml", ".ga", ".cf", ".gq", ".zip", ".info", ".online"]
    if any(domain.endswith(tld) for tld in suspicious_tlds):
        red_flags.append("Suspicious Top-Level Domain (TLD)")
        evidence.append(f"Domain uses a TLD often associated with spam/phishing: {domain}")
        risk_score += 25

    # 6. Phishing-style domains
    parts = domain.split('.')
    if len(parts) > 4:
        red_flags.append("Excessive subdomains")
        evidence.append(f"Domain has {len(parts)} parts, which is unusually high: {domain}")
        risk_score += 20

    if domain.count('-') > 2:
        red_flags.append("Multiple hyphens in domain")
        evidence.append(f"Domain contains {domain.count('-')} hyphens, common in deceptive domains: {domain}")
        risk_score += 15

    # 7. Excessive special characters in path/query
    special_chars = sum(1 for c in parsed_url.path + parsed_url.query if c in "-_=%?&")
    if special_chars > 15:
        red_flags.append("Excessive special characters")
        evidence.append(f"URL contains {special_chars} special characters in its path/query.")
        risk_score += 10

    # Cap risk score at 100
    risk_score = min(risk_score, 100)

    # Determine Risk Level
    if risk_score >= 70:
        risk_level = "HIGH"
    elif risk_score >= 30:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "red_flags": red_flags,
        "evidence": evidence
    }
