import streamlit as st

# ==============================================================================
# Page Configuration & Visual Foundation
# ==============================================================================
st.set_page_config(
    page_title="TrustLens — Check Before You Believe",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Comprehensive Visual System: Wide Widescreen Cybersecurity / Verification Workspace
st.markdown(
    """
    <style>
    /* Global Base */
    .stApp {
        background-color: #0b0f17;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Wide Responsive Application Workspace: 90-94% width, max 1560px */
    .block-container {
        max-width: 1560px !important;
        width: 100% !important;
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
        padding-left: 4.5% !important;
        padding-right: 4.5% !important;
        margin: 0 auto !important;
    }

    @media (max-width: 1200px) {
        .block-container {
            padding-left: 3% !important;
            padding-right: 3% !important;
        }
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 4% !important;
            padding-right: 4% !important;
        }
    }

    /* Top Application Bar */
    .tl-top-navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.85rem 0;
        margin-bottom: 1.75rem;
        border-bottom: 1px solid #1a2233;
        width: 100%;
    }
    .tl-nav-left {
        display: flex;
        align-items: center;
        gap: 0.95rem;
    }
    .tl-nav-brand {
        display: flex;
        align-items: center;
        gap: 0.55rem;
    }
    .tl-nav-brand-title {
        font-size: 1.25rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f8fafc;
    }
    .tl-nav-tagline {
        font-size: 0.85rem;
        font-weight: 500;
        color: #64748b;
        padding-left: 0.85rem;
        border-left: 1px solid #1e293b;
    }
    .tl-nav-status {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding-left: 0.85rem;
        border-left: 1px solid #1e293b;
        font-size: 0.78rem;
        color: #94a3b8;
    }
    .tl-status-dot {
        width: 7px;
        height: 7px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }
    .tl-nav-right-pill {
        font-size: 0.75rem;
        font-weight: 500;
        color: #94a3b8;
        padding: 0.25rem 0.75rem;
        background-color: #111622;
        border: 1px solid #1e293b;
        border-radius: 9999px;
        letter-spacing: 0.02em;
    }

    /* Hero / Intro Section */
    .tl-hero-section {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.6rem;
        gap: 2rem;
        width: 100%;
    }
    .tl-hero-left {
        flex: 1;
    }
    .tl-hero-heading {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: #f8fafc;
        margin: 0 0 0.35rem 0;
        line-height: 1.2;
    }
    .tl-hero-subtext {
        font-size: 0.96rem;
        color: #94a3b8;
        margin: 0;
        max-width: 720px;
        line-height: 1.5;
    }
    .tl-hero-right {
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        gap: 0.45rem;
    }
    .tl-supported-title {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #64748b;
        text-transform: uppercase;
    }
    .tl-supported-types {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .tl-type-pill {
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: #94a3b8;
        background-color: #121824;
        border: 1px solid #1f293d;
        padding: 0.25rem 0.65rem;
        border-radius: 4px;
    }

    @media (max-width: 900px) {
        .tl-hero-section {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
        }
        .tl-hero-right {
            align-items: flex-start;
        }
    }

    /* Main Verification Workspace Container */
    .tl-workspace-card {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 10px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        width: 100%;
    }
    .tl-workspace-header {
        margin-bottom: 1.25rem;
    }
    .tl-workspace-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #f8fafc;
        letter-spacing: -0.01em;
        margin-bottom: 0.2rem;
    }
    .tl-workspace-desc {
        font-size: 0.88rem;
        color: #94a3b8;
    }

    /* Mode Selector Buttons Styling */
    div.st-key-mode_msg button, div.st-key-mode_url button, div.st-key-mode_notice button {
        width: 100% !important;
        height: auto !important;
        min-height: 84px !important;
        padding: 1.1rem 1.35rem !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 8px !important;
        transition: all 0.15s ease !important;
    }
    div.st-key-mode_msg button span[data-testid="stIconMaterial"],
    div.st-key-mode_url button span[data-testid="stIconMaterial"],
    div.st-key-mode_notice button span[data-testid="stIconMaterial"] {
        font-size: 1.35rem !important;
        color: #3b82f6 !important;
        margin-bottom: 0.25rem !important;
    }
    div.st-key-mode_msg button strong,
    div.st-key-mode_url button strong,
    div.st-key-mode_notice button strong {
        font-size: 0.98rem !important;
        font-weight: 600 !important;
        display: block !important;
        margin-bottom: 0.2rem !important;
    }
    div.st-key-mode_msg button p,
    div.st-key-mode_url button p,
    div.st-key-mode_notice button p {
        font-size: 0.84rem !important;
        font-weight: 400 !important;
        margin: 0 !important;
        line-height: 1.4 !important;
    }

    /* Inactive Mode Cards */
    div.st-key-mode_msg button[kind="secondary"],
    div.st-key-mode_url button[kind="secondary"],
    div.st-key-mode_notice button[kind="secondary"] {
        background-color: #121824 !important;
        border: 1px solid #1f293d !important;
    }
    div.st-key-mode_msg button[kind="secondary"] strong,
    div.st-key-mode_url button[kind="secondary"] strong,
    div.st-key-mode_notice button[kind="secondary"] strong {
        color: #e2e8f0 !important;
    }
    div.st-key-mode_msg button[kind="secondary"] p,
    div.st-key-mode_url button[kind="secondary"] p,
    div.st-key-mode_notice button[kind="secondary"] p {
        color: #94a3b8 !important;
    }
    div.st-key-mode_msg button[kind="secondary"]:hover,
    div.st-key-mode_url button[kind="secondary"]:hover,
    div.st-key-mode_notice button[kind="secondary"]:hover {
        background-color: #172030 !important;
        border-color: #2c3c58 !important;
    }

    /* Active Mode Cards: TrustLens Blue Accent */
    div.st-key-mode_msg button[kind="primary"],
    div.st-key-mode_url button[kind="primary"],
    div.st-key-mode_notice button[kind="primary"] {
        background-color: rgba(37, 99, 235, 0.09) !important;
        border: 1px solid #3b82f6 !important;
        box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.25) !important;
    }
    div.st-key-mode_msg button[kind="primary"] strong,
    div.st-key-mode_url button[kind="primary"] strong,
    div.st-key-mode_notice button[kind="primary"] strong {
        color: #ffffff !important;
    }
    div.st-key-mode_msg button[kind="primary"] p,
    div.st-key-mode_url button[kind="primary"] p,
    div.st-key-mode_notice button[kind="primary"] p {
        color: #cbd5e1 !important;
    }

    /* Input Section Inside Workspace */
    .tl-input-wrapper {
        margin-top: 1.5rem;
        padding-top: 1.35rem;
        border-top: 1px solid #1a2233;
        width: 100%;
    }
    .tl-input-header {
        margin-bottom: 0.75rem;
    }
    .tl-input-title {
        font-size: 0.98rem;
        font-weight: 600;
        color: #f8fafc;
        margin-bottom: 0.15rem;
    }
    .tl-input-desc {
        font-size: 0.85rem;
        color: #94a3b8;
    }

    /* Textarea & Inputs: Wide and Comfortable */
    .stTextArea textarea, .stTextInput input {
        background-color: #0c1018 !important;
        color: #f8fafc !important;
        border: 1px solid #1f293d !important;
        border-radius: 6px !important;
        font-size: 0.94rem !important;
        line-height: 1.55 !important;
        padding: 0.85rem 1rem !important;
        width: 100% !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }

    /* File Uploader */
    div[data-testid="stFileUploader"] section {
        background-color: #0c1018 !important;
        border: 1px dashed #222d42 !important;
        border-radius: 6px !important;
        padding: 1.75rem 1.25rem !important;
        width: 100% !important;
    }
    .tl-formats-hint {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 0.45rem;
    }

    /* Primary Action: Analyze Button */
    div.st-key-btn_analyze_action > button {
        background-color: #2563eb !important;
        border: 1px solid #1d4ed8 !important;
        color: #ffffff !important;
        font-size: 0.98rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em !important;
        padding: 0.8rem 1.75rem !important;
        border-radius: 6px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.25) !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
        margin-top: 0.85rem !important;
        width: 100% !important;
    }
    div.st-key-btn_analyze_action > button:hover {
        background-color: #1d4ed8 !important;
        border-color: #1e40af !important;
    }
    div.st-key-btn_analyze_action > button:active {
        background-color: #1e40af !important;
    }

    /* "How TrustLens Checks" Pipeline Bar */
    .tl-pipeline-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #0e1420;
        border: 1px solid #1a2233;
        border-radius: 8px;
        padding: 0.95rem 2rem;
        margin-bottom: 1.75rem;
        width: 100%;
    }
    .tl-pipeline-step {
        display: flex;
        align-items: center;
        gap: 0.85rem;
    }
    .tl-step-index {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.85rem;
        font-weight: 700;
        color: #3b82f6;
    }
    .tl-step-text {
        display: flex;
        flex-direction: column;
    }
    .tl-step-label {
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #cbd5e1;
    }
    .tl-step-detail {
        font-size: 0.84rem;
        color: #64748b;
    }
    .tl-pipeline-connector {
        display: flex;
        align-items: center;
        color: #334155;
    }

    @media (max-width: 800px) {
        .tl-pipeline-bar {
            flex-direction: column;
            align-items: flex-start;
            gap: 1rem;
            padding: 1.25rem;
        }
        .tl-pipeline-connector {
            display: none;
        }
    }

    /* Tasteful Empty State */
    .tl-empty-state {
        background-color: #0e1420;
        border: 1px solid #1a2233;
        border-radius: 8px;
        padding: 2.75rem 2rem;
        text-align: center;
        width: 100%;
    }
    .tl-empty-icon {
        margin-bottom: 0.75rem;
        color: #475569;
    }
    .tl-empty-title {
        font-size: 0.98rem;
        font-weight: 600;
        color: #cbd5e1;
        margin-bottom: 0.3rem;
    }
    .tl-empty-desc {
        font-size: 0.85rem;
        color: #64748b;
        max-width: 500px;
        margin: 0 auto;
        line-height: 1.45;
    }

    /* Trust Report Styles */
    .tl-report-wrapper {
        margin-top: 0.5rem;
        width: 100%;
    }
    .tl-report-supertitle {
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.75rem;
    }

    /* Verdict & Risk Banner: Balanced 2-Column Desktop Grid */
    .tl-verdict-banner {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 8px;
        padding: 1.6rem 2rem;
        margin-bottom: 1.25rem;
        width: 100%;
    }
    .tl-verdict-grid {
        display: grid;
        grid-template-columns: minmax(280px, 360px) 1fr;
        gap: 2.5rem;
        align-items: flex-start;
    }
    .tl-verdict-left-col {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .tl-verdict-right-col {
        border-left: 1px solid #1a2233;
        padding-left: 2.5rem;
        display: flex;
        flex-direction: column;
    }
    .tl-micro-label {
        font-size: 0.74rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.2rem;
    }
    .tl-verdict-title {
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f8fafc;
        line-height: 1.2;
    }
    .tl-verdict-risk-row {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        margin-top: 0.25rem;
    }
    .tl-risk-pill {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.9rem;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }
    .tl-verdict-summary-text {
        font-size: 0.96rem;
        color: #cbd5e1;
        line-height: 1.6;
        margin-top: 0.3rem;
    }

    @media (max-width: 900px) {
        .tl-verdict-grid {
            grid-template-columns: 1fr;
            gap: 1.25rem;
        }
        .tl-verdict-right-col {
            border-left: none;
            padding-left: 0;
            border-top: 1px solid #1a2233;
            padding-top: 1rem;
        }
    }

    /* Section Cards */
    .tl-card {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 8px;
        padding: 1.35rem 1.6rem;
        height: 100%;
        width: 100%;
    }
    .tl-card-header {
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 0.75rem;
    }

    /* Red Flags List */
    .tl-bullet-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    .tl-bullet-item {
        font-size: 0.92rem;
        color: #cbd5e1;
        line-height: 1.5;
        padding: 0.4rem 0;
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
    }
    .tl-bullet-flag {
        color: #ef4444;
        font-weight: bold;
    }

    /* Evidence Key-Value Table */
    .tl-evidence-table {
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
        margin-top: 0.2rem;
        width: 100%;
    }
    .tl-evidence-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #161f2e;
        font-size: 0.92rem;
    }
    .tl-evidence-row:last-child {
        border-bottom: none;
    }
    .tl-evidence-key {
        color: #94a3b8;
        font-weight: 500;
    }
    .tl-evidence-val {
        color: #f8fafc;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        font-size: 0.86rem;
        background-color: #0c1018;
        padding: 0.2rem 0.65rem;
        border-radius: 4px;
        border: 1px solid #1a2233;
    }

    /* What Changed Section */
    .tl-diff-container {
        background-color: #101622;
        border: 1px solid #1a2233;
        border-radius: 8px;
        padding: 1.35rem 1.6rem;
        margin-top: 1.25rem;
        width: 100%;
    }
    .tl-diff-subtext {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 0.85rem;
    }
    .tl-diff-grid {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }
    .tl-diff-card {
        background-color: #0c1018;
        border: 1px solid #1a2233;
        border-radius: 6px;
        padding: 1rem 1.25rem;
    }
    .tl-diff-title {
        font-size: 0.86rem;
        font-weight: 600;
        color: #e2e8f0;
        margin-bottom: 0.5rem;
    }
    .tl-diff-columns {
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        gap: 1rem;
        font-size: 0.88rem;
    }
    .tl-diff-col-box {
        padding: 0.55rem 0.85rem;
        border-radius: 4px;
        line-height: 1.45;
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
        padding: 0.1rem 0.35rem;
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
            gap: 0.5rem;
        }
        .tl-diff-arrow-icon {
            display: none;
        }
    }

    /* Recommended Next Action Card */
    .tl-action-box {
        background-color: #0d1624;
        border: 1px solid #1e3a5f;
        border-left: 3px solid #3b82f6;
        border-radius: 6px;
        padding: 1.25rem 1.6rem;
        margin-top: 1.25rem;
        width: 100%;
    }
    .tl-action-title {
        font-size: 0.76rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #60a5fa;
        margin-bottom: 0.4rem;
    }
    .tl-action-content {
        font-size: 0.96rem;
        color: #e2e8f0;
        line-height: 1.5;
    }

    /* Secondary Reset Button */
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
# Mock Backend Integration Interface
# NOTE: Replace these functions with backend/AI logic when ready.
# ==============================================================================
def analyze_message(text: str) -> dict:
    """Mock analysis for suspicious text or forwarded messages."""
    text_lower = (text or "").lower()

    if "safe" in text_lower or "official" in text_lower:
        return {
            "verdict": "Verified",
            "risk_level": "Low",
            "summary": "This message originates from an authorized service routing format and does not request credentials, OTPs, or immediate funds.",
            "red_flags": [],
            "evidence": [
                "Sender routing: Official shortcode",
                "Link safety: Clean destination",
                "Linguistic tone: Informational",
            ],
            "what_changed": [],
            "next_action": "No immediate risk detected. Standard digital caution applies.",
        }
    elif "unknown" in text_lower:
        return {
            "verdict": "Unable to Verify",
            "risk_level": "Indeterminate",
            "summary": "Insufficient verifiable context or corroborating signals to establish authenticity with high confidence.",
            "red_flags": [
                "Sender identity cannot be conclusively corroborated against registry data",
            ],
            "evidence": [
                "Telemetry records: Insufficient data",
                "Threat index match: None found",
            ],
            "what_changed": [],
            "next_action": "Do not act on requests until the source can be verified independently via official phone or website.",
        }
    else:
        return {
            "verdict": "Suspicious",
            "risk_level": "High",
            "summary": "This content contains several signals associated with a potentially fraudulent offer.",
            "red_flags": [
                "Requests an upfront payment or immediate credential submission",
                "Suspicious domain pattern masquerading as institutional portal",
                "No matching official source found in verified registry",
            ],
            "evidence": [
                "Domain age: 9 days",
                "Source match: Not found",
                "URL pattern: Suspicious",
            ],
            "what_changed": [],
            "next_action": "Do not make the payment until the offer has been independently verified.",
        }


def analyze_url(url: str) -> dict:
    """Mock analysis for suspicious URLs or links."""
    url_lower = (url or "").lower()

    if "google.com" in url_lower or "safe" in url_lower or "github.com" in url_lower:
        return {
            "verdict": "Verified",
            "risk_level": "Low",
            "summary": "The analyzed domain is well-established, holds valid organizational validation certificates, and shows no history of malicious activity.",
            "red_flags": [],
            "evidence": [
                "Domain age: > 5 years",
                "SSL certificate: Valid EV Certificate",
                "Reputation score: Clean registry",
            ],
            "what_changed": [],
            "next_action": "This link appears authentic. Maintain standard secure browsing habits.",
        }
    elif "unknown" in url_lower:
        return {
            "verdict": "Unable to Verify",
            "risk_level": "Indeterminate",
            "summary": "The destination URL has insufficient historical telemetry data and cannot be corroborated against existing reputation indices.",
            "red_flags": [
                "Domain lacks sufficient historical traffic telemetry",
            ],
            "evidence": [
                "Registration: Under 30 days",
                "Threat feed match: Unrecorded",
            ],
            "what_changed": [],
            "next_action": "Exercise caution before entering any personal data or credentials on this website.",
        }
    else:
        return {
            "verdict": "High Risk",
            "risk_level": "High",
            "summary": "The analyzed URL exhibits several deceptive indicators, including domain typo-squatting and suspicious registration age.",
            "red_flags": [
                "Recently registered domain with no established web reputation",
                "Domain name imitates a recognized portal with subtle character substitution",
                "Target destination initiates multiple unverified redirects",
            ],
            "evidence": [
                "Domain age: 9 days",
                "Source match: Not found",
                "URL pattern: Suspicious",
            ],
            "what_changed": [],
            "next_action": "Do not visit this URL or submit any credentials. Close any browser windows opened from this link.",
        }


def analyze_notice(image) -> dict:
    """Mock analysis for notices, circulars, and document images."""
    return {
        "verdict": "Suspicious",
        "risk_level": "High",
        "summary": "The submitted notice shows signs of layout tampering, altered application deadlines, and unauthorized beneficiary accounts.",
        "red_flags": [
            "Application deadline modified relative to official circular",
            "Department seal shows compression artifacts and resolution mismatch",
            "Payment beneficiary address redirected to private account",
        ],
        "evidence": [
            "Emblem resolution: 72 DPI (Standard is 300 DPI)",
            "Typography match: 3 mismatched fonts detected",
            "Dispatch registry: Not found in public gazette",
        ],
        "what_changed": [
            {
                "item": "Application deadline",
                "original": "Application deadline: 15 October",
                "forwarded": "Application deadline: 10 October",
                "highlight": "10 October",
            },
            {
                "item": "Payment beneficiary",
                "original": "Payable to: Department Treasury Account",
                "forwarded": "Payable to: Private UPI verification link",
                "highlight": "Private UPI verification link",
            },
            {
                "item": "Header seal",
                "original": "Official high-resolution department seal",
                "forwarded": "Substituted with low-resolution web graphic",
                "highlight": "low-resolution web graphic",
            },
        ],
        "next_action": "Do not make the payment or share personal information until the offer has been independently verified.",
    }


# ==============================================================================
# Status Styling Helper
# ==============================================================================
def get_risk_style(risk_level: str, verdict: str) -> dict:
    """Returns restrained status indicators for verdict states."""
    risk_lower = (risk_level or "").lower()
    verdict_lower = (verdict or "").lower()

    if "high" in risk_lower or "critical" in risk_lower or "fraud" in verdict_lower:
        return {
            "badge_text": "HIGH RISK",
            "border_color": "#dc2626",
            "bg_color": "rgba(239, 68, 68, 0.12)",
            "text_color": "#f87171",
            "accent_bar": "#ef4444",
        }
    elif "medium" in risk_lower or "suspicious" in verdict_lower or "warn" in risk_lower:
        return {
            "badge_text": "MEDIUM RISK",
            "border_color": "#d97706",
            "bg_color": "rgba(245, 158, 11, 0.12)",
            "text_color": "#fbbf24",
            "accent_bar": "#f59e0b",
        }
    elif "low" in risk_lower or "verified" in verdict_lower or "safe" in risk_lower:
        return {
            "badge_text": "VERIFIED / LOW RISK",
            "border_color": "#059669",
            "bg_color": "rgba(16, 185, 129, 0.12)",
            "text_color": "#34d399",
            "accent_bar": "#10b981",
        }
    else:  # Unable to Verify / Indeterminate
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
    """Render compact product header bar aligned with wide layout."""
    st.markdown(
        """
        <div class="tl-top-navbar">
            <div class="tl-nav-left">
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
                    <span>Verification system ready</span>
                </div>
            </div>
            <div class="tl-nav-right">
                <span class="tl-nav-right-pill">Local checks + AI</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    """Render compact intro section spanning wide layout intentionally."""
    st.markdown(
        """
        <div class="tl-hero-section">
            <div class="tl-hero-left">
                <h1 class="tl-hero-heading">Verify before you trust.</h1>
                <p class="tl-hero-subtext">
                    Check suspicious messages, links and notices before you act or share them. TrustLens analyzes the content and shows the evidence behind the result.
                </p>
            </div>
            <div class="tl-hero-right">
                <span class="tl-supported-title">Supported Verification</span>
                <div class="tl-supported-types">
                    <span class="tl-type-pill">MESSAGE</span>
                    <span class="tl-type-pill">LINK</span>
                    <span class="tl-type-pill">NOTICE</span>
                </div>
            </div>
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
                    <span class="tl-step-detail">Message, link or notice</span>
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
                    <span class="tl-step-detail">Local signals and source comparison</span>
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
                    <span class="tl-step-detail">Evidence, risk and next action</span>
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
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                    <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
            </div>
            <div class="tl-empty-title">Your verification report will appear here</div>
            <div class="tl-empty-desc">
                Select a verification mode, enter content above, and run analysis to view the risk evaluation.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_trust_report(report_data: dict):
    """
    Render polished Trust Report component with visually connected wide sections:
    - Report Header & Verdict / Summary Grid (Side-by-Side across top banner)
    - Red Flags & Evidence Table (Side-by-Side)
    - What Changed (Conditionally rendered)
    - Recommended Next Action
    """
    verdict = report_data.get("verdict", "Under Review")
    risk_level = report_data.get("risk_level", "Unknown")
    summary = report_data.get("summary", "No summary available.")
    red_flags = report_data.get("red_flags", [])
    evidence = report_data.get("evidence", [])
    what_changed = report_data.get("what_changed", [])
    next_action = report_data.get("next_action", "No specific action recorded.")

    style = get_risk_style(risk_level, verdict)

    st.markdown('<div class="tl-report-wrapper">', unsafe_allow_html=True)
    st.markdown('<div class="tl-report-supertitle">TRUST REPORT</div>', unsafe_allow_html=True)

    # 1. Verdict & Summary Grid Banner
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
                    </div>
                </div>
                <div class="tl-verdict-right-col">
                    <div class="tl-micro-label">SUMMARY</div>
                    <div class="tl-verdict-summary-text">
                        {summary}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2. Red Flags & 3. Evidence Table (Side by Side in wide layout)
    col_flags, col_evidence = st.columns(2)

    with col_flags:
        flags_html = ""
        if red_flags:
            for item in red_flags:
                flags_html += f'<li class="tl-bullet-item"><span class="tl-bullet-flag">•</span><span>{item}</span></li>'
        else:
            flags_html = '<li class="tl-bullet-item" style="color: #94a3b8;">No distinct red flags detected.</li>'

        st.markdown(
            f"""
            <div class="tl-card">
                <div class="tl-card-header">RED FLAGS</div>
                <ul class="tl-bullet-list">
                    {flags_html}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_evidence:
        evidence_rows = ""
        if evidence:
            for item in evidence:
                if ":" in item:
                    key, val = item.split(":", 1)
                    evidence_rows += f"""
                    <div class="tl-evidence-row">
                        <span class="tl-evidence-key">{key.strip()}</span>
                        <span class="tl-evidence-val">{val.strip()}</span>
                    </div>
                    """
                else:
                    evidence_rows += f"""
                    <div class="tl-evidence-row">
                        <span class="tl-evidence-key">Signal</span>
                        <span class="tl-evidence-val">{item.strip()}</span>
                    </div>
                    """
        else:
            evidence_rows = '<div style="color: #94a3b8; font-size: 0.88rem; padding: 0.4rem 0;">No technical telemetry recorded.</div>'

        st.markdown(
            f"""
            <div class="tl-card">
                <div class="tl-card-header">EVIDENCE</div>
                <div class="tl-evidence-table">
                    {evidence_rows}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 4. What Changed (Only shown when relevant)
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
                <div class="tl-diff-subtext">Discrepancies identified during document/notice verification:</div>
                <div class="tl-diff-grid">
                    {diff_cards_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # 5. Recommended Next Action
    st.markdown(
        f"""
        <div class="tl-action-box">
            <div class="tl-action-title">RECOMMENDED NEXT ACTION</div>
            <div class="tl-action-content">{next_action}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# Main Application Flow
# ==============================================================================
def main():
    # Session state setup
    if "selected_mode" not in st.session_state:
        st.session_state["selected_mode"] = "Message"
    if "has_analyzed" not in st.session_state:
        st.session_state["has_analyzed"] = False
        st.session_state["report_data"] = None

    # 1. Product Header (Aligned with wide layout)
    render_header()

    # 2. Product Intro & Hero (Wide composition)
    render_hero()

    # 3. Main Verification Workspace Card (Wide format)
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

    # Verification Mode Selectable Product Cards (3 balanced wide columns)
    col_msg, col_url, col_notice = st.columns(3)

    with col_msg:
        if st.button(
            "**Message**  \nCheck forwarded messages and offers",
            key="mode_msg",
            icon=":material/chat:",
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
            "**URL**  \nInspect suspicious links and domains",
            key="mode_url",
            icon=":material/link:",
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
            "**Notice**  \nCompare notices and uploaded images",
            key="mode_notice",
            icon=":material/description:",
            use_container_width=True,
            type="primary" if st.session_state["selected_mode"] == "Notice" else "secondary",
        ):
            if st.session_state["selected_mode"] != "Notice":
                st.session_state["selected_mode"] = "Notice"
                st.session_state["has_analyzed"] = False
                st.session_state["report_data"] = None
                st.rerun()

    # Dynamic Input Area
    user_input = None
    current_mode = st.session_state["selected_mode"]

    st.markdown('<div class="tl-input-wrapper">', unsafe_allow_html=True)

    if current_mode == "Message":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Paste the message</div>
                <div class="tl-input-desc">Add the suspicious message, offer, email or forwarded content.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        user_input = st.text_area(
            "Suspicious message",
            placeholder="Paste suspicious text, email, or WhatsApp message here...",
            height=145,
            label_visibility="collapsed",
        )

    elif current_mode == "URL":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Enter the URL</div>
                <div class="tl-input-desc">Paste the link you want TrustLens to inspect.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        user_input = st.text_input(
            "Suspicious URL",
            placeholder="https://example.com/verify-account",
            label_visibility="collapsed",
        )

    elif current_mode == "Notice":
        st.markdown(
            """
            <div class="tl-input-header">
                <div class="tl-input-title">Upload a notice</div>
                <div class="tl-input-desc">Upload the notice or screenshot you want to verify.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        user_input = st.file_uploader(
            "Upload notice",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
            help="Supported formats: PNG · JPG · JPEG",
        )
        st.markdown('<div class="tl-formats-hint">Supported formats: PNG · JPG · JPEG</div>', unsafe_allow_html=True)

        if user_input is not None:
            st.image(
                user_input,
                caption="Uploaded notice preview",
                use_container_width=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # Primary Analyze Action
    analyze_clicked = st.button(
        "Analyze with TrustLens ➔",
        type="primary",
        key="btn_analyze_action",
        use_container_width=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)  # Close tl-workspace-card

    # 4. "How TrustLens Checks" Pipeline Bar
    render_pipeline_bar()

    # 5. Validation and Execution Logic
    if analyze_clicked:
        is_valid = True

        if current_mode == "Message":
            if not user_input or not user_input.strip():
                st.warning("Please enter a message to verify.")
                is_valid = False
        elif current_mode == "URL":
            if not user_input or not user_input.strip():
                st.warning("Please enter a URL to verify.")
                is_valid = False
        elif current_mode == "Notice":
            if user_input is None:
                st.warning("Please upload an image to verify.")
                is_valid = False

        if is_valid:
            with st.spinner("Analyzing your content..."):
                if current_mode == "Message":
                    report = analyze_message(user_input)
                elif current_mode == "URL":
                    report = analyze_url(user_input)
                else:
                    report = analyze_notice(user_input)

                st.session_state["report_data"] = report
                st.session_state["has_analyzed"] = True

    # 6. Trust Report or Empty State
    if st.session_state.get("has_analyzed") and st.session_state.get("report_data"):
        render_trust_report(st.session_state["report_data"])

        # Secondary Reset Action
        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        if st.button("Verify another item", key="btn_verify_another"):
            st.session_state["has_analyzed"] = False
            st.session_state["report_data"] = None
            st.rerun()
    else:
        render_empty_state()


if __name__ == "__main__":
    main()
