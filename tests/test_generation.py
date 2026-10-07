import os
import pytest
from app.services.pdf_generator import generate_certificate_pdf

def test_pdf_generation_service():
    certificate_id = "test-uuid-12345"
    recipient_name = "Charlie Brown"
    title = "Certificate of Completion"
    event_name = "Cloud Native Security"
    issue_date = "2026-10-07"
    custom_attributes = {"Grade": "Distinction"}

    file_path, checksum = generate_certificate_pdf(
        certificate_id=certificate_id,
        recipient_name=recipient_name,
        title=title,
        event_name=event_name,
        issue_date=issue_date,
        custom_attributes=custom_attributes
    )

    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) > 1000
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA-256 length

    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)


def test_pdf_generation_missing_name_fails():
    with pytest.raises(ValueError):
        generate_certificate_pdf(
            certificate_id="test-fail",
            recipient_name="",
            title="Title",
            event_name="Event",
            issue_date="2026-10-07"
        )
