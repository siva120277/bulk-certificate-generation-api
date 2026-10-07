import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Storage directory for generated certificates
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR}/certificates.db")
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL", f"sqlite:///{BASE_DIR}/certificates.db")

# Base URL for generated certificate verification links
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

APP_NAME = "Bulk Certificate Generation API"
API_V1_STR = "/api/v1"
