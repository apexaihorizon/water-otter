"""
Advanced SQL Querying & Transactional CRUD Blueprint (`sql_bp`).
Implements all relational operations from the ESE Report:
- View Communities (`SELECT`)
- Poor Water Access (`CALL GetPoorWaterAccess(threshold)` Stored Procedure)
- Water Analysis (`INNER JOIN`)
- Below Average Access (`Nested Subquery`)
- Income Analysis (`GROUP BY`)
- Inequality Summary (`MIN`, `MAX`, `AVG` Aggregations)
- Sanitation Data (`Multi-Table JOIN`)
- Interactive CRUD Manager & 1-Click Temporary Community K CRUD Lifecycle Demo
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from app.database.sql_repository import QUERY_CATALOG
from app.validators import validate_community_payload, validate_threshold
from app.exceptions import ValidationError, DBMSAppError

sql_bp = Blueprint("sql", __name__)


@sql_bp.route("/workbench")
def workbench():
    """
    Interactive SQL Query Workbench.
    Allows switching between all 7 analytical SQL views, inspecting exact SQL code,
    customizing the Stored Procedure threshold, and exporting results to CSV/JSON.
    """
    sql_repo = current_app.extensions["sql_repo"]
    mode = request.args.get("mode", "water_analysis_join")
    threshold = validate_threshold(request.args.get("threshold", 50.0), default=50.0)

    if mode not in QUERY_CATALOG:
        mode = "water_analysis_join"

    query_meta = dict(QUERY_CATALOG[mode])
    rows = []
    summary_dict = None

    if mode == "view_communities":
        rows = sql_repo.get_all_communities()
    elif mode == "stored_procedure_poor_access":
        rows = sql_repo.call_get_poor_water_access(threshold=threshold)
        query_meta["sql"] = query_meta["sql"].replace("50.0", str(threshold))
    elif mode == "water_analysis_join":
        rows = sql_repo.get_water_analysis_join()
    elif mode == "nested_subquery_below_avg":
        rows = sql_repo.get_below_average_water_access_subquery()
    elif mode == "income_group_analysis":
        rows = sql_repo.get_income_group_analysis()
    elif mode == "inequality_summary":
        summary_dict = sql_repo.get_inequality_summary_aggregation()
        rows = [summary_dict] if summary_dict else []
    elif mode == "sanitation_analysis":
        rows = sql_repo.get_sanitation_analysis()
    else:
        rows = sql_repo.get_water_analysis_join()

    columns = list(rows[0].keys()) if rows else []

    return render_template(
        "sql_lab.html",
        active_mode=mode,
        threshold=threshold,
        query_catalog=QUERY_CATALOG,
        query_meta=query_meta,
        rows=rows,
        columns=columns,
        summary_dict=summary_dict,
    )


@sql_bp.route("/crud", methods=["GET"])
def crud_manager():
    """Renders the SQL CRUD Management interface and Temporary Community K Demo runner."""
    sql_repo = current_app.extensions["sql_repo"]
    communities = sql_repo.get_sanitation_analysis()
    edit_id = request.args.get("edit_id", type=int)
    edit_record = sql_repo.get_single_community_full(edit_id) if edit_id else None

    return render_template(
        "crud_manager.html",
        communities=communities,
        edit_record=edit_record,
        demo_steps=None,
        query_meta=QUERY_CATALOG["crud_demo_community_k"],
    )


@sql_bp.route("/crud/create", methods=["POST"])
def create_community():
    """Handles form submission to INSERT a new community, water_quality, and sanitation record."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    try:
        cleaned = validate_community_payload(request.form.to_dict(), require_all=True)
        sql_repo.create_community_record(cleaned)
        # Keep NoSQL document store synchronized
        nosql_repo.insert_document_pair(
            {
                "community_id": cleaned["community_id"],
                "community_name": cleaned["community_name"],
                "district": cleaned["district"],
                "population": cleaned["population"],
                "income_category": cleaned["income_category"],
            },
            {
                "water_id": 100 + cleaned["community_id"],
                "community_id": cleaned["community_id"],
                "clean_water_access": cleaned["clean_water_access"],
                "availability_hours": cleaned["availability_hours"],
                "distance_to_source": cleaned["distance_to_source"],
                "water_quality_score": cleaned["water_quality_score"],
            },
        )
        flash(f"Successfully inserted '{cleaned['community_name']}' (ID={cleaned['community_id']}) into SQL & NoSQL databases.", "success")
    except (ValidationError, DBMSAppError) as err:
        flash(f"Validation / Database Error: {err.message} {getattr(err, 'details', '')}", "danger")
    return redirect(url_for("sql.crud_manager"))


@sql_bp.route("/crud/update/<int:community_id>", methods=["POST"])
def update_community(community_id: int):
    """Handles form submission to UPDATE an existing community across normalized tables."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    try:
        payload = request.form.to_dict()
        payload["community_id"] = community_id
        cleaned = validate_community_payload(payload, require_all=True)
        sql_repo.update_community_record(community_id, cleaned)
        nosql_repo.update_community_population(
            community_id,
            new_population=cleaned["population"],
            new_access=cleaned["clean_water_access"],
        )
        flash(f"Successfully updated Community ID {community_id} ('{cleaned['community_name']}').", "success")
    except (ValidationError, DBMSAppError) as err:
        flash(f"Update Error: {err.message} {getattr(err, 'details', '')}", "danger")
    return redirect(url_for("sql.crud_manager"))


@sql_bp.route("/crud/delete/<int:community_id>", methods=["POST"])
def delete_community(community_id: int):
    """Deletes a community record and cascades deletion across child tables."""
    sql_repo = current_app.extensions["sql_repo"]
    nosql_repo = current_app.extensions["nosql_repo"]
    deleted = sql_repo.delete_community_record(community_id)
    nosql_repo.delete_document_by_community_id(community_id)
    if deleted:
        flash(f"Deleted Community ID {community_id} from SQL and NoSQL databases.", "warning")
    else:
        flash(f"Community ID {community_id} was not found.", "info")
    return redirect(url_for("sql.crud_manager"))


@sql_bp.route("/crud/demo-community-k", methods=["POST"])
def run_community_k_demo():
    """Executes the automated Temporary Community K CRUD Lifecycle Demo (INSERT -> UPDATE -> DELETE)."""
    sql_repo = current_app.extensions["sql_repo"]
    demo_steps = sql_repo.run_community_k_crud_demo()
    communities = sql_repo.get_sanitation_analysis()
    flash("Executed Temporary Community K CRUD Demonstration (INSERT -> UPDATE -> DELETE).", "success")
    return render_template(
        "crud_manager.html",
        communities=communities,
        edit_record=None,
        demo_steps=demo_steps,
        query_meta=QUERY_CATALOG["crud_demo_community_k"],
    )
