"""
MongoDB / NoSQL Integration Blueprint (`nosql_bp`).
Demonstrates PyMongo document storage, `$lt` filtering, multi-stage Aggregation
Pipelines (`$group`, `$lookup`, `$unwind`), and the automated `mongodb_demo.py` lifecycle.
"""

from flask import Blueprint, render_template, request, flash, current_app
from app.database.nosql_repository import PIPELINE_CATALOG
from app.validators import validate_threshold

nosql_bp = Blueprint("nosql", __name__)


@nosql_bp.route("/workbench")
def workbench():
    """Renders the MongoDB / NoSQL Workbench with collection browser, filter, and aggregation pipelines."""
    nosql_repo = current_app.extensions["nosql_repo"]
    threshold = validate_threshold(request.args.get("threshold", 50.0), default=50.0)

    docs_bundle = nosql_repo.get_all_documents()
    filtered_docs = nosql_repo.filter_poor_water_access(threshold=threshold)
    agg_results = nosql_repo.run_aggregation_pipeline()

    return render_template(
        "nosql_lab.html",
        threshold=threshold,
        docs_bundle=docs_bundle,
        filtered_docs=filtered_docs,
        agg_results=agg_results,
        pipeline_catalog=PIPELINE_CATALOG,
        demo_trace=None,
    )


@nosql_bp.route("/run-demo", methods=["POST"])
def run_demo():
    """Executes the complete `mongodb_demo.py` lifecycle (Create, Read, Update, Delete, Filter, Aggregation)."""
    nosql_repo = current_app.extensions["nosql_repo"]
    demo_trace = nosql_repo.run_mongodb_lifecycle_demo()
    docs_bundle = nosql_repo.get_all_documents()
    filtered_docs = nosql_repo.filter_poor_water_access(threshold=50.0)
    agg_results = nosql_repo.run_aggregation_pipeline()
    flash("Completed MongoDB CRUD, Filtering ($lt), and Aggregation Pipeline demonstration.", "success")

    return render_template(
        "nosql_lab.html",
        threshold=50.0,
        docs_bundle=docs_bundle,
        filtered_docs=filtered_docs,
        agg_results=agg_results,
        pipeline_catalog=PIPELINE_CATALOG,
        demo_trace=demo_trace,
    )
