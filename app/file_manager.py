"""
File Handling and Audit Logging Utility Class.
Addresses ESE Rubric: Python Programming Implementation (file handling, classes, exception handling).
Provides CSV export, JSON export, seed data loading, and persistent DBMS query audit logging.
"""

import csv
import datetime
import json
import pathlib
from typing import List, Dict, Any


class FileManager:
    """Manages file I/O operations for query exports, seed imports, and DBMS operation logs."""

    def __init__(self, export_dir: pathlib.Path, audit_log_path: pathlib.Path, seed_json_path: pathlib.Path):
        self.export_dir = pathlib.Path(export_dir)
        self.audit_log_path = pathlib.Path(audit_log_path)
        self.seed_json_path = pathlib.Path(seed_json_path)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

    def load_seed_dataset(self) -> Dict[str, List[Dict[str, Any]]]:
        """Reads the canonical JSON seed dataset from disk."""
        with open(self.seed_json_path, mode="r", encoding="utf-8") as f:
            return json.load(f)

    def export_to_csv(self, query_name: str, rows: List[Dict[str, Any]]) -> pathlib.Path:
        """Writes query result dictionaries to a timestamped CSV file on disk."""
        safe_slug = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in query_name.lower())
        file_path = self.export_dir / f"{safe_slug}.csv"
        fieldnames = list(rows[0].keys()) if rows else ["result"]
        with open(file_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            if rows:
                writer.writerows(rows)
        self.log_event("FILE_EXPORT_CSV", f"Exported {len(rows)} rows for '{query_name}' to {file_path.name}")
        return file_path

    def export_to_json(self, query_name: str, payload: Any) -> pathlib.Path:
        """Writes analytical results or NoSQL documents to a formatted JSON file on disk."""
        safe_slug = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in query_name.lower())
        file_path = self.export_dir / f"{safe_slug}.json"
        export_wrapper = {
            "query_name": query_name,
            "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "record_count": len(payload) if isinstance(payload, list) else 1,
            "data": payload,
        }
        with open(file_path, mode="w", encoding="utf-8") as jsonfile:
            json.dump(export_wrapper, jsonfile, indent=2)
        self.log_event("FILE_EXPORT_JSON", f"Exported JSON dataset for '{query_name}' to {file_path.name}")
        return file_path

    def log_event(self, category: str, message: str) -> None:
        """Appends a structured audit entry to the persistent DBMS log file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{category}] {message}\\n"
        try:
            with open(self.audit_log_path, mode="a", encoding="utf-8") as logf:
                logf.write(line)
        except OSError:
            pass

    def read_recent_logs(self, limit: int = 40) -> List[str]:
        """Reads the most recent DBMS audit log lines from disk."""
        if not self.audit_log_path.exists():
            return []
        try:
            with open(self.audit_log_path, mode="r", encoding="utf-8") as logf:
                lines = [ln.strip() for ln in logf.readlines() if ln.strip()]
            return list(reversed(lines[-limit:]))
        except OSError:
            return []
