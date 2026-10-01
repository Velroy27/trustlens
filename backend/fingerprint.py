"""
Fingerprinting module for TrustLens.
Generates unique identifiers for content using hashing.
"""
import hashlib
import re

def generate_fingerprint(content: str) -> str:
    """
    Generates a SHA-256 fingerprint for the given content.
    Normalizes whitespace and casing before hashing to ensure consistent fingerprints.

    Args:
        content (str): The text content to fingerprint.

    Returns:
        str: The SHA-256 hex digest of the normalized content.
    """
    if not isinstance(content, str):
        content = str(content)
        
    # Normalize: lowercase, strip, and replace multiple whitespaces/newlines with a single space
    normalized = content.lower().strip()
    normalized = re.sub(r'\s+', ' ', normalized)
    
    encoded_content = normalized.encode('utf-8')
    hash_obj = hashlib.sha256(encoded_content)
    return hash_obj.hexdigest()
