import os
import hashlib
import io
from pathlib import Path
from typing import Optional, Dict, Any

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import qrcode
from PIL import Image

from app.config import STORAGE_DIR, BASE_URL


def generate_qr_code(data: str) -> io.BytesIO:
    """Generate a QR code image stream in PNG format."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=4,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)
    return img_byte_arr


def draw_certificate_template(
    c: canvas.Canvas,
    width: float,
    height: float,
    recipient_name: str,
    title: str,
    event_name: str,
    issue_date: str,
    certificate_id: str,
    verification_url: str,
    custom_attributes: Optional[Dict[str, Any]] = None
):
    """Draw a rich, elegant certificate design on a ReportLab landscape canvas."""
    # 1. Background & Outer Decorative Border
    c.setFillColor(colors.HexColor("#FAFAFC"))
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # Outer Border Frame (Gold & Deep Navy)
    c.setStrokeColor(colors.HexColor("#1E293B")) # Deep Navy
    c.setLineWidth(5)
    c.rect(20, 20, width - 40, height - 40)
    
    c.setStrokeColor(colors.HexColor("#D97706")) # Gold accent line
    c.setLineWidth(2)
    c.rect(26, 26, width - 52, height - 52)
    
    # Corner Accents
    corner_size = 20
    c.setFillColor(colors.HexColor("#D97706"))
    # Top-Left
    c.rect(20, height - 20 - corner_size, corner_size, corner_size, fill=True, stroke=False)
    # Top-Right
    c.rect(width - 20 - corner_size, height - 20 - corner_size, corner_size, corner_size, fill=True, stroke=False)
    # Bottom-Left
    c.rect(20, 20, corner_size, corner_size, fill=True, stroke=False)
    # Bottom-Right
    c.rect(width - 20 - corner_size, 20, corner_size, corner_size, fill=True, stroke=False)

    # 2. Header / Organization Brand
    c.setFillColor(colors.HexColor("#64748B"))
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2.0, height - 70, "INTERNATIONAL ACADEMY OF EXCELLENCE")
    
    # Ribbon / Decorative Line
    c.setStrokeColor(colors.HexColor("#CBD5E1"))
    c.setLineWidth(1)
    c.line(width / 2.0 - 150, height - 85, width / 2.0 + 150, height - 85)

    # 3. Main Certificate Title
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2.0, height - 125, title.upper())

    # 4. Presentation Line
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2.0, height - 165, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

    # 5. Recipient Name (Prominent & Elegant)
    c.setFillColor(colors.HexColor("#1E3A8A")) # Royal Navy Blue
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2.0, height - 215, recipient_name)

    # Underline for Recipient Name
    c.setStrokeColor(colors.HexColor("#D97706"))
    c.setLineWidth(2)
    c.line(width / 2.0 - 180, height - 225, width / 2.0 + 180, height - 225)

    # 6. Description & Event Name
    c.setFillColor(colors.HexColor("#475569"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2.0, height - 260, "for successfully completing requirements and demonstrating excellence in")

    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2.0, height - 295, event_name)

    # Custom attributes rendering if provided (e.g. Grade, Track, Hours)
    if custom_attributes:
        attr_str = " | ".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in custom_attributes.items() if v])
        if attr_str:
            c.setFillColor(colors.HexColor("#64748B"))
            c.setFont("Helvetica-Oblique", 11)
            c.drawCentredString(width / 2.0, height - 320, attr_str)

    # 7. Footer Info (Date, Signature, QR Code)
    # Issue Date (Left)
    c.setFillColor(colors.HexColor("#334155"))
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, 95, f"Date of Issue: {issue_date}")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawString(60, 80, f"Certificate ID: {certificate_id}")

    # Signature Line (Center-Right)
    sig_x = width - 240
    c.setStrokeColor(colors.HexColor("#94A3B8"))
    c.setLineWidth(1)
    c.line(sig_x, 100, sig_x + 160, 100)
    
    c.setFillColor(colors.HexColor("#0F172A"))
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(sig_x + 80, 85, "Authorized Signatory")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#64748B"))
    c.drawCentredString(sig_x + 80, 72, "Director of Certification")

    # QR Code (Bottom Left or Bottom Right)
    try:
        qr_img_stream = generate_qr_code(verification_url)
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(qr_img_stream)
        c.drawImage(img_reader, width - 110, 45, width=55, height=55)
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.HexColor("#94A3B8"))
        c.drawCentredString(width - 82, 36, "Scan to verify")
    except Exception as e:
        # Gracefully handle QR code rendering error if any
        pass


def generate_certificate_pdf(
    certificate_id: str,
    recipient_name: str,
    title: str,
    event_name: str,
    issue_date: str,
    custom_attributes: Optional[Dict[str, Any]] = None
) -> tuple[str, str]:
    """
    Generates a PDF certificate file and returns (file_path, checksum).
    Raises exception if inputs are invalid or rendering fails.
    """
    if not recipient_name or not recipient_name.strip():
        raise ValueError("Recipient name is required for certificate generation.")

    # File destination
    file_filename = f"cert_{certificate_id}.pdf"
    file_path = os.path.join(STORAGE_DIR, file_filename)
    
    verification_url = f"{BASE_URL}/api/v1/certificates/verify/{certificate_id}"

    # Setup canvas (Landscape A4: 841.89 x 595.27 pt)
    page_width, page_height = landscape(A4)
    
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    
    draw_certificate_template(
        c=c,
        width=page_width,
        height=page_height,
        recipient_name=recipient_name,
        title=title,
        event_name=event_name,
        issue_date=issue_date,
        certificate_id=certificate_id,
        verification_url=verification_url,
        custom_attributes=custom_attributes
    )
    
    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Save to disk
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    # Compute SHA-256 checksum
    checksum = hashlib.sha256(pdf_bytes).hexdigest()

    return file_path, checksum
