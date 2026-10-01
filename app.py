import datetime
import html
import io
import re
from typing import Any
import streamlit as st

from backend.analyzer import (
    analyze_text,
    analyze_url,
    analyze_notice,
    analyze_protect,
    analyze_email,
    analyze_image,
)
from backend.database import (
    save_official_notice,
    get_all_official_notices,
    save_verification_report,
    get_verification_report,
)
from backend.fingerprint import generate_fingerprint
from backend.gemini_service import extract_text_from_image
from backend.qr_receipt import generate_qr_receipt, generate_verification_id

# ==============================================================================
# Page Configuration & Visual Foundation
# ==============================================================================
st.set_page_config(
    page_title="TrustLens — Check Before You Believe",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Professional Cybersecurity Dark Theme: No fixed header overlap, disciplined hierarchy
st.markdown(
    """
    <style>
    /* Fix Streamlit Header Overlay: Hide default Streamlit fixed header so it never covers content */
    header[data-testid="stHeader"] {
        display: none !important;
        height: 0 !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    #MainMenu {
        visibility: hidden !important;
    }

    footer {
        visibility: hidden !important;
    }

    /* Global Base */
    .stApp {
        background-color: #0b0f17;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Screen Width Intentionality: ~1060px centered layout with ample top margin */
    .block-container {
        max-width: 1060px !important;
        width: 100% !important;
        padding-top: 1.75rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        margin: 0 auto !important;
        position: relative !important;
        box-sizing: border-box !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1.25rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
    }

    /* Top Navbar: in-flow static positioning (never covers content) */
    .tl-nav-brand-wrap {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        height: 100%;
        padding: 0.25rem 0;
        flex-wrap: wrap;
    }
    .tl-nav-brand {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .tl-nav-brand-title {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f8fafc;
    }
    .tl-nav-tagline {
        font-size: 0.82rem;
        font-weight: 500;
        color: #64748b;
        padding-left: 0.75rem;
        border-left: 1px solid #1e293b;
    }
    .tl-nav-status {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding-left: 0.75rem;
        border-left: 1px solid #1e293b;
        font-size: 0.76rem;
        color: #94a3b8;
    }
    .tl-status-dot {
        width: 7px;
        height: 7px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }

    /* Header Action Button: small, clean, unobtrusive */
    div.st-key-nav_btn_org_login > button,
    div.st-key-nav_btn_back_home > button,
    div.st-key-nav_btn_public > button,
    div.st-key-nav_btn_dash > button,
    div.st-key-nav_btn_logout > button {
        background-color: #121824 !important;
        border: 1px solid #1f293d !important;
        color: #94a3b8 !important;
        font-size: 0.84rem !important;
        font-weight: 500 !important;
        padding: 0.4rem 0.9rem !important;
        border-radius: 6px !important;
        transition: all 0.15s ease !important;
        margin-top: 0.1rem !important;
    }
    div.st-key-nav_btn_org_login > button:hover,
    div.st-key-nav_btn_back_home > button:hover,
    div.st-key-nav_btn_public > button:hover,
    div.st-key-nav_btn_dash > button:hover,
    div.st-key-nav_btn_logout > button:hover {
        background-color: #1e293b !important;
        border-color: #3b82f6 !important;
        color: #f8fafc !important;
    }

    /* Hero / Intro Section */
    .tl-hero-section {
        margin-top: 0.85rem;
        margin-bottom: 1.35rem;
        width: 100%;
    }
    .tl-hero-heading {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: #f8fafc;
        margin: 0 0 0.35rem 0;
        line-height: 1.2;
    }
    .tl-hero-subtext {
        font-size: 0.94rem;
        color: #94a3b8;
        margin: 0;
        max-width: 680px;
        line-height: 1.5;
    }

    /* Main Verification Workspace Container */
    .tl-workspace-card {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 8px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.35rem;
        width: 100%;
    }
    .tl-workspace-header {
        margin-bottom: 1.15rem;
    }
    .tl-workspace-title {
        font-size: 1.15rem;
        font-weight: 600;
        color: #f8fafc;
        letter-spacing: -0.01em;
        margin-bottom: 0.2rem;
    }
    .tl-workspace-desc {
        font-size: 0.86rem;
        color: #94a3b8;
    }

    /* Mode Selector Buttons Styling: 5 balanced cards */
    div.st-key-mode_msg button,
    div.st-key-mode_url button,
    div.st-key-mode_notice button,
    div.st-key-mode_image button,
    div.st-key-mode_email button {
        width: 100% !important;
        height: auto !important;
        min-height: 72px !important;
        padding: 0.85rem 1rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 6px !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-mode_msg button strong,
    div.st-key-mode_url button strong,
    div.st-key-mode_notice button strong,
    div.st-key-mode_image button strong,
    div.st-key-mode_email button strong {
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        display: block !important;
        margin-bottom: 0.15rem !important;
    }
    div.st-key-mode_msg button p,
    div.st-key-mode_url button p,
    div.st-key-mode_notice button p,
    div.st-key-mode_image button p,
    div.st-key-mode_email button p {
        font-size: 0.80rem !important;
        font-weight: 400 !important;
        margin: 0 !important;
        line-height: 1.35 !important;
    }

    /* Inactive Mode Cards */
    div.st-key-mode_msg button[kind="secondary"],
    div.st-key-mode_url button[kind="secondary"],
    div.st-key-mode_notice button[kind="secondary"],
    div.st-key-mode_image button[kind="secondary"],
    div.st-key-mode_email button[kind="secondary"] {
        background-color: #121824 !important;
        border: 1px solid #1f293d !important;
    }
    div.st-key-mode_msg button[kind="secondary"] strong,
    div.st-key-mode_url button[kind="secondary"] strong,
    div.st-key-mode_notice button[kind="secondary"] strong,
    div.st-key-mode_image button[kind="secondary"] strong,
    div.st-key-mode_email button[kind="secondary"] strong {
        color: #cbd5e1 !important;
    }
    div.st-key-mode_msg button[kind="secondary"] p,
    div.st-key-mode_url button[kind="secondary"] p,
    div.st-key-mode_notice button[kind="secondary"] p,
    div.st-key-mode_image button[kind="secondary"] p,
    div.st-key-mode_email button[kind="secondary"] p {
        color: #64748b !important;
    }
    div.st-key-mode_msg button[kind="secondary"]:hover,
    div.st-key-mode_url button[kind="secondary"]:hover,
    div.st-key-mode_notice button[kind="secondary"]:hover,
    div.st-key-mode_image button[kind="secondary"]:hover,
    div.st-key-mode_email button[kind="secondary"]:hover {
        background-color: #162030 !important;
        border-color: #2b3b55 !important;
    }

    /* Active Mode Cards */
    div.st-key-mode_msg button[kind="primary"],
    div.st-key-mode_url button[kind="primary"],
    div.st-key-mode_notice button[kind="primary"],
    div.st-key-mode_image button[kind="primary"],
    div.st-key-mode_email button[kind="primary"] {
        background-color: rgba(37, 99, 235, 0.12) !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.25) !important;
    }
    div.st-key-mode_msg button[kind="primary"] strong,
    div.st-key-mode_url button[kind="primary"] strong,
    div.st-key-mode_notice button[kind="primary"] strong,
    div.st-key-mode_image button[kind="primary"] strong,
    div.st-key-mode_email button[kind="primary"] strong {
        color: #ffffff !important;
    }
    div.st-key-mode_msg button[kind="primary"] p,
    div.st-key-mode_url button[kind="primary"] p,
    div.st-key-mode_notice button[kind="primary"] p,
    div.st-key-mode_image button[kind="primary"] p,
    div.st-key-mode_email button[kind="primary"] p {
        color: #93c5fd !important;
    }

    /* Input Section Inside Workspace */
    .tl-input-wrapper {
        margin-top: 1.25rem;
        padding-top: 1.15rem;
        border-top: 1px solid #1a2233;
        width: 100%;
    }
    .tl-input-header {
        margin-bottom: 0.65rem;
    }
    .tl-input-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.15rem;
    }
    .tl-input-desc {
        font-size: 0.84rem;
        color: #94a3b8;
    }

    /* Textarea & Inputs */
    .stTextArea textarea, .stTextInput input {
        background-color: #0c1018 !important;
        color: #f8fafc !important;
        border: 1px solid #1f293d !important;
        border-radius: 6px !important;
        font-size: 0.92rem !important;
        line-height: 1.5 !important;
        padding: 0.75rem 0.9rem !important;
        width: 100% !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }

    /* Primary Action Buttons */
    div.st-key-btn_analyze_action > button,
    div.st-key-btn_register_notice > button,
    div.st-key-btn_lookup_search > button,
    div.st-key-btn_signin > button {
        background-color: #2563eb !important;
        border: 1px solid #1d4ed8 !important;
        color: #ffffff !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        padding: 0.75rem 1.5rem !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25) !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
        margin-top: 0.75rem !important;
        width: 100% !important;
    }
    div.st-key-btn_analyze_action > button:hover,
    div.st-key-btn_register_notice > button:hover,
    div.st-key-btn_lookup_search > button:hover,
    div.st-key-btn_signin > button:hover {
        background-color: #1d4ed8 !important;
        border-color: #1e40af !important;
    }

    /* "How TrustLens Checks" Pipeline Bar */
    .tl-pipeline-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #0e1420;
        border: 1px solid #1a2233;
        border-radius: 6px;
        padding: 0.85rem 1.6rem;
        margin-bottom: 1.5rem;
        width: 100%;
    }
    .tl-pipeline-step {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .tl-step-index {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.82rem;
        font-weight: 700;
        color: #3b82f6;
    }
    .tl-step-text {
        display: flex;
        flex-direction: column;
    }
    .tl-step-label {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #cbd5e1;
    }
    .tl-step-detail {
        font-size: 0.82rem;
        color: #64748b;
    }
    .tl-pipeline-connector {
        display: flex;
        align-items: center;
        color: #334155;
    }

    @media (max-width: 768px) {
        .tl-pipeline-bar {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.85rem;
            padding: 1rem;
        }
        .tl-pipeline-connector {
            display: none;
        }
    }

    /* Empty State */
    .tl-empty-state {
        background-color: #0e1420;
        border: 1px solid #1a2233;
        border-radius: 6px;
        padding: 2.25rem 1.5rem;
        text-align: center;
        width: 100%;
    }
    .tl-empty-icon {
        margin-bottom: 0.65rem;
        color: #475569;
    }
    .tl-empty-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 0.25rem;
    }
    .tl-empty-desc {
        font-size: 0.84rem;
        color: #64748b;
        max-width: 480px;
        margin: 0 auto;
        line-height: 1.45;
    }

    /* Trust Report Styles */
    .tl-report-wrapper {
        margin-top: 0.25rem;
        width: 100%;
    }
    .tl-report-supertitle {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.65rem;
    }

    /* Verdict Banner */
    .tl-verdict-banner {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 8px;
        padding: 1.4rem 1.75rem;
        margin-bottom: 1.15rem;
        width: 100%;
    }
    .tl-verdict-grid {
        display: grid;
        grid-template-columns: minmax(240px, 320px) 1fr;
        gap: 2rem;
        align-items: flex-start;
    }
    .tl-verdict-left-col {
        display: flex;
        flex-direction: column;
        gap: 0.4rem;
    }
    .tl-verdict-right-col {
        border-left: 1px solid #1a2233;
        padding-left: 2rem;
        display: flex;
        flex-direction: column;
    }
    .tl-micro-label {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.2rem;
    }
    .tl-verdict-title {
        font-size: 1.65rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f8fafc;
        line-height: 1.2;
    }
    .tl-verdict-risk-row {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        margin-top: 0.2rem;
        flex-wrap: wrap;
    }
    .tl-risk-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.3rem 0.75rem;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .tl-score-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.3rem 0.65rem;
        border-radius: 4px;
        font-size: 0.76rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        background-color: #0c1018;
        border: 1px solid #1a2233;
        color: #94a3b8;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    }
    .tl-verdict-summary-text {
        font-size: 0.94rem;
        color: #cbd5e1;
        line-height: 1.55;
        margin-top: 0.25rem;
    }

    @media (max-width: 768px) {
        .tl-verdict-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
        .tl-verdict-right-col {
            border-left: none;
            padding-left: 0;
            border-top: 1px solid #1a2233;
            padding-top: 0.85rem;
        }
    }

    /* Cards */
    .tl-card {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 6px;
        padding: 1.2rem 1.4rem;
        height: 100%;
        width: 100%;
    }
    .tl-card-header {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.65rem;
    }

    /* Bullets */
    .tl-bullet-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .tl-bullet-item {
        font-size: 0.90rem;
        color: #cbd5e1;
        line-height: 1.5;
        padding: 0.35rem 0;
        display: flex;
        align-items: flex-start;
        gap: 0.55rem;
    }
    .tl-bullet-flag {
        color: #ef4444;
        font-weight: bold;
    }

    /* Diff Container (What Changed) */
    .tl-diff-container {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 6px;
        padding: 1.25rem 1.45rem;
        margin-top: 1.15rem;
        width: 100%;
    }
    .tl-diff-subtext {
        font-size: 0.84rem;
        color: #94a3b8;
        margin-bottom: 0.75rem;
    }
    .tl-diff-grid {
        display: flex;
        flex-direction: column;
        gap: 0.65rem;
    }
    .tl-diff-card {
        background-color: #0c1018;
        border: 1px solid #1a2233;
        border-radius: 4px;
        padding: 0.85rem 1.1rem;
    }
    .tl-diff-title {
        font-size: 0.84rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.4rem;
    }
    .tl-diff-columns {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 0.85rem;
        font-size: 0.86rem;
    }
    .tl-diff-col-box {
        padding: 0.5rem 0.75rem;
        border-radius: 4px;
        line-height: 1.4;
    }
    .tl-diff-orig {
        background-color: #121824;
        color: #94a3b8;
        border: 1px solid #1e293b;
    }
    .tl-diff-fwd {
        background-color: rgba(245, 158, 11, 0.08);
        color: #fef08a;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .tl-diff-highlight {
        background-color: rgba(245, 158, 11, 0.25);
        color: #fde047;
        padding: 0.1rem 0.3rem;
        border-radius: 3px;
        font-weight: 600;
    }
    .tl-diff-arrow-icon {
        color: #475569;
        font-weight: bold;
    }

    @media (max-width: 768px) {
        .tl-diff-columns {
            grid-template-columns: 1fr;
            gap: 0.4rem;
        }
        .tl-diff-arrow-icon {
            display: none;
        }
    }

    /* Recommended Next Action */
    .tl-action-box {
        background-color: #0d1624;
        border: 1px solid #1e3a5f;
        border-left: 3px solid #3b82f6;
        border-radius: 6px;
        padding: 1.15rem 1.4rem;
        margin-top: 1.15rem;
        width: 100%;
    }
    .tl-action-title {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #60a5fa;
        margin-bottom: 0.35rem;
    }
    .tl-action-content {
        font-size: 0.94rem;
        color: #e2e8f0;
        line-height: 1.5;
    }

    /* Secondary Action Button */
    div.st-key-btn_verify_another > button {
        background-color: transparent !important;
        border: 1px solid #222d42 !important;
        color: #94a3b8 !important;
        font-size: 0.86rem !important;
        font-weight: 500 !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.2rem !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-btn_verify_another > button:hover {
        background-color: #121824 !important;
        border-color: #3b82f6 !important;
        color: #f8fafc !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# Frontend Adapter & Normalization Helper
# ==============================================================================
def _clean_text_string(val: Any) -> str:
    """
    Sanitize text: strip raw HTML tags, unescape entities, and normalize whitespace.
    Ensures raw HTML markup is never exposed as literal text to the user.
    """
    if not val:
        return ""
    text = str(val)
    if "<" in text and ">" in text:
        text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.strip()
    text = re.sub(r"^Signal\s*:\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^Signal\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_backend_report(raw: dict) -> dict:
    """
    Frontend adapter normalizing backend responses for Trust Report rendering.
    Maps backend fields: verdict, risk_level, risk_score, summary, red_flags, evidence, next_action, changes.
    """
    if not isinstance(raw, dict):
        return {
            "verdict": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "risk_score": 0,
            "summary": "No data returned from analysis.",
            "red_flags": [],
            "evidence": [],
            "what_changed": [],
            "next_action": "Verify independently.",
            "verification_id": None,
        }

    # Format notice diff changes if present
    what_changed = []
    raw_changes = raw.get("changes") or raw.get("what_changed") or []
    for c in raw_changes:
        if isinstance(c, dict):
            c_type = c.get("type", "replace")
            before = _clean_text_string(c.get("before") or "")
            after = _clean_text_string(c.get("after") or "")
            item_title = c.get("category") or ("Text Modified" if c_type == "replace" else "Content Added" if c_type == "add" else "Content Removed")

            if c_type == "replace":
                highlight = after
            elif c_type == "add":
                highlight = after
                before = "(Not present in baseline notice)"
            elif c_type == "remove":
                highlight = ""
                after = "(Removed from baseline notice)"
            else:
                highlight = after

            what_changed.append({
                "item": item_title,
                "original": before,
                "forwarded": after,
                "highlight": highlight,
            })
        elif isinstance(c, str):
            clean_c = _clean_text_string(c)
            if clean_c:
                what_changed.append(clean_c)

    # Clean red flags & evidence items to ensure plain readable text
    raw_red_flags = raw.get("red_flags") or []
    cleaned_red_flags = []
    for item in raw_red_flags:
        cleaned = _clean_text_string(item)
        if cleaned:
            cleaned_red_flags.append(cleaned)

    raw_evidence = raw.get("evidence") or []
    cleaned_evidence = []
    for item in raw_evidence:
        cleaned = _clean_text_string(item)
        if cleaned:
            cleaned_evidence.append(cleaned)

    summary_clean = _clean_text_string(raw.get("summary", "Analysis complete.")) or "Analysis complete."
    next_action_clean = _clean_text_string(raw.get("next_action", "Exercise caution before acting.")) or "Exercise caution before acting."

    return {
        "verdict": raw.get("verdict", "UNKNOWN"),
        "risk_level": raw.get("risk_level", "LOW"),
        "risk_score": raw.get("risk_score", 0),
        "summary": summary_clean,
        "red_flags": cleaned_red_flags,
        "evidence": cleaned_evidence,
        "what_changed": what_changed,
        "next_action": next_action_clean,
        "matched_source": raw.get("matched_source"),
        "has_matching_original": raw.get("has_matching_original", True if raw.get("matched_source") else False),
        "extracted_text": raw.get("extracted_text"),
        "fingerprint": raw.get("fingerprint"),
        "verification_id": raw.get("verification_id") or raw.get("report_id") or raw.get("id"),
        "image_authenticity": raw.get("image_authenticity"),
        "identity_protection": raw.get("identity_protection") or raw.get("protect"),
        "protect": raw.get("protect") or raw.get("identity_protection"),
    }


# ==============================================================================
# Status Styling Helper
# ==============================================================================
def get_risk_style(risk_level: str, verdict: str) -> dict:
    """Returns restrained status indicators for verdict states."""
    risk_upper = (risk_level or "").upper()
    verdict_upper = (verdict or "").upper()

    if (
        "HIGH" in risk_upper
        or "CRITICAL" in risk_upper
        or "MALICIOUS" in verdict_upper
        or "TAMPERED" in verdict_upper
        or "FRAUD" in verdict_upper
    ):
        return {
            "badge_text": "HIGH RISK" if "TAMPERED" not in verdict_upper else "TAMPERED / HIGH RISK",
            "border_color": "#dc2626",
            "bg_color": "rgba(239, 68, 68, 0.12)",
            "text_color": "#f87171",
            "accent_bar": "#ef4444",
        }
    elif (
        "MEDIUM" in risk_upper
        or "SUSPICIOUS" in verdict_upper
        or "WARN" in risk_upper
    ):
        return {
            "badge_text": "MEDIUM RISK" if "SUSPICIOUS" not in verdict_upper else "SUSPICIOUS / MEDIUM RISK",
            "border_color": "#d97706",
            "bg_color": "rgba(245, 158, 11, 0.12)",
            "text_color": "#fbbf24",
            "accent_bar": "#f59e0b",
        }
    elif (
        "LOW" in risk_upper
        or "SAFE" in verdict_upper
        or "AUTHENTIC" in verdict_upper
        or "VERIFIED" in verdict_upper
    ):
        badge_text = "AUTHENTIC / SAFE" if "AUTHENTIC" in verdict_upper else "VERIFIED / LOW RISK"
        return {
            "badge_text": badge_text,
            "border_color": "#059669",
            "bg_color": "rgba(16, 185, 129, 0.12)",
            "text_color": "#34d399",
            "accent_bar": "#10b981",
        }
    else:
        return {
            "badge_text": "UNABLE TO VERIFY",
            "border_color": "#475569",
            "bg_color": "rgba(148, 163, 184, 0.12)",
            "text_color": "#cbd5e1",
            "accent_bar": "#94a3b8",
        }


# ==============================================================================
# UI Component Renderers
# ==============================================================================
def render_header():
    """Render top navbar with brand and unobtrusive organization controls."""
    col_nav_brand, col_nav_auth = st.columns([6, 3])

    with col_nav_brand:
        st.markdown(
            """
            <div class="tl-nav-brand-wrap">
                <div class="tl-nav-brand">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        <path d="m9 12 2 2 4-4"/>
                    </svg>
                    <span class="tl-nav-brand-title">TrustLens</span>
                </div>
                <span class="tl-nav-tagline">Check Before You Believe</span>
                <div class="tl-nav-status">
                    <span class="tl-status-dot"></span>
                    <span>System ready</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_nav_auth:
        is_org_logged_in = st.session_state.get("org_logged_in", False)
        current_view = st.session_state.get("view", "public")

        if is_org_logged_in:
            c1, c2 = st.columns(2)
            with c1:
                if current_view == "org_dashboard":
                    if st.button("Public View", key="nav_btn_public", use_container_width=True):
                        st.session_state["view"] = "public"
                        st.rerun()
                else:
                    if st.button("Org Dashboard", key="nav_btn_dash", use_container_width=True):
                        st.session_state["view"] = "org_dashboard"
                        st.rerun()
            with c2:
                if st.button("Logout", key="nav_btn_logout", use_container_width=True):
                    st.session_state["org_logged_in"] = False
                    st.session_state["view"] = "public"
                    st.rerun()
        else:
            if current_view == "org_login":
                if st.button("← Back to TrustLens", key="nav_btn_back_home", use_container_width=True):
                    st.session_state["view"] = "public"
                    st.rerun()
            else:
                if st.button("Organization Login", key="nav_btn_org_login", use_container_width=True):
                    st.session_state["view"] = "org_login"
                    st.rerun()


def render_hero():
    """Render short, focused hero heading."""
    st.markdown(
        """
        <div class="tl-hero-section">
            <h1 class="tl-hero-heading">Verify before you trust.</h1>
            <p class="tl-hero-subtext">
                Check suspicious messages, links, notices, images, and emails before you act or share them. TrustLens inspects signals and explains the evidence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pipeline_bar():
    """Render subtle three-step explanation of how TrustLens checks."""
    st.markdown(
        """
        <div class="tl-pipeline-bar">
            <div class="tl-pipeline-step">
                <span class="tl-step-index">01</span>
                <div class="tl-step-text">
                    <span class="tl-step-label">INPUT</span>
                    <span class="tl-step-detail">Message, link, notice, image, or email</span>
                </div>
            </div>
            <div class="tl-pipeline-connector">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
            <div class="tl-pipeline-step">
                <span class="tl-step-index">02</span>
                <div class="tl-step-text">
                    <span class="tl-step-label">CHECK</span>
                    <span class="tl-step-detail">Local signals and forensics comparison</span>
                </div>
            </div>
            <div class="tl-pipeline-connector">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#334155" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </div>
            <div class="tl-pipeline-step">
                <span class="tl-step-index">03</span>
                <div class="tl-step-text">
                    <span class="tl-step-label">REPORT</span>
                    <span class="tl-step-detail">Evidence, risk and audit receipt</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state():
    """Render tasteful empty state before analysis."""
    st.markdown(
        """
        <div class="tl-empty-state">
            <div class="tl-empty-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                </svg>
            </div>
            <div class="tl-empty-title">Your verification report will appear here</div>
            <div class="tl-empty-desc">
                Paste a message, link, or email — or upload a notice, image, or email screenshot above to begin verification.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trust_report(report_data: dict):
    """
    Render Trust Report following strict visual hierarchy:
    1. Verdict & Summary Banner
    2. Red Flags & Evidence Table
    3. What Changed (for notices only)
    4. Image Authenticity (when image analyzed)
    5. PROTECT — Identity Safety (when identity signals present)
    6. Recommended Next Action
    7. Verification Receipt + QR
    8. Technical Evidence Expander
    """
    verdict = report_data.get("verdict", "Under Review")
    risk_level = report_data.get("risk_level", "Unknown")
    risk_score = report_data.get("risk_score", 0)
    summary = report_data.get("summary", "No summary available.")
    red_flags = report_data.get("red_flags", [])
    evidence = report_data.get("evidence", [])
    what_changed = report_data.get("what_changed", [])
    next_action = report_data.get("next_action", "No specific action recorded.")
    verification_id = report_data.get("verification_id")
    image_authenticity = report_data.get("image_authenticity")
    protect_data = report_data.get("protect") or report_data.get("identity_protection")

    style = get_risk_style(risk_level, verdict)

    supertitle_text = "TRUST REPORT"
    if verification_id:
        supertitle_text += f" · REF: {verification_id}"

    st.markdown('<div class="tl-report-wrapper">', unsafe_allow_html=True)
    st.markdown(f'<div class="tl-report-supertitle">{supertitle_text}</div>', unsafe_allow_html=True)

    # 1. Verdict & Summary Banner
    st.markdown(
        f"""
        <div class="tl-verdict-banner" style="border-left: 4px solid {style['accent_bar']};">
            <div class="tl-verdict-grid">
                <div class="tl-verdict-left-col">
                    <div class="tl-micro-label">VERDICT</div>
                    <div class="tl-verdict-title">{verdict}</div>
                    <div class="tl-verdict-risk-row">
                        <span class="tl-micro-label" style="margin-bottom: 0;">RISK LEVEL:</span>
                        <span class="tl-risk-pill" style="background-color: {style['bg_color']}; border: 1px solid {style['border_color']}; color: {style['text_color']};">
                            {style['badge_text']}
                        </span>
                        <span class="tl-score-pill">Risk Score: {risk_score}/100</span>
                    </div>
                </div>
                <div class="tl-verdict-right-col">
                    <div class="tl-micro-label">SUMMARY</div>
                    <div class="tl-verdict-summary-text">
                        {html.escape(_clean_text_string(summary))}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Repository match notice if no baseline match was found in notice verification
    if report_data.get("matched_source") is None and report_data.get("has_matching_original") is False:
        st.markdown(
            """
            <div class="tl-action-box" style="border-left-color: #f59e0b; background-color: #17150c; border-color: #451a03; margin-top: 0; margin-bottom: 1.15rem;">
                <div class="tl-action-title" style="color: #fbbf24;">REPOSITORY MATCH STATUS</div>
                <div class="tl-action-content" style="color: #fef08a;">
                    No verified original notice was found in the TrustLens repository. Showing general authenticity and tampering analysis.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 2. Red Flags & Evidence Table
    col_flags, col_evidence = st.columns(2)

    with col_flags:
        flags_html = ""
        if red_flags:
            for item in red_flags:
                clean_item = html.escape(_clean_text_string(item))
                flags_html += f'<li class="tl-bullet-item"><span class="tl-bullet-flag">•</span><span>{clean_item}</span></li>'
        else:
            flags_html = '<li class="tl-bullet-item" style="color: #94a3b8;">No distinct red flags detected.</li>'

        st.markdown(
            f'<div class="tl-card"><div class="tl-card-header">RED FLAGS</div><ul class="tl-bullet-list">{flags_html}</ul></div>',
            unsafe_allow_html=True,
        )

    with col_evidence:
        evidence_html = ""
        if evidence:
            for item in evidence:
                clean_item = html.escape(_clean_text_string(item))
                evidence_html += f'<li class="tl-bullet-item"><span class="tl-bullet-flag" style="color: #60a5fa;">•</span><span>{clean_item}</span></li>'
        else:
            evidence_html = '<li class="tl-bullet-item" style="color: #94a3b8;">No technical signals recorded.</li>'

        st.markdown(
            f'<div class="tl-card"><div class="tl-card-header">EVIDENCE</div><ul class="tl-bullet-list">{evidence_html}</ul></div>',
            unsafe_allow_html=True,
        )

    # 3. What Changed (for notices only)
    if what_changed:
        diff_cards_html = ""
        for change in what_changed:
            if isinstance(change, dict):
                title = change.get("item", "Discrepancy")
                original = change.get("original", "")
                forwarded = change.get("forwarded", "")
                highlight = change.get("highlight", "")

                if highlight and highlight in forwarded:
                    fwd_display = forwarded.replace(highlight, f'<mark class="tl-diff-highlight">{highlight}</mark>')
                else:
                    fwd_display = forwarded

                diff_cards_html += f"""
                <div class="tl-diff-card">
                    <div class="tl-diff-title">{title}</div>
                    <div class="tl-diff-columns">
                        <div class="tl-diff-col-box tl-diff-orig">
                            <span style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b; display: block; margin-bottom: 2px;">Original:</span>
                            {original}
                        </div>
                        <div class="tl-diff-arrow-icon">→</div>
                        <div class="tl-diff-col-box tl-diff-fwd">
                            <span style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; color: #d97706; display: block; margin-bottom: 2px;">Forwarded:</span>
                            {fwd_display}
                        </div>
                    </div>
                </div>
                """
            else:
                diff_cards_html += f"""
                <div class="tl-diff-card">
                    <div class="tl-diff-title">• {change}</div>
                </div>
                """

        st.markdown(
            f"""
            <div class="tl-diff-container">
                <div class="tl-card-header">WHAT CHANGED</div>
                <div class="tl-diff-subtext">Discrepancies identified against the verified official baseline:</div>
                <div class="tl-diff-grid">
                    {diff_cards_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. Image Authenticity (when image was analyzed)
    if image_authenticity and isinstance(image_authenticity, dict):
        assessment = image_authenticity.get("assessment", "UNCERTAIN")
        confidence = image_authenticity.get("confidence", "LOW")
        signals = image_authenticity.get("signals", [])
        limitations = image_authenticity.get("limitations", [])

        assess_colors = {
            "LIKELY_ORIGINAL": ("#059669", "rgba(16,185,129,0.1)", "#34d399"),
            "LIKELY_MANIPULATED": ("#dc2626", "rgba(239,68,68,0.1)", "#f87171"),
            "LIKELY_AI_GENERATED": ("#d97706", "rgba(245,158,11,0.1)", "#fbbf24"),
            "UNCERTAIN": ("#475569", "rgba(148,163,184,0.1)", "#94a3b8"),
        }
        ac_border, ac_bg, ac_text = assess_colors.get(assessment, assess_colors["UNCERTAIN"])

        signals_html = "".join(
            f'<li class="tl-bullet-item"><span class="tl-bullet-flag" style="color:#60a5fa;">•</span>'
            f'<span>{html.escape(_clean_text_string(s))}</span></li>'
            for s in signals
        ) or '<li class="tl-bullet-item" style="color:#94a3b8;">No specific tampering signals detected.</li>'

        limitations_html = "".join(
            f'<li class="tl-bullet-item"><span class="tl-bullet-flag" style="color:#94a3b8;">•</span>'
            f'<span>{html.escape(_clean_text_string(lim))}</span></li>'
            for lim in limitations
        ) or ""

        st.markdown(
            f"""
            <div class="tl-card" style="margin-top:1.15rem; border-left: 3px solid {ac_border};">
                <div class="tl-card-header">IMAGE AUTHENTICITY</div>
                <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.65rem;">
                    <span style="font-size:1.05rem; font-weight:700; color:{ac_text};">{assessment.replace("_", " ")}</span>
                    <span style="font-size:0.74rem; background:{ac_bg}; border:1px solid {ac_border};
                           color:{ac_text}; padding:2px 8px; border-radius:4px;">Confidence: {confidence}</span>
                </div>
                <div class="tl-micro-label" style="margin-bottom:0.25rem;">OBSERVABLE SIGNALS</div>
                <ul class="tl-bullet-list">{signals_html}</ul>
                {f'<div class="tl-micro-label" style="margin-top:0.55rem; margin-bottom:0.25rem;">LIMITATIONS</div><ul class="tl-bullet-list">{limitations_html}</ul>' if limitations_html else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 5. PROTECT — Identity Safety (when identity signals present)
    if protect_data and isinstance(protect_data, dict):
        if "identity_protection" in protect_data and isinstance(protect_data["identity_protection"], dict):
            protect_data = protect_data["identity_protection"]
        id_risk = protect_data.get("risk_level") or protect_data.get("identity_attack_risk", "LOW")
        raw_attacks = protect_data.get("attack_type") or protect_data.get("possible_attack") or []
        if isinstance(raw_attacks, list):
            attack_types = [str(a).strip() for a in raw_attacks if a and str(a).upper() not in ("NONE", "UNKNOWN")]
        elif isinstance(raw_attacks, str) and raw_attacks.upper() not in ("NONE", "UNKNOWN"):
            attack_types = [raw_attacks.strip()]
        else:
            attack_types = []
        p_signals = protect_data.get("signals", [])
        p_actions = protect_data.get("recommended_actions") or protect_data.get("actions", [])

        if id_risk != "LOW" or p_signals or attack_types:
            risk_colors = {
                "HIGH": ("#dc2626", "rgba(239,68,68,0.1)", "#f87171"),
                "MEDIUM": ("#d97706", "rgba(245,158,11,0.1)", "#fbbf24"),
                "LOW": ("#059669", "rgba(16,185,129,0.1)", "#34d399"),
            }
            pr_border, pr_bg, pr_text = risk_colors.get(id_risk, risk_colors["LOW"])

            ps_html = "".join(
                f'<li class="tl-bullet-item"><span class="tl-bullet-flag" style="color:#f87171;">•</span>'
                f'<span>{html.escape(_clean_text_string(s))}</span></li>'
                for s in p_signals
            ) or '<li class="tl-bullet-item" style="color:#94a3b8;">No identity attack signals detected.</li>'

            pa_html = "".join(
                f'<li class="tl-bullet-item"><span class="tl-bullet-flag" style="color:#34d399;">→</span>'
                f'<span>{html.escape(_clean_text_string(a))}</span></li>'
                for a in p_actions
            ) or ""

            attack_display = ", ".join(attack_types) if attack_types else "Identity Risk Signal"

            st.markdown(
                f"""
                <div class="tl-card" style="margin-top:1.15rem; border-left: 3px solid {pr_border};">
                    <div class="tl-card-header">🛡 PROTECT — IDENTITY SAFETY</div>
                    <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:0.65rem;">
                        <span style="font-size:0.95rem; font-weight:600; color:{pr_text};">
                            Identity Attack Risk: {id_risk}
                        </span>
                        <span style="font-size:0.74rem; background:{pr_bg}; border:1px solid {pr_border};
                               color:{pr_text}; padding:2px 8px; border-radius:4px;">{attack_display}</span>
                    </div>
                    <div class="tl-micro-label" style="margin-bottom:0.25rem;">OBSERVABLE ATTACK SIGNALS</div>
                    <ul class="tl-bullet-list">{ps_html}</ul>
                    {f'<div class="tl-micro-label" style="margin-top:0.55rem; margin-bottom:0.25rem;">PROTECTIVE ACTIONS</div><ul class="tl-bullet-list">{pa_html}</ul>' if pa_html else ''}
                    <div style="font-size:0.74rem; color:#475569; margin-top:0.55rem;">
                        ⚠ TrustLens reports observable risk signals only. Direct confirmation of SIM-swap or account takeover requires telecom/service-level verification.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 6. Recommended Next Action
    st.markdown(
        f"""
        <div class="tl-action-box">
            <div class="tl-action-title">RECOMMENDED NEXT ACTION</div>
            <div class="tl-action-content">{html.escape(_clean_text_string(next_action))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 7. Verification Receipt + QR Code
    st.markdown(
        '<div style="margin-top:1.25rem; border-top: 1px solid #1a2233; padding-top:1rem;"></div>',
        unsafe_allow_html=True,
    )
    col_receipt, col_qr = st.columns([3, 1])

    with col_receipt:
        receipt_vid = verification_id or st.session_state.get("_report_verification_id")
        if not receipt_vid:
            receipt_vid = generate_verification_id()
            st.session_state["_report_verification_id"] = receipt_vid

        timestamp_now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

        receipt, qr_bytes = generate_qr_receipt(
            verification_id=receipt_vid,
            verdict=verdict,
            risk_level=risk_level,
            risk_score=risk_score,
            summary=summary[:120] + ("..." if len(summary) > 120 else ""),
            timestamp=timestamp_now,
        )
        st.session_state["_last_receipt"] = receipt
        st.session_state["_last_qr_bytes"] = qr_bytes

        # Persist report into SQLite database for QR retrieval
        save_verification_report(receipt_vid, report_data)

        st.markdown(
            f"""
            <div class="tl-card" style="margin-top:0;">
                <div class="tl-card-header">VERIFICATION RECEIPT</div>
                <table style="width:100%; border-collapse:collapse; font-size:0.82rem; color:#94a3b8;">
                    <tr><td style="padding:3px 0; color:#64748b; width:130px;">Product</td>
                        <td style="color:#f8fafc; font-weight:600;">TrustLens</td></tr>
                    <tr><td style="padding:3px 0; color:#64748b;">Verification ID</td>
                        <td style="color:#f8fafc; font-family:monospace;">{html.escape(receipt['verification_id'])}</td></tr>
                    <tr><td style="padding:3px 0; color:#64748b;">Verdict</td>
                        <td style="color:{style['text_color']}; font-weight:600;">{html.escape(receipt['verdict'])}</td></tr>
                    <tr><td style="padding:3px 0; color:#64748b;">Risk Level</td>
                        <td style="color:{style['text_color']};">{html.escape(receipt['risk_level'])}</td></tr>
                    <tr><td style="padding:3px 0; color:#64748b;">Risk Score</td>
                        <td style="color:#f8fafc;">{receipt['risk_score']}/100</td></tr>
                    <tr><td style="padding:3px 0; color:#64748b;">Timestamp</td>
                        <td style="color:#f8fafc;">{html.escape(receipt['timestamp'])}</td></tr>
                    <tr><td style="padding:3px 0; color:#64748b;">Summary</td>
                        <td style="color:#cbd5e1;">{html.escape(receipt['summary'])}</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if qr_bytes:
            st.download_button(
                label="⬇ Download Verification Receipt (QR)",
                data=qr_bytes,
                file_name=f"trustlens_receipt_{receipt_vid}.png",
                mime="image/png",
                key=f"dl_qr_{receipt_vid}",
            )

    with col_qr:
        if qr_bytes:
            st.markdown(
                '<div class="tl-card" style="margin-top:0; text-align:center;">',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="tl-micro-label" style="text-align:center; margin-bottom:0.4rem;">SCAN TO AUDIT</div>',
                unsafe_allow_html=True,
            )
            st.image(qr_bytes, caption="Verification QR", use_container_width=True)
            st.markdown(
                f'<div style="font-size:0.68rem; color:#475569; text-align:center; margin-top:2px;">'
                f'{html.escape(receipt.get("verification_url", ""))}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # 8. Collapsible Technical Evidence & Audit Telemetry (Principle 10)
    with st.expander("Technical Evidence & Audit Details"):
        st.markdown("**Cryptographic Integrity**")
        fp_val = report_data.get("fingerprint") or generate_fingerprint(summary)
        st.code(f"SHA-256 Fingerprint: {fp_val}", language="text")

        if report_data.get("matched_source"):
            st.markdown("**Repository Baseline Reference**")
            st.write(f"Matched Official Notice ID: `{report_data.get('matched_source')}`")

        if report_data.get("extracted_text"):
            st.markdown("**Extracted Text from Image (Gemini Vision OCR)**")
            st.caption(report_data.get("extracted_text")[:350] + ("..." if len(report_data.get("extracted_text")) > 350 else ""))

        st.markdown("**Immutable Audit Log**")
        st.caption("This report is indexed in the TrustLens SQLite audit log. Use the Verification ID or scan the QR code to re-audit this result at any time.")

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# View Renderers: Public Verification, Organization Login, Dashboard, Receipt Lookup
# ==============================================================================
def render_public_verification():
    """Render the primary student / public verification view (No login required)."""
    render_hero()

    st.markdown(
        """
        <div class="tl-workspace-card">
            <div class="tl-workspace-header">
                <div class="tl-workspace-title">Verify content</div>
                <div class="tl-workspace-desc">Choose what you want to check.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    # Mode Selector Buttons: 5 balanced modes
    col_msg, col_url, col_notice, col_image, col_email = st.columns(5)

    with col_msg:
        if st.button(
            "💬 **Message**  \nCheck forwarded messages and offers",
            key="mode_msg",
            use_container_width=True,
            type="primary" if st.session_state["selected_mode"] == "Message" else "secondary",
        ):
            if st.session_state["selected_mode"] != "Message":
                st.session_state["selected_mode"] = "Message"
                st.session_state["has_analyzed"] = False
                st.session_state["report_data"] = None
                st.rerun()

    with col_url:
        if st.button(
            "🔗 **URL**  \nInspect suspicious links and domains",
            key="mode_url",
            use_container_width=True,
            type="primary" if st.session_state["selected_mode"] == "URL" else "secondary",
        ):
            if st.session_state["selected_mode"] != "URL":
                st.session_state["selected_mode"] = "URL"
                st.session_state["has_analyzed"] = False
                st.session_state["report_data"] = None
                st.rerun()

    with col_notice:
        if st.button(
            "📄 **Notice**  \nCheck a forwarded notice",
            key="mode_notice",
            use_container_width=True,
            type="primary" if st.session_state["selected_mode"] == "Notice" else "secondary",
        ):
            if st.session_state["selected_mode"] != "Notice":
                st.session_state["selected_mode"] = "Notice"
                st.session_state["has_analyzed"] = False
                st.session_state["report_data"] = None
                st.rerun()

    with col_image:
        if st.button(
            "🖼 **Image**  \nCheck authenticity or manipulation",
            key="mode_image",
            use_container_width=True,
            type="primary" if st.session_state["selected_mode"] == "Image" else "secondary",
        ):
            if st.session_state["selected_mode"] != "Image":
                st.session_state["selected_mode"] = "Image"
                st.session_state["has_analyzed"] = False
                st.session_state["report_data"] = None
                st.rerun()

    with col_email:
        if st.button(
            "✉️ **Email**  \nInspect sender, links & visual signals",
            key="mode_email",
            use_container_width=True,
            type="primary" if st.session_state["selected_mode"] == "Email Screenshot" else "secondary",
        ):
            if st.session_state["selected_mode"] != "Email Screenshot":
                st.session_state["selected_mode"] = "Email Screenshot"
                st.session_state["has_analyzed"] = False
                st.session_state["report_data"] = None
                st.rerun()

    # Dynamic Input Area
    user_input = None
    current_mode = st.session_state["selected_mode"]
    notice_forwarded_text = None
    notice_forwarded_image = None
    image_file = None
    email_screenshot_file = None
    email_pasted_text = None

    st.markdown('<div class="tl-input-wrapper">', unsafe_allow_html=True)

    if current_mode == "Message":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Paste the message</div>
                <div class="tl-input-desc">Paste suspicious text, job offer, OTP request, or forwarded message. TrustLens checks content safety and identity risks (PROTECT).</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        user_input = st.text_area(
            "Suspicious message",
            placeholder="Paste suspicious text, WhatsApp message, or SMS here...",
            height=140,
            key="msg_input_area",
            label_visibility="collapsed",
        )
        action_btn_text = "Analyze Message ➔"

    elif current_mode == "URL":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Enter the URL</div>
                <div class="tl-input-desc">Paste the link you want TrustLens to inspect for impersonation, IP hosts, or suspicious redirects.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        user_input = st.text_input(
            "Suspicious URL",
            placeholder="https://example.com/verify-account",
            key="url_input_field",
            label_visibility="collapsed",
        )
        action_btn_text = "Inspect URL ➔"

    elif current_mode == "Notice":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Verify a Forwarded Notice</div>
                <div class="tl-input-desc">Upload or paste the forwarded notice. TrustLens will look for the matching official source and compare the notice for changes.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tab_image, tab_text = st.tabs(["📷 Upload Forwarded Notice", "📋 Paste Notice Text"])

        with tab_image:
            notice_forwarded_image = st.file_uploader(
                "Upload forwarded notice (PNG, JPG, JPEG, WEBP)",
                type=["png", "jpg", "jpeg", "webp"],
                key="notice_fwd_image",
                label_visibility="collapsed",
            )
            if notice_forwarded_image:
                st.caption("TrustLens will read the notice with Gemini Vision, match the official baseline, and highlight changes.")

        with tab_text:
            notice_forwarded_text = st.text_area(
                "Forwarded notice text",
                placeholder="Paste the forwarded or suspicious notice text here...",
                height=130,
                key="notice_fwd_text",
                label_visibility="collapsed",
            )
        action_btn_text = "Verify Notice ➔"

    elif current_mode == "Image":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Check an Image</div>
                <div class="tl-input-desc">Upload an image or screenshot to assess whether it appears authentic, manipulated, or AI-generated. TrustLens will analyze visual signals and report observable evidence.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        image_file = st.file_uploader(
            "Upload Image or Screenshot",
            type=["png", "jpg", "jpeg", "webp"],
            key="general_image_uploader",
            label_visibility="collapsed",
        )
        if image_file:
            st.caption(
                "TrustLens will send this image to Gemini Vision and assess for visual manipulation, suspicious edits, unusual text rendering, pasted regions, or AI-generation indicators."
            )
        action_btn_text = "Check Image ➔"

    elif current_mode == "Email Screenshot":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Verify an Email</div>
                <div class="tl-input-desc">Upload a screenshot of a suspicious email and TrustLens will inspect the sender, content, links, requests, and visual signals.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tab_img, tab_txt = st.tabs(["📷 Upload Email Screenshot", "📋 Paste Email Text"])

        with tab_img:
            email_screenshot_file = st.file_uploader(
                "Upload email screenshot (PNG, JPG, JPEG, WEBP)",
                type=["png", "jpg", "jpeg", "webp"],
                key="email_screenshot_uploader",
                label_visibility="collapsed",
            )
            if email_screenshot_file:
                st.caption("TrustLens inspects sender domains, urgency, demands, embedded links, and visual impersonation signals.")

        with tab_txt:
            email_pasted_text = st.text_area(
                "Email text content",
                placeholder="Paste email headers and body text here...",
                height=130,
                key="email_text_input",
                label_visibility="collapsed",
            )
        action_btn_text = "Analyze Email ➔"

    st.markdown("</div>", unsafe_allow_html=True)

    # Primary Action Button
    analyze_clicked = st.button(
        action_btn_text,
        type="primary",
        key="btn_analyze_action",
        use_container_width=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # Pipeline Bar
    render_pipeline_bar()

    # Backend Execution Logic
    if analyze_clicked:
        is_valid = True

        if current_mode == "Message":
            if not user_input or not user_input.strip():
                st.warning("Please enter a message or text to verify.")
                is_valid = False
        elif current_mode == "URL":
            if not user_input or not user_input.strip():
                st.warning("Please enter a URL to verify.")
                is_valid = False
        elif current_mode == "Notice":
            if not notice_forwarded_text and not notice_forwarded_image:
                st.warning("Please upload a notice image or paste the forwarded notice text.")
                is_valid = False
        elif current_mode == "Image":
            if not image_file:
                st.warning("Please upload an image or screenshot to check.")
                is_valid = False
        elif current_mode == "Email Screenshot":
            if not email_screenshot_file and not (email_pasted_text and email_pasted_text.strip()):
                st.warning("Please upload an email screenshot or paste the email text.")
                is_valid = False

        if is_valid:
            try:
                if current_mode == "Message":
                    with st.spinner("Analyzing message with local signals and Gemini..."):
                        raw_report = analyze_text(user_input.strip())

                elif current_mode == "URL":
                    with st.spinner("Inspecting URL structure, domain signals and threat patterns..."):
                        raw_report = analyze_url(user_input.strip())

                elif current_mode == "Notice":
                    fwd_bytes = None
                    fwd_mime = "image/png"
                    if notice_forwarded_image:
                        fwd_bytes = notice_forwarded_image.read()
                        fwd_mime = notice_forwarded_image.type or "image/png"

                    with st.status("Verifying Notice with TrustLens...", expanded=True) as status_box:
                        st.write("Finding official baseline source in repository...")
                        raw_report = analyze_notice(
                            content=notice_forwarded_text.strip() if notice_forwarded_text else None,
                            image_bytes=fwd_bytes,
                            mime_type=fwd_mime,
                        )
                        if raw_report.get("matched_source"):
                            st.write("Official source found ✓")
                            st.write("Comparing text structure and visual elements...")
                        else:
                            st.write("No matching baseline found in repository. Assessing document authenticity...")
                        st.write("Report ready ✓")
                        status_box.update(label="Verification Complete ✓", state="complete", expanded=False)

                elif current_mode == "Image":
                    img_bytes = image_file.read()
                    img_mime = image_file.type or "image/png"
                    with st.spinner("Sending image to Gemini Vision for authenticity analysis..."):
                        raw_report = analyze_image(
                            image_bytes=img_bytes,
                            mime_type=img_mime,
                        )

                elif current_mode == "Email Screenshot":
                    em_bytes = None
                    em_mime = "image/png"
                    if email_screenshot_file:
                        em_bytes = email_screenshot_file.read()
                        em_mime = email_screenshot_file.type or "image/png"

                    with st.spinner("Analyzing email with Gemini Vision, URL forensics and PROTECT..."):
                        raw_report = analyze_email(
                            image_bytes=em_bytes,
                            mime_type=em_mime,
                            content=email_pasted_text.strip() if email_pasted_text else None,
                        )

                st.session_state["report_data"] = normalize_backend_report(raw_report)
                st.session_state["has_analyzed"] = True
                st.session_state.pop("_report_verification_id", None)

            except EnvironmentError:
                st.error(
                    "⚠️ **TrustLens is not configured yet.**\n\n"
                    "Create a `.env` file in the project root and add your Gemini API key:\n\n"
                    "```\nGEMINI_API_KEY=your_key_here\n```\n\n"
                    "You can get a free key at [aistudio.google.com](https://aistudio.google.com)."
                )
            except RuntimeError:
                st.error(
                    "⚠️ **Analysis failed.** The Gemini API returned an unexpected response. "
                    "Please try again in a moment."
                )
            except Exception:
                st.error("Unable to analyze this item. Please check your input or upload a clearer image.")

    # Render Report or Empty State
    if st.session_state.get("has_analyzed") and st.session_state.get("report_data"):
        render_trust_report(st.session_state["report_data"])

        # Secondary Reset Action
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("Verify another item", key="btn_verify_another"):
            st.session_state["has_analyzed"] = False
            st.session_state["report_data"] = None
            st.session_state.pop("_report_verification_id", None)
            st.rerun()
    else:
        render_empty_state()



def render_org_login():
    """Render clean, centered organization login page (Requirement 3)."""
    _, col_login, _ = st.columns([1, 2, 1])
    with col_login:
        st.markdown(
            """
            <div class="tl-workspace-card" style="margin-top: 1.5rem;">
                <div class="tl-workspace-header" style="text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.35rem;">🏛</div>
                    <div class="tl-workspace-title" style="font-size: 1.3rem;">Official Organization Login</div>
                    <div class="tl-workspace-desc">Authorized organizations can publish verified notices.</div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        email = st.text_input("Email", placeholder="velroysharon@gmail.com", key="login_email")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pw")

        if st.button("Sign In", type="primary", use_container_width=True, key="btn_signin"):
            clean_email = (email or "").strip().lower()
            clean_pw = (password or "").strip()
            # Demo authentication (hackathon demo only)
            if clean_email == "velroysharon@gmail.com" and clean_pw == "1234":
                st.session_state["org_logged_in"] = True
                st.session_state["view"] = "org_dashboard"
                st.rerun()
            else:
                st.error("Invalid email or password.")

        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Back to TrustLens", key="btn_back_from_login", use_container_width=True):
            st.session_state["view"] = "public"
            st.rerun()


def render_org_dashboard():
    """Render official college / organization dashboard (Requirement 4 & 18)."""
    if not st.session_state.get("org_logged_in", False):
        render_org_login()
        return

    st.markdown(
        """
        <div class="tl-workspace-card">
            <div class="tl-workspace-header" style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div class="tl-workspace-title">OFFICIAL ORGANIZATION</div>
                    <div class="tl-workspace-desc">Publish authentic institutional circulars to establish verified baselines for student verification.</div>
                </div>
            </div>
            <div class="tl-input-title" style="margin-top: 0.75rem; margin-bottom: 0.5rem;">Publish Official Notice</div>
        """,
        unsafe_allow_html=True,
    )

    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        college_title = st.text_input("Notice title", placeholder="e.g. University Scholarship Notice 2026", key="admin_notice_title")
    with col_t2:
        college_category = st.selectbox(
            "Category",
            [
                "Scholarships & Financial Aid",
                "Academic & Exams",
                "Admissions & Registration",
                "Administrative & Fees",
                "Campus & Events",
                "General Notice",
            ],
            key="admin_notice_cat",
        )

    tab_c_img, tab_c_text = st.tabs(["📷 Upload Notice Image", "📋 Official Notice Text"])
    with tab_c_img:
        college_img = st.file_uploader("Upload notice (PNG, JPG, JPEG, WEBP)", type=["png", "jpg", "jpeg", "webp"], key="admin_notice_img")
        if college_img:
            st.caption("Gemini Vision will extract circular text and index visual features for side-by-side verification.")
    with tab_c_text:
        college_text = st.text_area("Official notice text", placeholder="Paste authentic baseline notice or circular text here...", height=120, key="admin_notice_text")

    if st.button("Publish Official Notice", type="primary", key="btn_register_notice", use_container_width=True):
        if not college_title or not college_title.strip():
            st.warning("Please provide a notice title.")
        elif not college_text and not college_img:
            st.warning("Please provide official notice text or upload a notice image.")
        else:
            with st.spinner("Processing notice with Gemini Vision and registering into repository..."):
                img_bytes = None
                img_mime = "image/png"
                final_content = college_text.strip() if college_text else ""
                if college_img:
                    img_bytes = college_img.read()
                    img_mime = college_img.type or "image/png"
                    if not final_content:
                        try:
                            final_content = extract_text_from_image(img_bytes, img_mime)
                        except Exception as e:
                            st.error(f"Could not extract text from image: {e}")

                if final_content or img_bytes:
                    reg_id = save_official_notice(
                        title=college_title.strip(),
                        content=final_content,
                        notice_id=None,
                        image_blob=img_bytes,
                        image_mime=img_mime,
                        category=college_category,
                    )
                    st.success(f"Official notice '{college_title.strip()}' published successfully ✓ (Ref: `{reg_id}`)")
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Published Notices Section (Compact table-like layout)
    stored_notices = get_all_official_notices()
    count_label = f"({len(stored_notices)})" if stored_notices else "(0)"
    st.markdown(
        f"""
        <div class="tl-card" style="margin-top: 1.35rem;">
            <div class="tl-card-header" style="display:flex; justify-content:space-between; align-items:center;">
                <span>PUBLISHED NOTICES {count_label}</span>
                <span style="font-size:0.72rem; color:#64748b; font-weight:normal;">ACTIVE BASELINE REPOSITORY</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    if stored_notices:
        for idx, n in enumerate(stored_notices, 1):
            has_img_tag = "📷 Image" if n.get("image_blob") else "📄 Text"
            cat_display = n.get("category") or "General Notice"
            st.markdown(
                f"""
                <div style="background:#0c1018; border:1px solid #1a2233; border-radius:6px; padding:0.65rem 0.9rem; margin-bottom:0.5rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                        <span style="font-weight:600; font-size:0.92rem; color:#f8fafc;">{idx}. {html.escape(n['title'])}</span>
                        <span style="font-size:0.72rem; color:#64748b; margin-left:0.5rem;">{n['created_at'][:10] if n.get('created_at') else 'Active'}</span>
                    </div>
                    <div style="display:flex; gap:0.4rem; align-items:center;">
                        <span style="font-size:0.72rem; color:#38bdf8; background:rgba(56,189,248,0.1); border:1px solid rgba(56,189,248,0.3); padding:2px 7px; border-radius:4px;">{html.escape(cat_display)}</span>
                        <span style="font-size:0.72rem; color:#94a3b8; background:#121824; border:1px solid #1e293b; padding:2px 7px; border-radius:4px;">{has_img_tag}</span>
                        <span style="font-size:0.70rem; color:#64748b; font-family:monospace;">{html.escape(n['id'])}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No official notices published yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_receipt_lookup():
    """Render QR receipt lookup by verification ID."""
    st.markdown(
        """
        <div class="tl-workspace-card">
            <div class="tl-workspace-header">
                <div class="tl-workspace-title">Verification Record Retrieval</div>
                <div class="tl-workspace-desc">Audit an immutable TrustLens verification report using its Verification ID or QR receipt.</div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    search_id = st.text_input("Verification ID", placeholder="e.g. TL-8F29A...", key="lookup_search_input")
    if st.button("Search Audit Record ➔", type="primary", key="btn_lookup_search", use_container_width=True):
        if not search_id or not search_id.strip():
            st.warning("Please enter a Verification ID to search.")
        else:
            found_report = get_verification_report(search_id.strip())
            if found_report:
                st.session_state["_lookup_result"] = found_report
            else:
                st.session_state["_lookup_result"] = "NOT_FOUND"

    if st.session_state.get("_lookup_result") == "NOT_FOUND":
        st.error("Verification record not found. The ID does not match any record in the TrustLens audit database.")
    elif isinstance(st.session_state.get("_lookup_result"), dict):
        rec = st.session_state["_lookup_result"]
        st.success(f"Verified Authentic Record retrieved from TrustLens database ✓ (Audit timestamp: {rec.get('stored_timestamp', 'N/A')})")
        render_trust_report(normalize_backend_report(rec))

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# Main Application Flow
# ==============================================================================
def main():
    # Session state initialization
    if "view" not in st.session_state:
        st.session_state["view"] = "public"
    if "org_logged_in" not in st.session_state:
        st.session_state["org_logged_in"] = False
    if "selected_mode" not in st.session_state:
        st.session_state["selected_mode"] = "Message"
    if "has_analyzed" not in st.session_state:
        st.session_state["has_analyzed"] = False
        st.session_state["report_data"] = None

    # Sync user_role for backwards-compatibility
    if st.session_state["view"] in ("org_dashboard", "org_login"):
        st.session_state["user_role"] = "college"
    elif st.session_state["view"] == "receipt_lookup":
        st.session_state["user_role"] = "lookup"
    else:
        st.session_state["user_role"] = "student"

    # Handle direct URL query parameter for QR receipt verification
    query_id = st.query_params.get("report_id") or st.query_params.get("id")
    if query_id:
        render_header()
        st.markdown(
            f"""
            <div class="tl-workspace-card">
                <div class="tl-workspace-header">
                    <div class="tl-workspace-title">Verification Record Retrieval</div>
                    <div class="tl-workspace-desc">Auditing record reference: <code>{html.escape(query_id)}</code></div>
                </div>
            """,
            unsafe_allow_html=True,
        )
        record = get_verification_report(query_id)
        if record:
            st.success(f"Verified Authentic Record retrieved from TrustLens database ✓ (Audit timestamp: {record.get('stored_timestamp', 'N/A')})")
            render_trust_report(normalize_backend_report(record))
        else:
            st.error("Verification record not found. The requested verification ID does not match any record in the TrustLens audit database.")

        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("← Return to Workspace", key="btn_return_from_query"):
            st.query_params.clear()
            st.session_state["view"] = "public"
            st.rerun()
        return

    # 1. Product Header
    render_header()

    # 2. View Routing
    current_view = st.session_state.get("view", "public")
    if current_view == "org_login":
        render_org_login()
    elif current_view == "org_dashboard":
        render_org_dashboard()
    elif current_view == "receipt_lookup":
        render_receipt_lookup()
    else:
        render_public_verification()


if __name__ == "__main__":
    main()
