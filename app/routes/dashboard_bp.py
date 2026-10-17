"""
Executive Dashboard & ESE Rubric Benchmark Blueprint (`dashboard_bp`).
Displays overall SQL & NoSQL inequality KPIs, income-group comparison charts,
sanitation correlations, and interactive ESE Rubric verification.
"""

from flask import Blueprint, render_template, current_app

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    """Renders the main executive dashboard combining SQL and NoSQL analytical outputs."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    file_manager = current_app.extensions["file_manager"]

    summary = sql_repo.get_inequality_summary_aggregation()
    income_groups = sql_repo.get_income_group_analysis()
    poor_access = sql_repo.call_get_poor_water_access(50.0)
    water_join = sql_repo.get_water_analysis_join()
    mongo_agg = nosql_repo.run_aggregation_pipeline()
    recent_logs = file_manager.read_recent_logs(limit=12)

    return render_template(
        "dashboard.html",
        summary=summary,
        income_groups=income_groups,
        poor_access=poor_access,
        water_join=water_join,
        mongo_agg=mongo_agg,
        recent_logs=recent_logs,
    )


@dashboard_bp.route("/rubric-benchmark")
def rubric_benchmark():
    """Renders the interactive ESE Rubric Benchmark, Test Matrix, and Viva Voce Guide."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    file_manager = current_app.extensions["file_manager"]

    summary = sql_repo.get_inequality_summary_aggregation()
    mongo_agg = nosql_repo.run_aggregation_pipeline()
    logs = file_manager.read_recent_logs(limit=25)

    return render_template(
        "rubric_benchmark.html",
        summary=summary,
        mongo_agg=mongo_agg,
        logs=logs,
    )
