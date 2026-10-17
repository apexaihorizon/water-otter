#!/usr/bin/env python3
"""
Main Entry Point for the Water Access Inequality Analysis System (Flask Web App).
Run with:
    python run.py
Then open http://127.0.0.1:5000 in your browser.
"""

import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    print("=" * 76)
    print(" WATER ACCESS INEQUALITY ANALYSIS SYSTEM (Modular Flask + SQL & NoSQL DBMS)")
    print(" Symbiosis Institute of Technology, Pune | DCDS Lab ESE Miniproject")
    print(f" URL: http://127.0.0.1:{port}")
    print("=" * 76)
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
