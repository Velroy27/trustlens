"""
Gemini service module for TrustLens.
Handles interaction with the Gemini API for advanced analysis.
Currently implements a mock version for hackathon MVP.
"""

def analyze_with_gemini(content: str) -> dict:
    """
    Analyzes content using the Gemini model to determine authenticity and risk.
    (MOCK IMPLEMENTATION)

    Args:
        content (str): The text or content to analyze.

    Returns:
        dict: A dictionary containing the mock verdict, risk level, summary,
              red flags, evidence, and next action.
    """
    if not content:
        return {
            "verdict": "UNKNOWN",
            "risk_level": "LOW",
            "summary": "No content provided for analysis.",
            "red_flags": [],
            "evidence": [],
            "next_action": "Provide content to analyze."
        }

    # Mock response structure based on requirements
    return {
        "verdict": "SUSPICIOUS",
        "risk_level": "HIGH",
        "summary": "The provided content exhibits patterns commonly associated with phishing or scam attempts.",
        "red_flags": [
            "Urgent language used ('immediate action required')",
            "Request for sensitive information",
            "Unusual sender address format"
        ],
        "evidence": [
            "Content contains high-pressure tactics urging immediate response.",
            "Potential mismatch with official communications."
        ],
        "next_action": "Do not click any links or provide personal information. Report the message as phishing if applicable."
    }
