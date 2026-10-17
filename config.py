"""
Application Configuration Module.
Supports MySQL 8.0 (PyMySQL) and MongoDB (PyMongo) with automatic transparent
fallback to local SQLite and JSON Document Store so the app runs reliably in
any classroom or evaluation environment.
"""

import os
import pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent


class Config:
    """Base configuration with SQL, NoSQL, and file-handling settings."""

    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "sit-pune-dcds-lab-ese-2026-secret")
    APP_TITLE = "Water Access Inequality Analysis System"
    COURSE_INFO = "DCDS Lab ESE Miniproject | Symbiosis Institute of Technology, Pune"

    # MySQL 8.0 Connection Parameters
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "water_access_inequality")
    FORCE_SQLITE_FALLBACK = os.environ.get("FORCE_SQLITE_FALLBACK", "false").lower() == "true"

    # SQLite Fallback Path (used automatically when MySQL server is unreachable)
    SQLITE_DB_PATH = pathlib.Path(
        os.environ.get("SQLITE_DB_PATH", str(BASE_DIR / "data" / "water_access_inequality.db"))
    )

    # MongoDB Connection Parameters
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB = os.environ.get("MONGO_DB", "water_access_inequality")
    FORCE_MONGO_FALLBACK = os.environ.get("FORCE_MONGO_FALLBACK", "false").lower() == "true"

    # Local NoSQL Document Store Fallback Path
    NOSQL_FALLBACK_PATH = pathlib.Path(
        os.environ.get("NOSQL_FALLBACK_PATH", str(BASE_DIR / "data" / "nosql_document_store.json"))
    )

    # File Handling Paths (Seed Data, CSV/JSON Exports, Audit Logs)
    SEED_JSON_PATH = BASE_DIR / "data" / "seed_dataset.json"
    SCHEMA_SQL_PATH = BASE_DIR / "sql" / "schema.sql"
    SEED_SQL_PATH = BASE_DIR / "sql" / "seed_data.sql"
    EXPORT_DIR = BASE_DIR / "data" / "exports"
    AUDIT_LOG_PATH = BASE_DIR / "logs" / "dbms_audit.log"


class TestingConfig(Config):
    """Isolated configuration for automated unit and integration testing."""

    TESTING = True
    FORCE_SQLITE_FALLBACK = True
    FORCE_MONGO_FALLBACK = True
    SQLITE_DB_PATH = BASE_DIR / "data" / "test_water_access.db"
    NOSQL_FALLBACK_PATH = BASE_DIR / "data" / "test_nosql_store.json"
    AUDIT_LOG_PATH = BASE_DIR / "logs" / "test_dbms_audit.log"
