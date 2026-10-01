"""
QR Verification Receipt generator for TrustLens.
Generates a scannable QR code and structured receipt for each verification report.
"""
import io
import os
import uuid
import datetime
from typing import Optional, Tuple


def _get_base_url() -> str:
    """Reads TRUSTLENS_PUBLIC_BASE_URL from environment; falls back to a local placeholder."""
    url = os.environ.get("TRUSTLENS_PUBLIC_BASE_URL", "").rstrip("/")
    return url or "https://trustlens.app"


def generate_verification_id() -> str:
    """Generates a short unique verification ID."""
    return "TL-" + str(uuid.uuid4()).upper().replace("-", "")[:12]


def generate_qr_receipt(
    verification_id: str,
    verdict: str,
    risk_level: str,
    risk_score: int,
    summary: str,
    timestamp: Optional[str] = None,
) -> Tuple[dict, bytes]:
    """
    Generates a verification receipt dict and a QR code PNG as bytes.

    The QR code encodes the verification URL, NOT the entire report.

    Args:
        verification_id (str): Unique verification reference ID.
        verdict (str): Analysis verdict (SAFE, SUSPICIOUS, etc.).
        risk_level (str): Risk level (LOW, MEDIUM, HIGH).
        risk_score (int): Integer risk score 0-100.
        summary (str): Short summary string.
        timestamp (str, optional): ISO timestamp string. Defaults to current UTC time.

    Returns:
        Tuple[dict, bytes]:
            - receipt (dict): Structured receipt metadata.
            - qr_png_bytes (bytes): QR code image as PNG bytes.
    """
    if not timestamp:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    base_url = _get_base_url()
    verification_url = f"{base_url}/report/{verification_id}"

    receipt = {
        "product": "TrustLens",
        "verification_id": verification_id,
        "verification_url": verification_url,
        "verdict": (verdict or "UNKNOWN").upper(),
        "risk_level": (risk_level or "UNKNOWN").upper(),
        "risk_score": risk_score,
        "timestamp": timestamp,
        "summary": summary or "Verification completed.",
    }

    # Generate QR code (encodes only the verification URL)
    qr_bytes = b""
    try:
        import qrcode  # type: ignore
        from qrcode.image.pure import PyPNGImage  # type: ignore

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=3,
        )
        qr.add_data(verification_url)
        qr.make(fit=True)

        # Try Pillow image (preferred — richer rendering)
        try:
            from PIL import Image  # type: ignore
            img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            qr_bytes = buf.getvalue()
        except Exception:
            # Fall back to pure-python PNG if Pillow is unavailable
            img = qr.make_image(image_factory=PyPNGImage)
            buf = io.BytesIO()
            img.save(buf)
            qr_bytes = buf.getvalue()
    except Exception as e:
        # If qrcode itself fails unexpectedly, return empty bytes
        qr_bytes = b""

    return receipt, qr_bytes
