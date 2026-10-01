"""
Analyzer entry point for TrustLens.
Aggregates the verification modules to return standardized Trust Reports.
"""
from typing import Dict, Any, Optional
from .url_checker import check_url
from .notice_compare import compare_notices
from .fingerprint import generate_fingerprint
from .database import (
    save_analysis,
    get_analysis,
    increment_analysis_count,
    get_community_memory,
    initialize_database,
    find_matching_notice,
    get_all_official_notices,
    save_official_notice,
    save_verification_report,
    get_verification_report,
)
from .gemini_service import (
    analyze_with_gemini,
    extract_text_from_image,
    analyze_notice_images,
    assess_image_authenticity,
    analyze_protect as _gemini_analyze_protect,
    analyze_email_with_gemini,
)
from .qr_receipt import generate_verification_id

# Ensure database tables and demo seed records are initialized
initialize_database()


def _build_standard_report(
    verdict: str,
    risk_level: str,
    risk_score: int,
    summary: str,
    red_flags: list,
    evidence: list,
    next_action: str
) -> Dict[str, Any]:
    return {
        "verdict": verdict,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "summary": summary,
        "red_flags": red_flags,
        "evidence": evidence,
        "next_action": next_action
    }


def analyze_text(content: str, language: str = "English") -> Dict[str, Any]:
    """
    Analyzes arbitrary text content using Gemini.
    Also executes identity attack security evaluation (PROTECT capability).
    Stores and retrieves from the database using a fingerprint to avoid re-analysis.
    """
    if not content or not content.strip():
        rep = _build_standard_report(
            verdict="UNKNOWN",
            risk_level="LOW",
            risk_score=0,
            summary="No content provided for analysis.",
            red_flags=[],
            evidence=[],
            next_action="Provide message or text content to verify."
        )
        rep["verification_id"] = generate_verification_id()
        return rep

    fp = generate_fingerprint(content)
    existing = get_analysis(fp)
    if existing and 'verdict' in existing:
        new_count = increment_analysis_count(fp)
        existing["community_memory"] = {
            "previously_checked": True,
            "count": new_count,
            "first_seen": existing.get("stored_at") or existing.get("timestamp"),
            "previous_verdict": existing.get("verdict"),
            "previous_risk_level": existing.get("risk_level"),
        }
        if not language or language.strip().lower() == "english":
            return existing

    # Analyze via Gemini
    gemini_result = analyze_with_gemini(content, language=language)

    report = _build_standard_report(
        verdict=gemini_result.get("verdict", "UNKNOWN"),
        risk_level=gemini_result.get("risk_level", "LOW"),
        risk_score=gemini_result.get("risk_score", 80 if gemini_result.get("risk_level") == "HIGH" else 20),
        summary=gemini_result.get("summary", "Analysis complete."),
        red_flags=gemini_result.get("red_flags", []),
        evidence=gemini_result.get("evidence", []),
        next_action=gemini_result.get("next_action", "Proceed with caution.")
    )

    # Attach PROTECT identity-security analysis
    try:
        protect_res = _gemini_analyze_protect(content)
        report["identity_protection"] = protect_res.get("identity_protection", protect_res)
        report["protect"] = protect_res
    except Exception:
        pass

    vid = generate_verification_id()
    report["verification_id"] = vid

    # Check if this item had previous community memory
    comm_mem = get_community_memory(fp)
    if comm_mem:
        report["community_memory"] = comm_mem

    save_analysis(fp, report)
    save_verification_report(vid, report, fingerprint=fp)
    return report


def analyze_url(url: str, language: str = "English") -> Dict[str, Any]:
    """
    Analyzes a URL using local heuristics.
    """
    if not url or not url.strip():
        rep = _build_standard_report(
            verdict="UNKNOWN",
            risk_level="LOW",
            risk_score=0,
            summary="No URL provided for analysis.",
            red_flags=[],
            evidence=[],
            next_action="Provide a valid URL to verify."
        )
        rep["verification_id"] = generate_verification_id()
        return rep

    fp = generate_fingerprint(url)
    existing = get_analysis(fp)
    if existing and 'verdict' in existing:
        new_count = increment_analysis_count(fp)
        existing["community_memory"] = {
            "previously_checked": True,
            "count": new_count,
            "first_seen": existing.get("stored_at") or existing.get("timestamp"),
            "previous_verdict": existing.get("verdict"),
            "previous_risk_level": existing.get("risk_level"),
        }
        return existing

    url_res = check_url(url)
    risk_level = url_res.get("risk_level", "LOW")
    risk_score = url_res.get("risk_score", 0)

    verdict = "SUSPICIOUS" if risk_score >= 30 else "SAFE"
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

    vid = generate_verification_id()
    report["verification_id"] = vid

    comm_mem = get_community_memory(fp)
    if comm_mem:
        report["community_memory"] = comm_mem

    save_analysis(fp, report)
    save_verification_report(vid, report, fingerprint=fp)
    return report


def analyze_notice(
    content: Optional[str] = None,
    second_arg: Optional[str] = None,
    original_text: Optional[str] = None,
    modified_text: Optional[str] = None,
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png",
    official_image_bytes: Optional[bytes] = None,
    official_image_mime: str = "image/png",
) -> Dict[str, Any]:
    """
    Analyzes a forwarded notice against verified source-of-truth notices.

    Supports:
    1. Single forwarded text: auto-matches official notice from repository.
    2. Single forwarded image: Gemini Vision OCR -> auto-match -> text diff.
       Also runs image authenticity assessment.
    3. Two images (official + forwarded): Gemini Vision image-to-image comparison.
    4. Dual text (original_text, modified_text): explicit baseline comparison.

    Returns:
        dict: Standardized Trust Report with verdict, risk, evidence, changes,
              and optionally image_authenticity.
    """
    forwarded_content: Optional[str] = None
    manual_original: Optional[str] = None
    image_authenticity: Optional[Dict[str, Any]] = None

    # ── 1. Resolve inputs ────────────────────────────────────────────────────

    # CASE A: Two images → image-to-image Gemini Vision comparison
    if official_image_bytes and image_bytes:
        try:
            gemini_img_res = analyze_notice_images(
                official_bytes=official_image_bytes,
                forwarded_bytes=image_bytes,
                official_mime=official_image_mime,
                forwarded_mime=mime_type,
            )
        except Exception as e:
            return _build_standard_report(
                verdict="UNKNOWN",
                risk_level="MEDIUM",
                risk_score=50,
                summary="Image comparison could not be completed.",
                red_flags=["Image analysis service temporarily unavailable."],
                evidence=[str(e)],
                next_action="Try again or paste the notice text manually for verification.",
            )

        # Also assess authenticity of the forwarded image
        try:
            image_authenticity = assess_image_authenticity(image_bytes, mime_type)
        except Exception:
            image_authenticity = None

        changes_raw = gemini_img_res.get("changes", [])
        # Convert Gemini image changes into what_changed format
        what_changed = [{"item": "Visual/Text Change", "original": "", "forwarded": c, "highlight": c}
                        for c in changes_raw]

        report = _build_standard_report(
            verdict=gemini_img_res.get("verdict", "SUSPICIOUS"),
            risk_level=gemini_img_res.get("risk_level", "MEDIUM"),
            risk_score=gemini_img_res.get("risk_score", 50),
            summary=gemini_img_res.get("summary", "Image comparison completed."),
            red_flags=gemini_img_res.get("red_flags", []),
            evidence=gemini_img_res.get("evidence", []),
            next_action=gemini_img_res.get("next_action", "Review detected discrepancies carefully."),
        )
        report["changes"] = what_changed
        report["matched_source"] = "Official notice image (uploaded)"
        report["verification_id"] = None
        report["extracted_text"] = None
        report["has_matching_original"] = True
        if image_authenticity:
            report["image_authenticity"] = image_authenticity
        return report

    # CASE B: Single forwarded image → OCR then auto-match (+ authenticity)
    if image_bytes:
        try:
            forwarded_content = extract_text_from_image(image_bytes, mime_type)
        except Exception as e:
            return _build_standard_report(
                verdict="UNKNOWN",
                risk_level="LOW",
                risk_score=0,
                summary="Could not extract text from the uploaded image.",
                red_flags=["Image text extraction failed."],
                evidence=[str(e)],
                next_action="Try a clearer image or paste the notice text directly.",
            )
        # Assess authenticity of the forwarded image
        try:
            image_authenticity = assess_image_authenticity(image_bytes, mime_type)
        except Exception:
            image_authenticity = None

        if content:
            manual_original = content
        elif original_text:
            manual_original = original_text

    elif second_arg is not None:
        # Called as analyze_notice(original_text, modified_text)
        manual_original = content
        forwarded_content = second_arg
    elif modified_text is not None:
        forwarded_content = modified_text
        manual_original = original_text
    else:
        # Single text input (forwarded notice)
        forwarded_content = content
        manual_original = original_text

    if not forwarded_content or not forwarded_content.strip():
        return _build_standard_report(
            verdict="UNKNOWN",
            risk_level="LOW",
            risk_score=0,
            summary="No notice content provided for verification.",
            red_flags=[],
            evidence=[],
            next_action="Upload a notice screenshot or paste text to verify.",
        )

    # ── 2. Check fingerprint cache ────────────────────────────────────────────
    cache_key = f"NOTICE:{forwarded_content.strip()}"
    if manual_original:
        cache_key += f":ORIG:{manual_original.strip()}"
    fp = generate_fingerprint(cache_key)

    existing = get_analysis(fp)
    if existing and "verdict" in existing:
        new_count = increment_analysis_count(fp)
        existing["community_memory"] = {
            "previously_checked": True,
            "count": new_count,
            "first_seen": existing.get("stored_at") or existing.get("timestamp"),
            "previous_verdict": existing.get("verdict"),
            "previous_risk_level": existing.get("risk_level"),
        }
        # Inject live authenticity result on cache hits (may be stale otherwise)
        if image_authenticity and "image_authenticity" not in existing:
            existing["image_authenticity"] = image_authenticity
        return existing

    # ── 3. Locate baseline source ─────────────────────────────────────────────
    matched_notice: Optional[Dict[str, Any]] = None

    if manual_original and manual_original.strip():
        matched_notice = {
            "id": "CUSTOM-BASELINE",
            "title": "Provided Baseline Notice",
            "content": manual_original.strip(),
            "match_score": 1.0,
        }
    else:
        matched_notice = find_matching_notice(forwarded_content)

    # ── 4. Generate comparison or standalone assessment ───────────────────────
    if matched_notice:
        baseline_text = matched_notice["content"]
        notice_res = compare_notices(baseline_text, forwarded_content)
        changes = notice_res.get("changes", [])

        # If matched official notice has an image and the forwarded notice was uploaded as an image,
        # perform side-by-side Gemini Vision image comparison for deep visual signal analysis
        if image_bytes and matched_notice.get("image_blob"):
            try:
                img_cmp = analyze_notice_images(
                    official_bytes=matched_notice["image_blob"],
                    forwarded_bytes=image_bytes,
                    official_mime=matched_notice.get("image_mime") or "image/png",
                    forwarded_mime=mime_type,
                )
                # Merge visual comparison evidence
                for ev in img_cmp.get("evidence", []):
                    if ev not in notice_res.get("evidence", []):
                        notice_res.setdefault("evidence", []).append(f"Visual check: {ev}")
                for rf in img_cmp.get("red_flags", []):
                    if rf not in notice_res.get("red_flags", []):
                        notice_res.setdefault("red_flags", []).append(rf)
            except Exception:
                pass

        if changes:
            verdict = "TAMPERED"
            risk_level = notice_res.get("risk_level", "HIGH")
            risk_score = notice_res.get("risk_score", 85)
            red_flags = [c.get("label", "Content modified") for c in changes]
            evidence = [
                f"Matched official record: {matched_notice['title']} (Ref: {matched_notice.get('id', 'N/A')}).",
                f"Detected {len(changes)} unauthorized modification(s) compared to the authentic notice.",
            ] + [f"Discrepancy: {c.get('label')}" for c in changes]
            next_action = (
                "Do not rely on or forward this altered notice. "
                "Verify all dates and instructions exclusively through the official institutional portal."
            )
        else:
            verdict = "AUTHENTIC"
            risk_level = "LOW"
            risk_score = 0
            red_flags = []
            evidence = [
                f"Matched official record: {matched_notice['title']} (Ref: {matched_notice.get('id', 'N/A')}).",
                "Text matches the verified baseline circular exactly with zero discrepancies.",
            ]
            next_action = "This notice matches the official baseline circular and is authentic."

        report = _build_standard_report(
            verdict=verdict,
            risk_level=risk_level,
            risk_score=risk_score,
            summary=notice_res.get("summary", "Notice verification completed."),
            red_flags=red_flags,
            evidence=evidence,
            next_action=next_action,
        )
        report["changes"] = changes
        report["matched_source"] = matched_notice["title"]
        report["verification_id"] = matched_notice.get("id") or generate_verification_id()
        report["extracted_text"] = forwarded_content
        report["has_matching_original"] = True

    else:
        # No matching source — standalone Gemini heuristic assessment
        gemini_res = analyze_with_gemini(forwarded_content)

        verdict = "UNVERIFIED" if gemini_res.get("verdict") == "SAFE" else gemini_res.get("verdict", "SUSPICIOUS")
        risk_level = gemini_res.get("risk_level", "MEDIUM")
        risk_score = max(55, gemini_res.get("risk_score", 55))

        summary = (
            "No verified original notice was found in the TrustLens repository for comparison. "
            "A standalone heuristic review was conducted."
        )
        red_flags = [
            "No verified original notice was found in institutional database"
        ] + gemini_res.get("red_flags", [])

        evidence = [
            "No verified original notice was found in the institutional repository.",
            "Standalone content assessment conducted using TrustLens verification model.",
        ] + gemini_res.get("evidence", [])

        next_action = (
            "Contact the issuing institution directly through official published channels "
            "to request a verified copy before taking action."
        )

        report = _build_standard_report(
            verdict=verdict,
            risk_level=risk_level,
            risk_score=risk_score,
            summary=summary,
            red_flags=red_flags,
            evidence=evidence,
            next_action=next_action,
        )
        report["changes"] = []
        report["matched_source"] = None
        report["verification_id"] = generate_verification_id()
        report["extracted_text"] = forwarded_content
        report["has_matching_original"] = False

    if image_authenticity:
        report["image_authenticity"] = image_authenticity

    vid = report.get("verification_id") or generate_verification_id()
    report["verification_id"] = vid

    save_analysis(fp, report)
    save_verification_report(vid, report, fingerprint=fp)
    return report


def analyze_protect(content: str) -> Dict[str, Any]:
    """
    Analyzes message/text content for identity-attack risk signals.

    Runs PROTECT: local keyword pre-screening + Gemini identity-safety reasoning.

    Returns:
        dict: Standardized identity_protection dictionary.
    """
    return _gemini_analyze_protect(content)


def analyze_email(
    image_bytes: Optional[bytes] = None,
    mime_type: str = "image/png",
    content: Optional[str] = None,
    language: str = "English",
) -> Dict[str, Any]:
    """
    Analyzes an email screenshot or email text for phishing, spoofing, impersonation,
    malicious links, and credential threats.

    Combines:
    1. Gemini Vision / forensics on the email screenshot and text.
    2. Image Authenticity assessment (if image provided).
    3. Extracted URL analysis via existing check_url heuristics.
    4. Identity attack detection via analyze_protect (PROTECT).

    Returns:
        dict: Standardized Trust Report.
    """
    import re

    if not image_bytes and (not content or not content.strip()):
        rep = _build_standard_report(
            verdict="UNKNOWN",
            risk_level="LOW",
            risk_score=0,
            summary="No email screenshot or text provided for analysis.",
            red_flags=[],
            evidence=[],
            next_action="Upload an email screenshot or paste the email text to verify.",
        )
        rep["verification_id"] = generate_verification_id()
        return rep

    # Generate cache fingerprint
    fp_source = (content or "") + (f":img_{len(image_bytes)}" if image_bytes else "")
    fp = generate_fingerprint(fp_source)
    existing = get_analysis(fp)
    if existing and "verdict" in existing:
        new_count = increment_analysis_count(fp)
        existing["community_memory"] = {
            "previously_checked": True,
            "count": new_count,
            "first_seen": existing.get("stored_at") or existing.get("timestamp"),
            "previous_verdict": existing.get("verdict"),
            "previous_risk_level": existing.get("risk_level"),
        }
        if not language or language.strip().lower() == "english":
            return existing

    # 1. Assess image authenticity if image provided
    image_authenticity = None
    if image_bytes:
        try:
            image_authenticity = assess_image_authenticity(image_bytes, mime_type)
        except Exception:
            image_authenticity = None

    # 2. Analyze email with Gemini
    gemini_res = analyze_email_with_gemini(
        image_bytes=image_bytes,
        mime_type=mime_type,
        email_text=content,
        language=language,
    )

    verdict = gemini_res.get("verdict", "SUSPICIOUS")
    risk_level = gemini_res.get("risk_level", "MEDIUM")
    risk_score = gemini_res.get("risk_score", 50)
    summary = gemini_res.get("summary", "Email analysis completed.")
    red_flags = list(gemini_res.get("red_flags", []))
    evidence = list(gemini_res.get("evidence", []))
    next_action = gemini_res.get("next_action", "Exercise caution before clicking links or replying.")

    # Format sender information into evidence if present
    sender_info = gemini_res.get("sender_info")
    if isinstance(sender_info, dict):
        disp = sender_info.get("displayed_sender")
        addr = sender_info.get("sender_address")
        org = sender_info.get("claimed_organization")
        mismatch = sender_info.get("domain_mismatch", False)
        if addr:
            evidence.append(f"Sender address: {addr}")
        if org:
            evidence.append(f"Claimed organization: {org}")
        if mismatch:
            evidence.append("Sender domain does not match the claimed organization.")

    # 3. Extract and verify any URLs found via existing check_url
    extracted_urls = list(gemini_res.get("extracted_urls", []))
    if content:
        for u in re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', content):
            if u not in extracted_urls:
                extracted_urls.append(u)

    for url_str in extracted_urls:
        if isinstance(url_str, str) and url_str.strip():
            u_clean = url_str.strip()
            try:
                url_eval = check_url(u_clean)
                u_score = url_eval.get("risk_score", 0)
                u_level = url_eval.get("risk_level", "LOW")
                u_flags = url_eval.get("red_flags", [])
                u_ev = url_eval.get("evidence", [])

                if u_score > 0:
                    for f in u_flags:
                        flag_txt = f"URL ({u_clean}): {f}"
                        if flag_txt not in red_flags:
                            red_flags.append(flag_txt)
                    for e in u_ev:
                        ev_txt = f"URL signal ({u_clean}): {e}"
                        if ev_txt not in evidence:
                            evidence.append(ev_txt)

                    if u_score > risk_score:
                        risk_score = max(risk_score, u_score)
                    if u_level == "HIGH" or u_score >= 60:
                        risk_level = "HIGH"
                        verdict = "MALICIOUS" if verdict != "SAFE" else "SUSPICIOUS"
            except Exception:
                pass

    report = _build_standard_report(
        verdict=verdict,
        risk_level=risk_level,
        risk_score=risk_score,
        summary=summary,
        red_flags=red_flags,
        evidence=evidence,
        next_action=next_action,
    )

    if image_authenticity:
        report["image_authenticity"] = image_authenticity

    # 4. Integrate PROTECT if identity attack indicators exist
    combined_eval_text = (summary + " " + " ".join(red_flags) + " " + (content or "")).strip()
    try:
        protect_res = _gemini_analyze_protect(combined_eval_text)
        p_risk = protect_res.get("risk_level", "LOW")
        p_signals = protect_res.get("signals", [])
        if p_risk != "LOW" or p_signals:
            report["identity_protection"] = protect_res.get("identity_protection", protect_res)
            report["protect"] = protect_res
    except Exception:
        pass

    comm_mem = get_community_memory(fp)
    if comm_mem:
        report["community_memory"] = comm_mem

    vid = generate_verification_id()
    report["verification_id"] = vid

    save_analysis(fp, report)
    save_verification_report(vid, report, fingerprint=fp)
    return report


def analyze_image(
    image_bytes: bytes,
    mime_type: str = "image/png",
    language: str = "English",
) -> Dict[str, Any]:
    """
    Analyzes a general image or screenshot for visual manipulation, AI generation,
    suspicious edits, or authenticity signals.

    Does NOT attempt official notice matching — this is for general image verification.

    Combines:
    1. Gemini Vision authenticity assessment (assess_image_authenticity).
    2. Builds a Trust Report that surfaces visual signals clearly.

    Returns:
        dict: Standardized Trust Report with image_authenticity section.
    """
    if not image_bytes:
        rep = _build_standard_report(
            verdict="UNKNOWN",
            risk_level="LOW",
            risk_score=0,
            summary="No image provided for analysis.",
            red_flags=[],
            evidence=[],
            next_action="Upload an image or screenshot to verify.",
        )
        rep["verification_id"] = generate_verification_id()
        return rep

    # Generate cache fingerprint based on image size + first 256 bytes
    fp_source = f"image:{mime_type}:{len(image_bytes)}:{image_bytes[:256].hex()}"
    fp = generate_fingerprint(fp_source)
    existing = get_analysis(fp)
    if existing and "verdict" in existing:
        new_count = increment_analysis_count(fp)
        existing["community_memory"] = {
            "previously_checked": True,
            "count": new_count,
            "first_seen": existing.get("stored_at") or existing.get("timestamp"),
            "previous_verdict": existing.get("verdict"),
            "previous_risk_level": existing.get("risk_level"),
        }
        return existing

    # Run Gemini Vision authenticity check
    image_authenticity = None
    try:
        image_authenticity = assess_image_authenticity(image_bytes, mime_type)
    except Exception:
        image_authenticity = None

    # Map authenticity assessment to Trust Report fields
    if image_authenticity and isinstance(image_authenticity, dict):
        assessment = image_authenticity.get("assessment", "UNCERTAIN")
        confidence = image_authenticity.get("confidence", "LOW")
        signals = image_authenticity.get("signals", [])
        limitations = image_authenticity.get("limitations", [])

        if assessment == "LIKELY_MANIPULATED":
            verdict = "LIKELY MANIPULATED"
            risk_level = "HIGH"
            risk_score = 80
            summary = "Visual analysis indicates this image may have been manipulated or edited. Suspicious signals were observed."
        elif assessment == "LIKELY_AI_GENERATED":
            verdict = "LIKELY AI-GENERATED"
            risk_level = "MEDIUM"
            risk_score = 65
            summary = "Visual signals suggest this image may be AI-generated. Treat as unverified unless the original source is confirmed."
        elif assessment == "LIKELY_ORIGINAL":
            verdict = "LIKELY ORIGINAL"
            risk_level = "LOW"
            risk_score = 10
            summary = "No obvious visual manipulation or AI-generation indicators were found. The image appears consistent with an authentic photograph or document."
        else:
            verdict = "UNCERTAIN"
            risk_level = "LOW"
            risk_score = 20
            summary = "The visual analysis was inconclusive. No strong indicators of manipulation or AI-generation were detected, but certainty is limited."

        red_flags = [s for s in signals if s]
        evidence = [f"Confidence: {confidence}"]
        if limitations:
            for lim in limitations:
                evidence.append(f"Limitation: {lim}")

        note = (
            "TrustLens provides a probabilistic visual assessment only. "
            "This cannot definitively prove an image is AI-generated or manipulated."
        )
        evidence.append(note)

        if assessment == "LIKELY_MANIPULATED":
            next_action = "Treat this image with caution. Verify through the original source before sharing or acting on it."
        elif assessment == "LIKELY_AI_GENERATED":
            next_action = "This image shows signs consistent with AI generation. Cross-check with the claimed source before treating it as authentic."
        elif assessment == "LIKELY_ORIGINAL":
            next_action = "No obvious manipulation signals detected. If content still seems suspicious, verify the original context."
        else:
            next_action = "Assessment was inconclusive. Use additional judgment and verify the source context independently."

    else:
        verdict = "UNCERTAIN"
        risk_level = "LOW"
        risk_score = 0
        summary = "Image authenticity assessment could not be completed at this time."
        red_flags = []
        evidence = []
        next_action = "Try again or verify the image through its claimed source."
        image_authenticity = None

    report = _build_standard_report(
        verdict=verdict,
        risk_level=risk_level,
        risk_score=risk_score,
        summary=summary,
        red_flags=red_flags,
        evidence=evidence,
        next_action=next_action,
    )

    if image_authenticity:
        report["image_authenticity"] = image_authenticity

    comm_mem = get_community_memory(fp)
    if comm_mem:
        report["community_memory"] = comm_mem

    vid = generate_verification_id()
    report["verification_id"] = vid

    save_analysis(fp, report)
    save_verification_report(vid, report, fingerprint=fp)
    return report
