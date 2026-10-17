"""
Flask Application Factory (`create_app`).
Initializes configuration, FileManager, SQLRepository, NoSQLRepository,
modular Flask Blueprints, context processors, and global exception handlers.
"""

from config import Config
from app.file_manager import FileManager
from app.database.sql_repository import SQLRepository
from app.database.nosql_repository import NoSQLRepository
from app.exceptions import DBMSAppError, ValidationError


def create_app(config_class=Config):
    """Application Factory creating and configuring the modular Flask instance."""
    from flask import Flask, render_template

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize core service singletons on app.extensions
    file_manager = FileManager(
        export_dir=config_class.EXPORT_DIR,
        audit_log_path=config_class.AUDIT_LOG_PATH,
        seed_json_path=config_class.SEED_JSON_PATH,
    )
    sql_repo = SQLRepository(config=config_class, file_manager=file_manager)
    nosql_repo = NoSQLRepository(config=config_class, file_manager=file_manager)

    # Ensure tables/collections and canonical seed records exist on startup
    sql_repo.initialize_and_seed(force_reset=False)
    nosql_repo.initialize_and_seed(force_reset=False)

    app.extensions["file_manager"] = file_manager
    app.extensions["sql_repo"] = sql_repo
    app.extensions["nosql_repo"] = nosql_repo

    # Register Modular Blueprints
    from app.routes.dashboard_bp import dashboard_bp
    from app.routes.sql_bp import sql_bp
    from app.routes.nosql_bp import nosql_bp
    from app.routes.api_bp import api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(sql_bp, url_prefix="/sql")
    app.register_blueprint(nosql_bp, url_prefix="/nosql")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Inject global database status metadata into all templates
    @app.context_processor
    def inject_db_status():
        return {
            "app_title": app.config.get("APP_TITLE", "Water Access Inequality Analysis System"),
            "course_info": app.config.get("COURSE_INFO", ""),
            "sql_backend_mode": sql_repo.backend_mode,
            "sql_connection_info": sql_repo.connection_info,
            "nosql_backend_mode": nosql_repo.backend_mode,
            "nosql_connection_info": nosql_repo.connection_info,
        }

    # Global Error & Exception Handlers (Testing, Validation, Security & Error Handling Rubric)
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError):
        return (
            render_template(
                "errors/400.html",
                error_title="Input Validation Error",
                error_message=err.message,
                error_field=err.field,
                error_details=err.details,
            ),
            400,
        )

    @app.errorhandler(DBMSAppError)
    def handle_dbms_error(err: DBMSAppError):
        return (
            render_template(
                "errors/500.html",
                error_title="Database Operation Error",
                error_message=err.message,
                error_details=err.details,
            ),
            err.status_code,
        )

    @app.errorhandler(404)
    def handle_not_found(err):
        return render_template("errors/404.html", error_message=str(err)), 404

    @app.errorhandler(500)
    def handle_server_error(err):
        return (
            render_template(
                "errors/500.html",
                error_title="Internal Server Error",
                error_message="An unexpected error occurred while processing your request.",
                error_details=str(err),
            ),
            500,
        )

    return app
