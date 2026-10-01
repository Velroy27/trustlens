"""
Gemini service module for TrustLens.
Handles interaction with the Gemini API for advanced content verification.
Uses google-genai SDK with API key loaded from the root .env file.
"""

import os
import ssl
import json
import re
import time
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Ensure environment variables from the project root .env are loaded
DOTENV_PATH = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=DOTENV_PATH)

# Primary model: Gemini 3.8 Flash (stable), with fallbacks for high-demand spikes
PRIMARY_MODEL = "gemini-3.8-flash"
FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]

ANALYSIS_PROMPT = """You are TrustLens, an expert digital security and verification analyst.

Analyze the given content to identify phishing attempts, financial scams, impersonation, or misinformation.

Evaluate the content thoroughly and output a valid JSON object with the following fields:
- "verdict": Exactly one of "SAFE", "SUSPICIOUS", "MALICIOUS"
- "risk_level": Exactly one of "LOW", "MEDIUM", "HIGH"
- "risk_score": An integer from 0 (completely safe) to 100 (critical threat)
- "summary": A concise 1-2 sentence professional assessment of the content
- "red_flags": A JSON array of specific red flag strings identified (empty array if none)
- "evidence": A JSON array of factual observations/evidence supporting your evaluation (empty array if none)
- "next_action": A concrete, actionable recommendation for the user

Content to analyze:
\"\"\"
{content}
\"\"\"
"""


def _get_api_key() -> str:
    """Retrieve GEMINI_API_KEY from environment, refreshing from .env if needed."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key and os.path.exists(DOTENV_PATH):
        load_dotenv(dotenv_path=DOTENV_PATH, override=True)
        key = os.environ.get("GEMINI_API_KEY")
    if not key or not key.strip():
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. "
            "Please create a .env file in the project root containing: GEMINI_API_KEY=your_key_here"
        )
    return key.strip()


def _get_ssl_context() -> ssl.SSLContext:
    """
    Creates an SSL context that loads Windows system certificates.
    Prevents [SSL: CERTIFICATE_VERIFY_FAILED] issues common on Windows/corporate environments.
    """
    ctx = ssl.create_default_context()
    if hasattr(ssl, "enum_certificates"):
        for store_name in ("ROOT", "CA"):
            try:
                for cert, encoding, trust in ssl.enum_certificates(store_name):
                    try:
                        ctx.load_verify_locations(cadata=cert)
                    except Exception:
                        pass
            except Exception:
                pass
    return ctx


def _create_genai_client(api_key: str):
    """Initializes and returns a configured google.genai Client."""
    from google import genai
    from google.genai import types

    ssl_context = _get_ssl_context()
    http_opts = types.HttpOptions(client_args={"verify": ssl_context})
    return genai.Client(api_key=api_key, http_options=http_opts)


def _sanitize_error_message(error: Exception, api_key: str) -> str:
    """Strips any occurrence of the API key from exception messages to prevent secret leakage."""
    msg = str(error)
    if api_key and api_key in msg:
        msg = msg.replace(api_key, "[REDACTED_API_KEY]")
    # Also mask any generic Gemini-like keys (e.g., AIza...)
    msg = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[REDACTED_API_KEY]', msg)
    return msg


def _parse_gemini_response(response_text: str) -> Dict[str, Any]:
    """
    Extracts and standardizes the JSON analysis report from Gemini's response text.
    Handles potential markdown code fences and validates all required fields.
    """
    text = (response_text or "").strip()

    # Strip markdown code blocks if returned
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)
    except Exception as parse_err:
        raise ValueError(f"Failed to parse JSON response: {parse_err}. Response was: {text[:150]}")

    # Standardize verdict
    verdict = str(data.get("verdict", "SUSPICIOUS")).upper().strip()
    if verdict not in ("SAFE", "SUSPICIOUS", "MALICIOUS"):
        verdict = "SUSPICIOUS"

    # Standardize risk_level
    risk_level = str(data.get("risk_level", "MEDIUM")).upper().strip()
    if risk_level not in ("LOW", "MEDIUM", "HIGH"):
        risk_level = "MEDIUM"

    # Standardize risk_score
    try:
        risk_score = int(data.get("risk_score", 75 if risk_level == "HIGH" else 45 if risk_level == "MEDIUM" else 15))
        risk_score = max(0, min(100, risk_score))
    except (TypeError, ValueError):
        risk_score = 80 if risk_level == "HIGH" else 40 if risk_level == "MEDIUM" else 10

    # Ensure list types for flags & evidence
    raw_red_flags = data.get("red_flags") or []
    if isinstance(raw_red_flags, list):
        red_flags = [str(item).strip() for item in raw_red_flags if item]
    else:
        red_flags = [str(raw_red_flags).strip()] if raw_red_flags else []

    raw_evidence = data.get("evidence") or []
    if isinstance(raw_evidence, list):
        evidence = [str(item).strip() for item in raw_evidence if item]
    else:
        evidence = [str(raw_evidence).strip()] if raw_evidence else []

    summary = str(data.get("summary") or "Content analysis completed successfully.").strip()
    next_action = str(data.get("next_action") or "Review details carefully before taking action.").strip()

    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "red_flags": red_flags,
        "evidence": evidence,
        "next_action": next_action,
    }


def analyze_with_gemini(content: str, language: str = "English") -> Dict[str, Any]:
    """
    Analyzes content using the Gemini API to determine authenticity and security risk.

    Args:
        content (str): The text or message content to analyze.
        language (str): Target response language (English, Kannada, Hindi, Hinglish).

    Returns:
        dict: Standardized analysis dictionary containing:
              verdict, risk_level, risk_score, summary, red_flags, evidence, next_action.

    Raises:
        EnvironmentError: If GEMINI_API_KEY is missing or empty.
        RuntimeError: If all candidate models fail or response cannot be parsed.
    """
    if not content or not content.strip():
        return {
            "verdict": "UNKNOWN",
            "risk_level": "LOW",
            "risk_score": 0,
            "summary": "No content provided for verification.",
            "red_flags": [],
            "evidence": [],
            "next_action": "Paste text or message content to analyze.",
        }

    api_key = _get_api_key()
    client = _create_genai_client(api_key)

    from google.genai import types
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.2,
    )
    prompt = ANALYSIS_PROMPT.format(content=content.strip())
    if language and language.strip().lower() != "english":
        lang_str = language.strip()
        prompt += (
            f"\n\nIMPORTANT LANGUAGE REQUIREMENT:\n"
            f"Please respond and write 'summary', 'red_flags', 'evidence', and 'next_action' in {lang_str}.\n"
            f"Keep the JSON keys and English values for 'verdict' ('SAFE', 'SUSPICIOUS', 'MALICIOUS') and 'risk_level' ('LOW', 'MEDIUM', 'HIGH') strictly in English."
        )

    # Try primary requested model, then resilient fallbacks if temporary high demand occurs
    candidate_models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        # Give primary model up to 2 attempts with a short backoff for transient 503 spikes
        max_attempts = 2 if model_name == PRIMARY_MODEL else 1
        for attempt in range(max_attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    return _parse_gemini_response(response.text)
            except Exception as e:
                last_error = e
                err_str = str(e)
                # For unrecoverable client errors (e.g. invalid auth), fail fast immediately
                if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                    clean_msg = _sanitize_error_message(e, api_key)
                    raise RuntimeError(f"Authentication failed with Gemini API: {clean_msg}") from None
                # If temporary high demand, back off briefly if another attempt remains
                if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str) and attempt + 1 < max_attempts:
                    time.sleep(1.5)
                    continue
                # Otherwise break out to try next candidate model
                break

    # If all models failed
    sanitized_err = _sanitize_error_message(last_error or Exception("No response received"), api_key)
    raise RuntimeError(f"Gemini analysis service unavailable: {sanitized_err}") from None


def extract_text_from_image(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Extracts visible text from an image or screenshot using Gemini Vision.

    Args:
        image_bytes (bytes): Raw bytes of the image file.
        mime_type (str): MIME type of the image (e.g., 'image/png', 'image/jpeg', 'image/webp').

    Returns:
        str: Clean extracted text from the image.

    Raises:
        ValueError: If image_bytes is empty.
        EnvironmentError: If GEMINI_API_KEY is missing or invalid.
        RuntimeError: If Vision extraction fails across all candidate models.
    """
    if not image_bytes:
        raise ValueError("No image data provided for text extraction.")

    api_key = _get_api_key()
    client = _create_genai_client(api_key)

    from google.genai import types
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type or "image/png")
    prompt = (
        "Extract all readable text from this document, circular, notice, or screenshot accurately. "
        "Preserve line breaks where appropriate. "
        "Do not analyze, do not summarize, and do not add any commentary or conversational filler. "
        "Return ONLY the extracted text."
    )

    candidate_models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        max_attempts = 2 if model_name == PRIMARY_MODEL else 1
        for attempt in range(max_attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[image_part, prompt],
                )
                if response and response.text:
                    extracted = response.text.strip()
                    # Strip accidental markdown code blocks if the model wrapped the text
                    if extracted.startswith("```"):
                        lines = extracted.splitlines()
                        if lines and lines[0].startswith("```"):
                            lines = lines[1:]
                        if lines and lines[-1].strip() == "```":
                            lines = lines[:-1]
                        extracted = "\n".join(lines).strip()
                    return extracted
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                    clean_msg = _sanitize_error_message(e, api_key)
                    raise RuntimeError(f"Authentication failed with Gemini API: {clean_msg}") from None
                if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str) and attempt + 1 < max_attempts:
                    time.sleep(1.5)
                    continue
                break



def analyze_notice_images(
    official_bytes: bytes,
    forwarded_bytes: bytes,
    official_mime: str = "image/png",
    forwarded_mime: str = "image/png",
) -> Dict[str, Any]:
    """
    Sends BOTH an official notice image and a forwarded/suspected-tampered notice image
    to Gemini Vision for side-by-side visual and textual comparison.

    Returns:
        dict: verdict, risk_level, risk_score, summary, red_flags, evidence,
              next_action, changes (list of human-readable change strings).
    """
    if not official_bytes:
        raise ValueError("No official notice image data provided.")
    if not forwarded_bytes:
        raise ValueError("No forwarded notice image data provided.")

    api_key = _get_api_key()
    client = _create_genai_client(api_key)

    from google.genai import types as gtypes

    official_part = gtypes.Part.from_bytes(data=official_bytes, mime_type=official_mime or "image/png")
    forwarded_part = gtypes.Part.from_bytes(data=forwarded_bytes, mime_type=forwarded_mime or "image/png")

    prompt = (
        "You are TrustLens, a forensic document verification expert.\n\n"
        "I am providing TWO images:\n"
        "  IMAGE 1: The official, authentic baseline notice.\n"
        "  IMAGE 2: A forwarded notice that may have been tampered with.\n\n"
        "Compare them carefully for:\n"
        "- Any changed text (dates, fees, URLs, phone numbers, names, amounts)\n"
        "- Visual differences (layout, fonts, stamps, signatures, logos removed or added)\n"
        "- Any suspicious editing artifacts\n\n"
        "Output a valid JSON object with exactly these fields:\n"
        '- "verdict": One of "AUTHENTIC", "TAMPERED", "SUSPICIOUS", "UNVERIFIED"\n'
        '- "risk_level": One of "LOW", "MEDIUM", "HIGH"\n'
        '- "risk_score": Integer 0-100\n'
        '- "summary": 1-2 sentence professional assessment\n'
        '- "red_flags": Array of specific red flag strings (empty if none)\n'
        '- "evidence": Array of factual observations supporting your evaluation\n'
        '- "next_action": Concrete actionable recommendation\n'
        '- "changes": Array of human-readable strings describing each specific change detected '
        '(e.g., "Deadline changed from 15 October to 25 October"). Empty array if no changes found.\n\n'
        "IMPORTANT: Never claim 100% certain forgery. Report observable signals only.\n"
        "Compare IMAGE 1 (official) vs IMAGE 2 (forwarded):"
    )

    candidate_models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        max_attempts = 2 if model_name == PRIMARY_MODEL else 1
        for attempt in range(max_attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[official_part, forwarded_part, prompt],
                    config=gtypes.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                if response and response.text:
                    parsed = _parse_gemini_response(response.text)
                    # Also extract the non-standard "changes" field
                    try:
                        raw_text = response.text.strip()
                        if raw_text.startswith("```"):
                            lines = raw_text.splitlines()
                            raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
                        raw_json = json.loads(raw_text)
                        parsed["changes"] = [str(c).strip() for c in (raw_json.get("changes") or []) if c]
                    except Exception:
                        parsed["changes"] = []
                    return parsed
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                    raise RuntimeError(
                        f"Authentication failed: {_sanitize_error_message(e, api_key)}"
                    ) from None
                if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str) and attempt + 1 < max_attempts:
                    time.sleep(1.5)
                    continue
                break

    sanitized_err = _sanitize_error_message(last_error or Exception("No response"), api_key)
    raise RuntimeError(f"Gemini image comparison failed: {sanitized_err}") from None


def _get_local_image_signals(image_bytes: bytes) -> List[str]:
    """Extracts supporting local metadata signals from image bytes using Pillow."""
    signals = []
    try:
        import io
        from PIL import Image
        with Image.open(io.BytesIO(image_bytes)) as img:
            signals.append(f"Image properties: {img.format} format, {img.width}x{img.height} px, {img.mode} mode")
            # Check EXIF
            exif_data = img.getexif() if hasattr(img, "getexif") else None
            if exif_data and len(exif_data) > 0:
                signals.append(f"Metadata header present ({len(exif_data)} EXIF tag(s) detected)")
            else:
                signals.append("No camera EXIF metadata detected (typical for screenshots or web-compressed images)")
    except Exception:
        pass
    return signals


def assess_image_authenticity(image_bytes: bytes, mime_type: str = "image/png") -> Dict[str, Any]:
    """
    Assesses whether an image is likely original, manipulated, or AI-generated.
    Combines local image property checks with Gemini Vision forensic assessment.

    Returns:
        dict: {
            "assessment": "LIKELY_ORIGINAL" | "LIKELY_MANIPULATED" | "LIKELY_AI_GENERATED" | "UNCERTAIN",
            "confidence": int (0-100),
            "signals": list[str],
            "limitations": list[str],
        }
    """
    if not image_bytes:
        raise ValueError("No image data provided for authenticity assessment.")

    local_signals = _get_local_image_signals(image_bytes)

    api_key = _get_api_key()
    client = _create_genai_client(api_key)

    from google.genai import types as gtypes

    image_part = gtypes.Part.from_bytes(data=image_bytes, mime_type=mime_type or "image/png")
    prompt = (
        "You are TrustLens, a forensic image analysis expert.\n\n"
        "Assess the authenticity of this document, notice, or screenshot image.\n"
        "Carefully inspect for:\n"
        "- Inconsistent fonts, kerning, unnatural text blending, or mismatch in font families\n"
        "- JPEG recompression artifacts or boxy pixelation around specific text areas\n"
        "- Misaligned or distorted institutional elements (stamps, signatures, seals, logos)\n"
        "- AI-generation artifacts (unnatural layout symmetry, synthetic font shapes)\n"
        "- Any signs of copy-pasted or digitally overwritten text\n\n"
        "Output a valid JSON object with exactly these fields:\n"
        '- "assessment": Exactly one of "LIKELY_ORIGINAL", "LIKELY_MANIPULATED", "LIKELY_AI_GENERATED", "UNCERTAIN"\n'
        '- "confidence": An integer from 0 to 100 representing confidence in this assessment\n'
        '- "signals": Array of specific observable signals you noticed (strings)\n'
        '- "limitations": Array of limitation statements (honest caveats about what cannot be confirmed)\n\n'
        "STRICT RULES:\n"
        "- Never claim 100% certainty or prove forgery conclusively from an image alone.\n"
        "- If nothing suspicious is observed, return LIKELY_ORIGINAL with appropriate confidence.\n"
        "- Limitations MUST include: 'Visual analysis alone cannot conclusively confirm manipulation without raw camera/source files.'\n"
    )

    VALID_ASSESSMENTS = {"LIKELY_ORIGINAL", "LIKELY_MANIPULATED", "LIKELY_AI_GENERATED", "UNCERTAIN"}
    candidate_models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        max_attempts = 2 if model_name == PRIMARY_MODEL else 1
        for attempt in range(max_attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=[image_part, prompt],
                    config=gtypes.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.15,
                    ),
                )
                if response and response.text:
                    text = response.text.strip()
                    if text.startswith("```"):
                        lines = text.splitlines()
                        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
                    data = json.loads(text)
                    assessment = str(data.get("assessment", "UNCERTAIN")).upper().strip()
                    if assessment not in VALID_ASSESSMENTS:
                        assessment = "UNCERTAIN"

                    # Convert confidence to integer 0-100
                    raw_conf = data.get("confidence", 70)
                    try:
                        confidence = int(raw_conf)
                        confidence = max(0, min(100, confidence))
                    except (ValueError, TypeError):
                        confidence = 85 if str(raw_conf).upper() == "HIGH" else 65 if str(raw_conf).upper() == "MEDIUM" else 45

                    gemini_signals = [str(s).strip() for s in (data.get("signals") or []) if s]
                    all_signals = local_signals + [s for s in gemini_signals if s not in local_signals]

                    limitations = [str(l).strip() for l in (data.get("limitations") or []) if l]
                    if not limitations:
                        limitations = [
                            "Visual inspection alone cannot conclusively confirm manipulation without cryptographically signed source documents."
                        ]

                    return {
                        "assessment": assessment,
                        "confidence": confidence,
                        "signals": all_signals,
                        "limitations": limitations,
                    }
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                    raise RuntimeError(
                        f"Authentication failed: {_sanitize_error_message(e, api_key)}"
                    ) from None
                if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str) and attempt + 1 < max_attempts:
                    time.sleep(1.5)
                    continue
                break

    sanitized_err = _sanitize_error_message(last_error or Exception("No response"), api_key)
    raise RuntimeError(f"Image authenticity assessment failed: {sanitized_err}") from None


# ── PROTECT: Identity-attack local keyword pre-screening ─────────────────────
_PROTECT_KEYWORDS: Dict[str, List[str]] = {
    "OTP Phishing": ["otp", "one-time password", "one time password", "verification code", "6-digit", "4-digit", "enter your code", "share your code"],
    "SIM-Swap Social Engineering": ["sim swap", "sim card", "mobile number port", "port number", "mnp", "number transfer", "sim replacement", "e-sim", "esim qr"],
    "KYC Fraud": ["kyc", "know your customer", "aadhar", "aadhaar", "pan card", "id verification", "identity verification", "update your kyc"],
    "Credential Theft": ["password", "login credentials", "sign in to confirm", "enter password", "reset your security credentials"],
    "Impersonation": ["bank official", "rbi", "reserve bank", "police officer", "income tax", "it department", "cyber crime cell", "customer executive"],
    "Account Takeover": ["account blocked", "account suspended", "unusual activity", "immediately call", "call now", "access restricted"],
    "Financial Scam": ["lottery", "prize money", "won", "claim your reward", "cashback offer", "refund pending", "transfer amount"],
}

_PROTECT_PROMPT = (
    "You are TrustLens PROTECT, an expert identity and digital social engineering defense system.\n\n"
    "Analyze the following content specifically for identity and account security threats:\n"
    "- Impersonation of officials, institutions, banks, or telecom providers\n"
    "- OTP phishing and verification code theft\n"
    "- SIM-swap social engineering and unauthorized number porting requests\n"
    "- Fake KYC update and identity document collection scams\n"
    "- Account takeover attempts and urgent credential harvesting\n"
    "- Credential theft techniques\n\n"
    "Output a valid JSON object with exactly these fields:\n"
    '- "risk_level": Exactly one of "LOW", "MEDIUM", "HIGH"\n'
    '- "attack_type": Array of specific attack types identified (e.g. ["OTP Phishing", "SIM-Swap Social Engineering"]). Empty array [] if normal/benign.\n'
    '- "signals": Array of specific observable signals found in the content (strings)\n'
    '- "recommended_actions": Array of concrete protective actions the user should take\n'
    '- "limitations": Array of caveats (e.g. "TrustLens reports observable risk signals only. It cannot confirm telecom-level SIM swaps without carrier data.")\n\n'
    "STRICT RULES:\n"
    "- Do NOT invent attacks for normal, safe messages. If message is benign, return risk_level: 'LOW', attack_type: [], signals: [], recommended_actions: [].\n"
    "- Do NOT claim a real SIM swap has definitely occurred — report: 'SIM-swap risk signals detected' or 'Possible SIM-swap social engineering'.\n"
    "- Only include attack types directly supported by evidence in the content.\n\n"
    "Content to analyze:\n"
    '"""\n{content}\n"""'
)


def analyze_protect(content: str) -> Dict[str, Any]:
    """
    Analyzes content for identity-attack risk signals (PROTECT capability).
    Combines local keyword pre-screening with Gemini reasoning.

    Returns standardized structure:
        {
            "identity_protection": {
                "risk_level": "LOW" | "MEDIUM" | "HIGH",
                "attack_type": list[str],
                "signals": list[str],
                "recommended_actions": list[str],
                "limitations": list[str],
            },
            # Top-level mirrors for backward compatibility:
            "risk_level": ...,
            "identity_attack_risk": ...,
            "attack_type": ...,
            "possible_attack": ...,
            "signals": ...,
            "recommended_actions": ...,
            "actions": ...,
            "limitations": ...,
        }
    """
    default_limitations = [
        "TrustLens reports observable risk signals and social engineering patterns only.",
        "It cannot directly confirm telecom-level SIM swaps or carrier status without access to mobile operator network data."
    ]

    if not content or not content.strip():
        base = {
            "risk_level": "LOW",
            "attack_type": [],
            "signals": [],
            "recommended_actions": [],
            "limitations": default_limitations,
        }
        return {
            "identity_protection": base,
            "identity_attack_risk": "LOW",
            "risk_level": "LOW",
            "attack_type": [],
            "possible_attack": "NONE",
            "signals": [],
            "actions": [],
            "recommended_actions": [],
            "limitations": default_limitations,
        }

    # Local pre-screening for identity keywords
    content_lower = content.lower()
    local_signals: List[str] = []
    local_attack_types: List[str] = []
    for attack_type, keywords in _PROTECT_KEYWORDS.items():
        hits = [kw for kw in keywords if kw in content_lower]
        if hits:
            local_attack_types.append(attack_type)
            local_signals.append(f"{attack_type} indicator(s): {', '.join(hits[:3])}")

    try:
        api_key = _get_api_key()
        client = _create_genai_client(api_key)

        from google.genai import types as gtypes

        prompt = _PROTECT_PROMPT.format(content=content.strip())
        VALID_RISKS = {"LOW", "MEDIUM", "HIGH"}
        candidate_models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
        last_error: Optional[Exception] = None

        for model_name in candidate_models:
            max_attempts = 2 if model_name == PRIMARY_MODEL else 1
            for attempt in range(max_attempts):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=gtypes.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.2,
                        ),
                    )
                    if response and response.text:
                        text = response.text.strip()
                        if text.startswith("```"):
                            lines = text.splitlines()
                            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:]).strip()
                        data = json.loads(text)

                        risk = str(data.get("risk_level") or data.get("identity_attack_risk") or "LOW").upper().strip()
                        if risk not in VALID_RISKS:
                            risk = "MEDIUM" if local_signals else "LOW"

                        # Extract attack_type list
                        raw_attacks = data.get("attack_type") or data.get("possible_attack") or []
                        if isinstance(raw_attacks, list):
                            attack_types = [str(a).strip() for a in raw_attacks if a and str(a).upper() not in ("NONE", "UNKNOWN")]
                        elif isinstance(raw_attacks, str) and raw_attacks.upper() not in ("NONE", "UNKNOWN"):
                            attack_types = [raw_attacks.strip()]
                        else:
                            attack_types = []

                        # Merge local attack types if high certainty
                        for lat in local_attack_types:
                            if lat not in attack_types and risk != "LOW":
                                attack_types.append(lat)

                        gemini_signals = [str(s).strip() for s in (data.get("signals") or []) if s]
                        combined_signals = []
                        for ls in local_signals:
                            if ls not in combined_signals:
                                combined_signals.append(ls)
                        for gs in gemini_signals:
                            if gs not in combined_signals:
                                combined_signals.append(gs)

                        actions = [str(a).strip() for a in (data.get("recommended_actions") or data.get("actions") or []) if a]
                        if not actions and risk != "LOW":
                            actions = [
                                "Do not share OTPs, passwords, or SIM replacement codes.",
                                "Verify sender authenticity via official published institutional channels."
                            ]

                        limitations = [str(l).strip() for l in (data.get("limitations") or []) if l]
                        if not limitations:
                            limitations = default_limitations

                        protect_dict = {
                            "risk_level": risk,
                            "attack_type": attack_types,
                            "signals": combined_signals,
                            "recommended_actions": actions,
                            "limitations": limitations,
                        }

                        return {
                            "identity_protection": protect_dict,
                            "identity_attack_risk": risk,
                            "risk_level": risk,
                            "attack_type": attack_types,
                            "possible_attack": attack_types[0] if attack_types else "NONE",
                            "signals": combined_signals,
                            "actions": actions,
                            "recommended_actions": actions,
                            "limitations": limitations,
                        }
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                        raise RuntimeError(
                            f"Authentication failed: {_sanitize_error_message(e, api_key)}"
                        ) from None
                    if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str) and attempt + 1 < max_attempts:
                        time.sleep(1.5)
                        continue
                    break

    except (EnvironmentError, RuntimeError):
        pass  # Graceful fallback to local heuristics

    # Local fallback
    risk = "MEDIUM" if local_signals else "LOW"
    actions = [
        "Do not share verification codes or personal credentials.",
        "Contact your institution or mobile operator through official verified numbers."
    ] if local_signals else []

    fallback_dict = {
        "risk_level": risk,
        "attack_type": local_attack_types,
        "signals": local_signals,
        "recommended_actions": actions,
        "limitations": default_limitations,
    }

    return {
        "identity_protection": fallback_dict,
        "identity_attack_risk": risk,
        "risk_level": risk,
        "attack_type": local_attack_types,
        "possible_attack": local_attack_types[0] if local_attack_types else "NONE",
        "signals": local_signals,
        "actions": actions,
        "recommended_actions": actions,
        "limitations": default_limitations,
    }


# ==============================================================================
# Email Screenshot Forensics & Verification
# ==============================================================================
EMAIL_ANALYSIS_PROMPT = """You are TrustLens, an expert digital forensics and email security analyst.

Analyze this email screenshot or email text to determine whether it appears legitimate, suspicious, phishing-related, impersonated, or potentially manipulated.

Thoroughly evaluate:
1. SENDER INFORMATION:
   - Displayed sender name vs actual sender email address
   - Domain mismatches (e.g. claims to be a bank, university, or tech company but sender domain is unrelated)
   - Lookalike / typosquatted / spoofed domains
2. EMAIL CONTENT & DEMANDS:
   - False urgency ("within 24 hours", "immediate action required", "account suspension")
   - Threats of penalty, legal action, or service cutoff
   - Requests for passwords, OTP verification codes, KYC documents, credit card details, or banking credentials
   - Unsolicited payment or transfer requests
   - Suspicious instructions or attachment references
3. LINKS & DESTINATIONS:
   - Extract ALL visible or clickable URLs in the email
   - Detect shortened URLs, misleading link text, IP hosts, or suspicious top-level domains
4. VISUAL SIGNALS (if image provided):
   - Fake branding, logo distortion, low-resolution badges
   - Formatting inconsistencies, awkward spacing, unusual typography
   - Fake security warning banners or seals
5. IDENTITY & IMPERSONATION:
   - Determine if the email claims to represent an organization (bank, university, college, company, government, delivery service, social platform, recruiter)
   - Do NOT claim an organization is being impersonated unless the evidence clearly supports that conclusion.

IMPORTANT GUIDELINES:
- Do NOT claim 100% certainty (do NOT say "100% fake" or "guaranteed phishing"). Use explainable risk terms: "Likely Safe", "Low Risk", "Suspicious", "High Risk", "Likely Malicious", "Uncertain".
- Only include red flags and evidence items that are actually detected. Do not output empty placeholders.

Output a valid JSON object with the following schema:
{
  "verdict": Exactly one of "SAFE", "SUSPICIOUS", "MALICIOUS", "UNVERIFIED",
  "risk_level": Exactly one of "LOW", "MEDIUM", "HIGH",
  "risk_score": An integer from 0 (completely safe) to 100 (critical threat),
  "summary": A concise 1-2 sentence professional assessment of the email,
  "red_flags": A JSON array of specific red flag strings detected (empty array if none),
  "evidence": A JSON array of clear factual observations supporting your evaluation (empty array if none),
  "extracted_urls": A JSON array of any URL strings visible or referenced in the email (empty array if none),
  "sender_info": {
     "displayed_sender": "string or null",
     "sender_address": "string or null",
     "claimed_organization": "string or null",
     "domain_mismatch": boolean
  },
  "next_action": A concrete, actionable recommendation for the user
}
"""


def analyze_email_with_gemini(
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png",
    email_text: Optional[str] = None,
    language: str = "English",
) -> Dict[str, Any]:
    """
    Analyzes an email screenshot or email text using Gemini Vision / language reasoning.
    Inspects sender domain mismatch, urgent coercion, credential/OTP demands, links,
    and visual impersonation signals.

    Args:
        image_bytes: Raw bytes of the email screenshot (optional if email_text provided).
        mime_type: Image MIME type.
        email_text: Plain text of the email (optional if image_bytes provided).
        language: Language for the analysis report (English, Kannada, Hindi, Hinglish).

    Returns:
        dict: Standardized email evaluation report.
    """
    if not image_bytes and (not email_text or not email_text.strip()):
        raise ValueError("Either an email screenshot or email text must be provided.")

    try:
        api_key = _get_api_key()
        client = _create_genai_client(api_key)
    except EnvironmentError as e:
        # Fallback heuristic if API key is unconfigured
        return {
            "verdict": "UNVERIFIED",
            "risk_level": "LOW",
            "risk_score": 25,
            "summary": "Email received. Gemini API key is not configured for automated deep forensics.",
            "red_flags": [],
            "evidence": ["Automated API verification is offline."],
            "extracted_urls": [],
            "sender_info": {"displayed_sender": None, "sender_address": None, "claimed_organization": None, "domain_mismatch": False},
            "next_action": "Check the sender email address directly and verify links manually.",
        }

    from google.genai import types

    contents: list = []
    if image_bytes:
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type or "image/png")
        contents.append(image_part)

    prompt_content = EMAIL_ANALYSIS_PROMPT
    if email_text:
        prompt_content += f'\n\nEmail Text:\n"""\n{email_text.strip()}\n"""'
    if language and language.strip().lower() != "english":
        lang_str = language.strip()
        prompt_content += (
            f"\n\nIMPORTANT LANGUAGE REQUIREMENT:\n"
            f"Please respond and write 'summary', 'red_flags', 'evidence', and 'next_action' in {lang_str}.\n"
            f"Keep the JSON keys and English values for 'verdict' and 'risk_level' strictly in English."
        )
    contents.append(prompt_content)

    config = types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json",
    )

    candidate_models = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]
    last_error: Optional[Exception] = None

    for model_name in candidate_models:
        max_attempts = 2 if model_name == PRIMARY_MODEL else 1
        for attempt in range(max_attempts):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                if response and response.text:
                    parsed = _parse_gemini_response(response.text)
                    if isinstance(parsed, dict) and "verdict" in parsed:
                        return parsed
            except Exception as e:
                last_error = e
                err_str = str(e)
                if "401" in err_str or "403" in err_str or "API_KEY_INVALID" in err_str:
                    clean_msg = _sanitize_error_message(e, api_key)
                    raise RuntimeError(f"Authentication failed with Gemini API: {clean_msg}") from None
                if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str) and attempt + 1 < max_attempts:
                    time.sleep(1.5)
                    continue
                break

    sanitized_err = _sanitize_error_message(last_error or Exception("No response received"), api_key)
    raise RuntimeError(f"Gemini email analysis service unavailable: {sanitized_err}") from None

