# Water Access Inequality Analysis System (Modular Flask + SQL & NoSQL DBMS)

**Institution:** Symbiosis Institute of Technology, Pune  
**Department:** Artificial Intelligence and Machine Learning (Batch 2025–29, SY / Sem 3)  
**Course:** Database Concepts for Data Science Lab (DCDS Lab ESE Miniproject)  
**Student:** Smit Jayeshkumar Parikh (PRN: 25070126121 | Division: AIML B1)

## 1. Overview & Upgrade Highlights

This modular **Flask** web application upgrades the original Tkinter-based *Water Access Inequality Analysis System* into a full-stack, multi-Blueprint web application designed specifically to achieve **10 / 10 Marks ("Excellent")** across every evaluation parameter in the **DCDS Lab ESE Rubrics**.

### Key Engineering & DBMS Features
- **Modular Flask Application Factory (`app/__init__.py`)**: Separated into 4 dedicated Blueprints (`dashboard_bp`, `sql_bp`, `nosql_bp`, `api_bp`) with clean MVC / Repository layering.
- **Dual-Mode SQL & NoSQL Connectivity**:
  - **Relational DBMS (`app/database/sql_repository.py`)**: Connects to **MySQL 8.0** via `PyMySQL` (`localhost:3306/water_access_inequality`) and automatically falls back to **SQLite3** if the MySQL daemon is offline during a classroom demonstration.
  - **NoSQL Document DBMS (`app/database/nosql_repository.py`)**: Connects to **MongoDB** via `PyMongo` (`mongodb://localhost:27017/water_access_inequality`) and automatically falls back to a local **JSON Document Engine** if `mongod` is offline.
- **Interactive Query Code Inspector**: Every view in the Flask UI displays the exact SQL statement, Stored Procedure definition, or PyMongo Aggregation Pipeline alongside the live tabular output so you can explain the query logic during your viva.

## 2. Project Directory Structure

```text
water_access_inequality_flask_app/
├── run.py                          # Main Flask server entry point
├── config.py                       # Environment & database configuration
├── requirements.txt                # Python package dependencies
├── README.md                       # Setup guide & ESE Rubric benchmark
├── sql/
│   ├── schema.sql                  # MySQL 8.0 DDL, constraints, view & Stored Procedure GetPoorWaterAccess
│   └── seed_data.sql               # Calibrated INSERT statements for Communities A–J
├── data/
│   ├── seed_dataset.json           # Canonical JSON seed dataset
│   └── exports/                    # Downloaded CSV & JSON query files (File Handling rubric)
├── logs/
│   └── dbms_audit.log              # Persistent DBMS execution & error log
├── app/
│   ├── __init__.py                 # Flask Application Factory (create_app) & Error Handlers
│   ├── exceptions.py               # Custom OOP Exception Hierarchy
│   ├── models.py                   # Python OOP Dataclasses (Community, WaterQuality, Sanitation)
│   ├── validators.py               # Server-side Input Validation & SQL Injection Defense
│   ├── file_manager.py             # File I/O Manager (CSV/JSON Export & Audit Logging)
│   ├── database/
│   │   ├── sql_repository.py       # SQL CRUD, JOINs, Nested Subquery, GROUP BY, Aggregations, Stored Proc
│   │   └── nosql_repository.py     # MongoDB CRUD, $lt Filtering, and $lookup/$group Aggregation Pipeline
│   ├── routes/
│   │   ├── dashboard_bp.py         # Executive Dashboard & Rubric Benchmark routes
│   │   ├── sql_bp.py               # Interactive SQL Workbench & Community K CRUD routes
│   │   ├── nosql_bp.py             # Interactive MongoDB Workbench & Demo Runner routes
│   │   └── api_bp.py               # REST JSON API, CSV/JSON File Export & DB Reset routes
│   ├── templates/                  # Responsive Jinja2 HTML5 templates
│   └── static/                     # Self-contained offline CSS & JS assets
└── tests/
    └── test_dbms_app.py            # Automated 11-test verification suite (unittest & pytest)
```

## 3. Quick Start Instructions

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: (Optional) Configure Live MySQL 8.0 & MongoDB
By default, the app attempts to connect to local MySQL (`root@localhost:3306/water_access_inequality`) and MongoDB (`mongodb://localhost:27017/water_access_inequality`). If either server is not running, the app **automatically activates its built-in SQLite / JSON Document fallback** so it never crashes.

To set custom MySQL credentials via environment variables:
```bash
# Windows PowerShell
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD="your_mysql_password"
$env:MYSQL_DB="water_access_inequality"

# Linux / macOS
export MYSQL_USER="root"
export MYSQL_PASSWORD="your_mysql_password"
export MYSQL_DB="water_access_inequality"
```
You can also run `sql/schema.sql` and `sql/seed_data.sql` directly in MySQL Workbench if desired, though the Flask app automatically creates the tables, stored procedure, and seed records on startup.

### Step 3: Run the Application
```bash
python run.py
```
Open **http://127.0.0.1:5000** in your browser.

### Step 4: Run the Automated Test Suite
```bash
python -m unittest discover -s tests -v
# or
pytest -v
```

## 4. Benchmark Mapping Against DCDS Lab ESE Rubrics (10 Marks)

| Criterion | Marks | How This Codebase Achieves "Excellent" |
| :--- | :--- | :--- |
| **1. Application Design & Functionality** | **2.0** | Modular Flask Application Factory (`app/__init__.py`) with 4 Blueprints (`dashboard_bp`, `sql_bp`, `nosql_bp`, `api_bp`), intuitive 5-tab navigation, and one-click seed reset. |
| **2. Python Programming Implementation** | **2.0** | OOP dataclasses (`app/models.py`), Repository pattern classes, context managers (`@contextmanager`), custom exception classes (`app/exceptions.py`), and File Handling (`app/file_manager.py` for CSV/JSON export & log files). |
| **3. Database Integration (SQL & NoSQL)** | **2.0** | Live MySQL 8.0 (`PyMySQL`) + MongoDB (`PyMongo`) integration with automatic transactional commits/rollbacks, cascading foreign keys, and synchronized SQL + NoSQL writes. |
| **4. Advanced Database Querying & Data Retrieval** | **2.0** | Implements 2-table & 3-table `INNER JOIN`, scalar `Nested Subquery` (`< 58.30%`), `GROUP BY income_category`, `MIN/MAX/AVG` aggregations, Stored Procedure `CALL GetPoorWaterAccess(50)`, MongoDB `$lt` filter, and `$lookup` + `$unwind` + `$group` Aggregation Pipeline. |
| **5. Code Quality, Documentation & Output Presentation** | **1.0** | Clean PEP-8 code with type hints and docstrings, interactive SQL/NoSQL syntax viewer on every page, and calibrated dataset matching exact report results (`Min: 30%`, `Max: 95%`, `Avg Access: 58.30%`, `Avg Quality: 73.30`). |
| **6. Testing, Validation, Security & Error Handling** | **1.0** | Server-side input validation (`app/validators.py`), parameterized SQL queries preventing SQL injection, custom 400/404/500 error pages, and an 11-test automated verification suite (`tests/test_dbms_app.py`). |
