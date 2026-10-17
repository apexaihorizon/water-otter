"""
REST JSON API, File Export (CSV/JSON), and Database Reset Blueprint (`api_bp`).
Addresses ESE Rubrics:
- Python Programming Implementation (File Handling: CSV & JSON generation)
- Database Integration & Diagnostics
"""

from flask import Blueprint, jsonify, request, send_file, redirect, url_for, flash, current_app
from app.validators import validate_threshold

api_bp = Blueprint("api", __name__)


def _resolve_query_rows(sql_repo, nosql_repo, query_key: str, threshold: float = 50.0):
    """Helper resolving any named SQL or NoSQL query to a list of dictionaries for API or File Export."""
    if query_key == "view_communities":
        return sql_repo.get_all_communities()
    if query_key == "stored_procedure_poor_access":
        return sql_repo.call_get_poor_water_access(threshold=threshold)
    if query_key == "water_analysis_join":
        return sql_repo.get_water_analysis_join()
    if query_key == "nested_subquery_below_avg":
        return sql_repo.get_below_average_water_access_subquery()
    if query_key == "income_group_analysis":
        return sql_repo.get_income_group_analysis()
    if query_key == "inequality_summary":
        return [sql_repo.get_inequality_summary_aggregation()]
    if query_key == "sanitation_analysis":
        return sql_repo.get_sanitation_analysis()
    if query_key == "mongodb_filtered":
        return nosql_repo.filter_poor_water_access(threshold=threshold)
    if query_key == "mongodb_aggregation":
        return nosql_repo.run_aggregation_pipeline()["income_breakdown"]
    return sql_repo.get_water_analysis_join()


@api_bp.route("/export/<string:fmt>/<string:query_key>")
def export_query_file(fmt: str, query_key: str):
    """Exports any SQL or NoSQL query result to a downloadable CSV or JSON file on disk."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    file_manager = current_app.extensions["file_manager"]
    threshold = validate_threshold(request.args.get("threshold", 50.0), default=50.0)

    rows = _resolve_query_rows(sql_repo, nosql_repo, query_key, threshold=threshold)
    if fmt.lower() == "csv":
        file_path = file_manager.export_to_csv(query_key, rows)
        return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype="text/csv")
    else:
        file_path = file_manager.export_to_json(query_key, rows)
        return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype="application/json")


@api_bp.route("/reset-databases", methods=["POST"])
def reset_databases():
    """Resets both SQL and NoSQL databases to the canonical 10-community seed dataset."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    sql_repo.initialize_and_seed(force_reset=True)
    nosql_repo.initialize_and_seed(force_reset=True)
    flash("Reset and re-seeded both SQL and NoSQL databases to the canonical 10 communities (Communities A–J).", "info")
    return redirect(request.referrer or url_for("dashboard.index"))


@api_bp.route("/health")
def health_check():
    """Returns JSON health status and key metrics for automated verification."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    summary = sql_repo.get_inequality_summary_aggregation()
    mongo_agg = nosql_repo.run_aggregation_pipeline()
    return jsonify({
        "status": "OK",
        "sql_backend": sql_repo.backend_mode,
        "sql_connection": sql_repo.connection_info,
        "nosql_backend": nosql_repo.backend_mode,
        "nosql_connection": nosql_repo.connection_info,
        "sql_summary": summary,
        "nosql_summary": mongo_agg["global_summary"],
    })
