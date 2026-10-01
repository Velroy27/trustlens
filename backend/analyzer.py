"""
Analyzer entry point for TrustLens.
Aggregates the modules to return standardized reports.
"""
from typing import Dict, Any
from .url_checker import check_url
from .notice_compare import compare_notices
from .fingerprint import generate_fingerprint
from .database import save_analysis, get_analysis
from .gemini_service import analyze_with_gemini

def _build_standard_report(verdict: str, risk_level: str, risk_score: int, summary: str, red_flags: list, evidence: list, next_action: str) -> Dict[str, Any]:
    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "red_flags": red_flags,
        "evidence": evidence,
        "next_action": next_action
    }

def analyze_text(content: str) -> Dict[str, Any]:
    """
    Analyzes arbitrary text content using Gemini.
    Stores and retrieves from the database using a fingerprint to avoid re-analysis.
    """
    fp = generate_fingerprint(content)
    existing = get_analysis(fp)
    
    if existing and 'verdict' in existing:
        return existing

    # Fallback to Gemini
    gemini_result = analyze_with_gemini(content)
    
    # Map mock Gemini response to standardized format
    report = _build_standard_report(
        verdict=gemini_result.get("verdict", "UNKNOWN"),
        risk_level=gemini_result.get("risk_level", "LOW"),
        risk_score=gemini_result.get("risk_score", 80 if gemini_result.get("risk_level") == "HIGH" else 20),
        summary=gemini_result.get("summary", "Analysis complete."),
        red_flags=gemini_result.get("red_flags", []),
        evidence=gemini_result.get("evidence", []),
        next_action=gemini_result.get("next_action", "Proceed with caution.")
    )
    
    save_analysis(fp, report)
    return report

def analyze_url(url: str) -> Dict[str, Any]:
    """
    Analyzes a URL using local heuristics.
    """
    fp = generate_fingerprint(url)
    existing = get_analysis(fp)
    if existing and 'verdict' in existing:
        return existing
        
    url_res = check_url(url)
    risk_level = url_res.get("risk_level", "LOW")
    risk_score = url_res.get("risk_score", 0)
    
    verdict = "SUSPICIOUS" if risk_score >= 50 else "SAFE"
    if risk_score >= 70:
        verdict = "MALICIOUS"
        
    summary = f"URL evaluated as {risk_level} risk."
    if risk_score > 0:
        summary += f" Detected {len(url_res.get('red_flags', []))} red flag(s)."
        
    report = _build_standard_report(
        verdict=verdict,
        risk_level=risk_level,
        risk_score=risk_score,
        summary=summary,
        red_flags=url_res.get("red_flags", []),
        evidence=url_res.get("evidence", []),
        next_action="Avoid visiting this URL." if verdict != "SAFE" else "URL appears safe."
    )
    
    save_analysis(fp, report)
    return report

def analyze_notice(original_text: str, modified_text: str) -> Dict[str, Any]:
    """
    Analyzes modifications between two notices.
    """
    fp = generate_fingerprint(original_text + "<SEP>" + modified_text)
    existing = get_analysis(fp)
    if existing and 'verdict' in existing:
        return existing

    notice_res = compare_notices(original_text, modified_text)
    risk_level = notice_res.get("risk_level", "LOW")
    
    risk_score = 0
    if risk_level == "MEDIUM":
        risk_score = 50
    elif risk_level == "HIGH":
        risk_score = 85
        
    verdict = "TAMPERED" if notice_res.get("changes") else "AUTHENTIC"
    
    red_flags = []
    evidence = []
    for change in notice_res.get("changes", []):
        if change['type'] == 'replace':
            red_flags.append("Content altered")
            evidence.append(f"Replaced '{change['before']}' with '{change['after']}'")
        elif change['type'] == 'remove':
            red_flags.append("Content removed")
            evidence.append(f"Removed '{change['before']}'")
        elif change['type'] == 'add':
            red_flags.append("Content added")
            evidence.append(f"Added '{change['after']}'")
            
    report = _build_standard_report(
        verdict=verdict,
        risk_level=risk_level,
        risk_score=risk_score,
        summary=notice_res.get("summary", ""),
        red_flags=red_flags,
        evidence=evidence,
        next_action="Review changes carefully." if verdict == "TAMPERED" else "No action needed."
    )
    
    # Store changes as part of the report so frontend can use them
    report['changes'] = notice_res.get("changes", [])
    
    save_analysis(fp, report)
    return report
