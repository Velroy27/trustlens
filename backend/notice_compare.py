"""
Notice comparison module for TrustLens.
Compares original and modified texts to identify changes, categorize tampering signals, and assess risk.
"""
import difflib
import re
from typing import List, Dict, Any

MONTH_PATTERN = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b'
DATE_PATTERN = re.compile(rf'(\d{{1,2}}\s+{MONTH_PATTERN}|\b{MONTH_PATTERN}\s+\d{{1,2}}|\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}|\d{{4}})', re.IGNORECASE)
FEE_PATTERN = re.compile(r'(fee|rs\.?|inr|₹|\$|rupees|amount|pay|charge|none|free|\d+,\d+|\d+)', re.IGNORECASE)
URL_OR_CONTACT_PATTERN = re.compile(r'(http|www|\.com|\.org|\.net|\.xyz|\.in|@|\+?\d{10,})', re.IGNORECASE)


def _categorize_change(before: str, after: str) -> str:
    """Categorizes the nature of the change (fee, deadline, contact, or generic text)."""
    comb = f"{before or ''} {after or ''}".lower()

    if "deadline" in comb or DATE_PATTERN.search(comb):
        return "Deadline / Date Changed"
    if "fee" in comb or "₹" in comb or "rs" in comb or "inr" in comb or "$" in comb or "free" in comb:
        return "Application Fee / Payment Changed"
    if URL_OR_CONTACT_PATTERN.search(comb):
        return "URL / Contact Details Changed"
    return "Text Content Modified"


def compare_notices(original_text: str, modified_text: str) -> dict:
    """
    Compares original text with modified text to identify alterations at the word level.

    Args:
        original_text (str): The baseline/original text.
        modified_text (str): The suspicious/modified text.

    Returns:
        dict: A dictionary containing changes, risk_level, risk_score, and a summary.
    """
    if not original_text or not modified_text:
        return {
            "changes": [],
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "Original or modified text is empty."
        }

    changes = []
    orig_words = original_text.split()
    mod_words = modified_text.split()

    matcher = difflib.SequenceMatcher(None, orig_words, mod_words)
    
    has_high_risk_alteration = False

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            before = " ".join(orig_words[i1:i2])
            after = " ".join(mod_words[j1:j2])
            category = _categorize_change(before, after)
            if "Fee" in category or "Deadline" in category or "URL" in category:
                has_high_risk_alteration = True

            changes.append({
                "type": "replace",
                "category": category,
                "before": before,
                "after": after,
                "label": f"{category}: {before} → {after}"
            })
        elif tag == 'delete':
            before = " ".join(orig_words[i1:i2])
            category = _categorize_change(before, "")
            changes.append({
                "type": "remove",
                "category": "Content Removed",
                "before": before,
                "after": None,
                "label": f"Removed: '{before}'"
            })
        elif tag == 'insert':
            after = " ".join(mod_words[j1:j2])
            category = _categorize_change("", after)
            if "Fee" in category or "Deadline" in category or "URL" in category:
                has_high_risk_alteration = True

            changes.append({
                "type": "add",
                "category": "Content Added",
                "before": None,
                "after": after,
                "label": f"Added: '{after}'"
            })

    # Assess Risk Level and Risk Score
    if not changes:
        risk_level = "LOW"
        risk_score = 0
        summary = "No differences detected. The notice text matches the authentic baseline exactly."
    elif has_high_risk_alteration or len(changes) >= 4:
        risk_level = "HIGH"
        risk_score = 85
        summary = f"Detected {len(changes)} modification(s), including critical alterations to deadlines, fees, or contact instructions."
    else:
        risk_level = "MEDIUM"
        risk_score = 50
        summary = f"Detected {len(changes)} modification(s) between the authentic baseline and the forwarded notice."

    return {
        "changes": changes,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary
    }
