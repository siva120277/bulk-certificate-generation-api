# Bulk Certificate Generation Backend API

A high-performance, resilient backend API built with **Python 3.12**, **FastAPI**, **SQLAlchemy**, and **ReportLab**. Designed to accept bulk certificate generation requests for large events or courses, track real-time job progress, isolate individual rendering failures, and serve generated PDF certificates.

---

## 🌟 Key Features

- **Bulk Certificate Generation**: Submit a single HTTP request containing dozens or hundreds of recipient details.
- **Asynchronous Background Processing**: Non-blocking `202 Accepted` response for immediate client feedback while processing generation jobs in the background.
- **Partial Failure Resilience**: Errors encountered during the generation of a specific certificate are caught, logged, and marked as `FAILED` on the recipient record without interrupting or aborting valid certificates in the same job.
- **Native PDF Rendering**: Uses ReportLab to generate vector PDF certificates with custom styling, typography, verification QR code, and SHA-256 integrity checksums.
- **Real-Time Progress Tracking**: Pollable job metrics (`total`, `processed`, `successful`, `failed`, `percentage`).
- **Certificate Verification**: Built-in verification endpoint (`/api/v1/certificates/verify/{id}`) to validate certificate authenticity via QR code scanning.
- **Batch Download**: Download individual PDF files or an entire batch as a ZIP archive (`/api/v1/jobs/{job_id}/download-all`).
- **Interactive Web Dashboard**: Embedded dark-mode UI dashboard for easy visual testing, live status polling, and PDF preview.

---

## 🏗️ Tech Stack & Architecture

- **Language**: Python 3.12+
- **Framework**: FastAPI (Async API layer)
- **Database**: SQLite with SQLAlchemy 2.0 (Async ORM via `aiosqlite`)
- **PDF Engine**: ReportLab + QRCode + Pillow
- **Testing**: Pytest + `pytest-asyncio` + HTTPX

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
Ensure Python 3.12 or higher is installed on your system.

### 2. Clone / Open Project Directory
```bash
cd c:/Users/Lenovo/Documents/bulk
```

### 3. Create & Activate Virtual Environment
On Windows (PowerShell / CMD):
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

On Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Running the Application

Start the FastAPI server using Uvicorn:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Once running:
- **Interactive Web UI Dashboard**: `http://localhost:8000/`
- **OpenAPI / Swagger Documentation**: `http://localhost:8000/docs`
- **ReDoc API Documentation**: `http://localhost:8000/redoc`

---

## 🧪 Running Tests

Execute the automated test suite covering job creation, validation, PDF generation, partial failure resilience, and certificate retrieval:

```bash
python -m pytest -v
```

---

## 📖 API Usage Guide

### 1. Submit a Bulk Certificate Generation Request

**Endpoint**: `POST /api/v1/jobs`  
**Headers**: `Content-Type: application/json`

**Sample Request Body**:
```json
{
  "title": "Certificate of Completion",
  "event_name": "Full Stack FastAPI Engineering 2026",
  "issue_date": "2026-10-07",
  "recipients": [
    {
      "name": "Jane Doe",
      "email": "jane.doe@example.com",
      "custom_attributes": {
        "grade": "Distinction",
        "track": "Backend Engineering"
      }
    },
    {
      "name": "John Smith",
      "email": "john.smith@example.com",
      "custom_attributes": {
        "grade": "High Merit",
        "track": "DevOps"
      }
    }
  ]
}
```

**Response (`202 Accepted`)**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Certificate of Completion",
  "event_name": "Full Stack FastAPI Engineering 2026",
  "issue_date": "2026-10-07",
  "template_name": "default",
  "status": "PENDING",
  "progress": {
    "total": 2,
    "processed": 0,
    "successful": 0,
    "failed": 0,
    "percentage": 0.0
  },
  "created_at": "2026-10-07T18:45:00Z",
  "updated_at": "2026-10-07T18:45:00Z"
}
```

---

### 2. Check Job Progress & Results

**Endpoint**: `GET /api/v1/jobs/{job_id}`

**Sample Response**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Certificate of Completion",
  "event_name": "Full Stack FastAPI Engineering 2026",
  "status": "COMPLETED",
  "progress": {
    "total": 2,
    "processed": 2,
    "successful": 2,
    "failed": 0,
    "percentage": 100.0
  },
  "certificates": [
    {
      "id": "98765432-10ab-cdef-feab-098765432100",
      "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "recipient_name": "Jane Doe",
      "recipient_email": "jane.doe@example.com",
      "status": "SUCCESS",
      "error_message": null,
      "file_url": "/api/v1/certificates/98765432-10ab-cdef-feab-098765432100/download"
    }
  ]
}
```

---

### 3. Retrieve & Download Generated Certificate

- **Metadata Lookup**: `GET /api/v1/certificates/{certificate_id}`
- **Download PDF File**: `GET /api/v1/certificates/{certificate_id}/download`
- **Download All Certificates as ZIP**: `GET /api/v1/jobs/{job_id}/download-all`
- **Verify Certificate Authenticity**: `GET /api/v1/certificates/verify/{certificate_id}`

---

## 📐 Important Implementation & Design Decisions

1. **FastAPI + Async Architecture**:
   - Chosen for native async IO support, performance, standard OpenAPI auto-documentation, and Pydantic v2 data validation.

2. **Database Engine & Persistence**:
   - SQLite with `sqlalchemy.ext.asyncio` provides zero-friction setup out of the box while maintaining strict relational foreign key relationships (`jobs` -> `certificates`).

3. **Background Worker Engine**:
   - Implemented via non-blocking async task processing with real-time atomic database commits per item. This guarantees that status updates (`PENDING` -> `GENERATING` -> `SUCCESS`/`FAILED`) are immediately queryable via the status endpoint while batch generation is running.

4. **Failure Isolation & Resiliency**:
   - The PDF generation loop catches item-level exceptions (e.g., malformed custom data, rendering errors, or missing parameters). When an error occurs, the worker sets `Certificate.status = FAILED`, stores the error stack/message in `Certificate.error_message`, increments `failed_count`, and immediately continues processing the next recipient in line.
   - If at least 1 certificate succeeds and at least 1 fails, the job status transitions to `PARTIALLY_FAILED`, providing full transparency.

5. **ReportLab PDF Rendering**:
   - Native Python PDF generation ensures crisp vector quality, exact pixel layout control, QR code integration, and zero system binary dependency constraints (unlike wkhtmltopdf or PhantomJS).

---

## 🛠️ Project File Structure

```
bulk/
├── app/
│   ├── api/                    # API endpoints (jobs, certificates, router)
│   ├── models/                 # SQLAlchemy DB models (Job, Certificate)
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/               # PDF generator & async background worker
│   ├── static/                 # Web Dashboard (index.html)
│   ├── config.py               # Application configuration
│   ├── database.py             # Database engine & session setup
│   └── main.py                 # FastAPI application entry point
├── tests/                      # Pytest suite
│   ├── conftest.py
│   ├── test_jobs_api.py
│   ├── test_validation.py
│   ├── test_generation.py
│   ├── test_failure_handling.py
│   └── test_retrieval.py
├── storage/                    # Directory for generated PDF files
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```
