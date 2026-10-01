"""
Notice comparison module for TrustLens.
Compares original and modified texts to identify changes and assess risk.
"""
import difflib

def compare_notices(original_text: str, modified_text: str) -> dict:
    """
    Compares original text with modified text to identify alterations at the word level.

    Args:
        original_text (str): The baseline/original text.
        modified_text (str): The suspicious/modified text.

    Returns:
        dict: A dictionary containing changes, risk level, and a summary.
    """
    if not original_text or not modified_text:
        return {
            "changes": [],
            "risk_level": "UNKNOWN",
            "summary": "Original or modified text is empty."
        }

    changes = []
    orig_words = original_text.split()
    mod_words = modified_text.split()

    matcher = difflib.SequenceMatcher(None, orig_words, mod_words)
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            changes.append({
                "type": "replace",
                "before": " ".join(orig_words[i1:i2]),
                "after": " ".join(mod_words[j1:j2])
            })
        elif tag == 'delete':
            changes.append({
                "type": "remove",
                "before": " ".join(orig_words[i1:i2]),
                "after": None
            })
        elif tag == 'insert':
            changes.append({
                "type": "add",
                "before": None,
                "after": " ".join(mod_words[j1:j2])
            })

    # Assess Risk Level based on changes
    risk_level = "LOW"
    summary = "No significant changes detected."

    if changes:
        risk_level = "MEDIUM"
        summary = f"Detected {len(changes)} modification(s) between the original and modified notices."
        
        if len(changes) > 5 or sum(len(c.get("after", "") or "") for c in changes) > 50:
            risk_level = "HIGH"
            summary += " High volume of modifications indicates potential tampering."

    return {
        "changes": changes,
        "risk_level": risk_level,
        "summary": summary
    }
