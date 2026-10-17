"""
Comprehensive Automated Test Suite for Water Access Inequality Analysis System.
Addresses ESE Rubric: Testing, Validation, Security & Error Handling (1.0 Mark).

Run with either:
    python -m unittest discover -s tests -v
or:
    pytest -v
"""

import unittest
from config import TestingConfig
from app.file_manager import FileManager
from app.database.sql_repository import SQLRepository
from app.database.nosql_repository import NoSQLRepository
from app.models import Community, WaterQuality, Sanitation, CommunityProfile
from app.validators import validate_community_payload, validate_threshold
from app.exceptions import ValidationError, QueryExecutionError

import importlib.util
from app import create_app
FLASK_AVAILABLE = importlib.util.find_spec("flask") is not None


class TestWaterAccessDBMSApp(unittest.TestCase):
    """End-to-end verification of SQL, NoSQL, OOP models, validation, security, and file handling."""

    def setUp(self):
        self.file_manager = FileManager(
            export_dir=TestingConfig.EXPORT_DIR,
            audit_log_path=TestingConfig.AUDIT_LOG_PATH,
            seed_json_path=TestingConfig.SEED_JSON_PATH,
        )
        self.sql_repo = SQLRepository(config=TestingConfig, file_manager=self.file_manager)
        self.nosql_repo = NoSQLRepository(config=TestingConfig, file_manager=self.file_manager)
        self.sql_repo.initialize_and_seed(force_reset=True)
        self.nosql_repo.initialize_and_seed(force_reset=True)

    def test_01_view_communities_count_and_order(self):
        """Verify View Communities returns all 10 canonical communities (A through J)."""
        rows = self.sql_repo.get_all_communities()
        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0]["community_name"], "Community A")
        self.assertEqual(rows[-1]["community_name"], "Community J")

    def test_02_inequality_summary_matches_ese_report_metrics(self):
        """Verify SQL MIN, MAX, AVG aggregations match Section 9 of the ESE Report exactly."""
        summary = self.sql_repo.get_inequality_summary_aggregation()
        self.assertEqual(summary["total_communities"], 10)
        self.assertAlmostEqual(summary["min_water_access"], 30.0, places=2)
        self.assertAlmostEqual(summary["max_water_access"], 95.0, places=2)
        self.assertAlmostEqual(summary["avg_water_access"], 58.30, places=2)
        self.assertAlmostEqual(summary["avg_water_quality"], 73.30, places=2)
        self.assertEqual(summary["low_income_communities"], 5)
        self.assertEqual(summary["middle_income_communities"], 4)
        self.assertEqual(summary["high_income_communities"], 1)

    def test_03_income_group_by_matches_ese_report_table(self):
        """Verify SQL GROUP BY income_category matches the Income-wise Analysis table on Page 4."""
        groups = {g["income_category"]: g for g in self.sql_repo.get_income_group_analysis()}
        self.assertEqual(set(groups.keys()), {"Low", "Middle", "High"})

        self.assertEqual(groups["Low"]["count"], 5)
        self.assertAlmostEqual(groups["Low"]["avg_access_pct"], 49.60, places=2)
        self.assertAlmostEqual(groups["Low"]["avg_quality"], 67.40, places=2)

        self.assertEqual(groups["Middle"]["count"], 4)
        self.assertAlmostEqual(groups["Middle"]["avg_access_pct"], 60.00, places=2)
        self.assertAlmostEqual(groups["Middle"]["avg_quality"], 75.00, places=2)

        self.assertEqual(groups["High"]["count"], 1)
        self.assertAlmostEqual(groups["High"]["avg_access_pct"], 95.00, places=2)
        self.assertAlmostEqual(groups["High"]["avg_quality"], 96.00, places=2)

    def test_04_stored_procedure_poor_water_access(self):
        """Verify Stored Procedure GetPoorWaterAccess(50) returns only communities with < 50% access."""
        poor_rows = self.sql_repo.call_get_poor_water_access(50.0)
        self.assertEqual(len(poor_rows), 4)
        for row in poor_rows:
            self.assertLess(row["clean_water_access"], 50.0)

    def test_05_water_analysis_and_sanitation_joins(self):
        """Verify 2-table and 3-table SQL INNER JOIN queries combine all columns accurately."""
        water_join = self.sql_repo.get_water_analysis_join()
        self.assertEqual(len(water_join), 10)
        self.assertIn("clean_water_access", water_join[0])
        self.assertIn("water_quality_score", water_join[0])

        sanitation_join = self.sql_repo.get_sanitation_analysis()
        self.assertEqual(len(sanitation_join), 10)
        self.assertIn("sanitation_coverage", sanitation_join[0])
        self.assertIn("toilet_availability", sanitation_join[0])

    def test_06_nested_subquery_below_overall_average(self):
        """Verify SQL Nested Subquery returns communities below overall average (58.30%)."""
        below_avg = self.sql_repo.get_below_average_water_access_subquery()
        self.assertEqual(len(below_avg), 5)
        for r in below_avg:
            self.assertLess(r["clean_water_access"], 58.30)

    def test_07_temporary_community_k_crud_lifecycle(self):
        """Verify Temporary Community K CRUD demo executes INSERT -> UPDATE -> DELETE cleanly."""
        steps = self.sql_repo.run_community_k_crud_demo()
        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[0]["snapshot"]["population"], 3500)
        self.assertEqual(steps[1]["snapshot"]["population"], 3850)
        self.assertEqual(steps[2]["snapshot"]["remaining_communities_count"], 10)

    def test_08_mongodb_nosql_filter_and_aggregation_pipeline(self):
        """Verify MongoDB $lt filtering, $group, $lookup pipeline, and full lifecycle demo."""
        filtered = self.nosql_repo.filter_poor_water_access(50.0)
        self.assertEqual(len(filtered), 4)

        agg = self.nosql_repo.run_aggregation_pipeline()
        gs = agg["global_summary"]
        self.assertAlmostEqual(gs["min_water_access"], 30.0, places=2)
        self.assertAlmostEqual(gs["max_water_access"], 95.0, places=2)
        self.assertAlmostEqual(gs["avg_water_access"], 58.30, places=2)
        self.assertAlmostEqual(gs["avg_water_quality"], 73.30, places=2)

        trace = self.nosql_repo.run_mongodb_lifecycle_demo()
        self.assertEqual(len(trace), 6)

    def test_09_input_validation_and_sql_injection_defense(self):
        """Verify server-side validators reject out-of-range metrics and SQL injection strings."""
        with self.assertRaises(ValidationError):
            validate_community_payload({
                "community_id": 12,
                "community_name": "Community X'; DROP TABLE communities;--",
                "district": "Pune",
                "population": 4000,
                "income_category": "Low",
                "clean_water_access": 50,
                "water_quality_score": 60,
            })

        with self.assertRaises(ValidationError):
            validate_community_payload({
                "community_id": 12,
                "community_name": "Valid Name",
                "district": "Pune",
                "population": -500,
                "income_category": "Low",
                "clean_water_access": 50,
                "water_quality_score": 60,
            })

        with self.assertRaises(ValidationError):
            validate_threshold(145.0)

    def test_10_oop_models_and_file_handling_exports(self):
        """Verify OOP dataclass models and CSV/JSON file export operations."""
        comm = Community(1, "Community A", "Pune Rural", 4200, "Low")
        wq = WaterQuality(101, 1, 30.0, 4.0, 3.5, 55.0)
        san = Sanitation(201, 1, 35.0, 40.0, 48.0)
        profile = CommunityProfile(comm, wq, san)
        flat = profile.to_flat_dict()
        self.assertEqual(flat["access_status"], "Critical (<50%)")

        rows = self.sql_repo.get_income_group_analysis()
        csv_path = self.file_manager.export_to_csv("test_income_export", rows)
        json_path = self.file_manager.export_to_json("test_income_export", rows)
        self.assertTrue(csv_path.exists())
        self.assertTrue(json_path.exists())
        self.assertGreater(len(self.file_manager.read_recent_logs()), 0)

    @unittest.skipUnless(FLASK_AVAILABLE, "Flask not installed in offline test runner")
    def test_11_flask_web_routes_integration(self):
        """Verify Flask Blueprints render HTTP 200 across Dashboard, SQL Lab, CRUD, and NoSQL Lab."""
        app = create_app(TestingConfig)
        client = app.test_client()
        for url in ["/", "/sql/workbench", "/sql/crud", "/nosql/workbench", "/rubric-benchmark", "/api/health"]:
            resp = client.get(url)
            self.assertEqual(resp.status_code, 200, f"Route {url} failed with {resp.status_code}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
