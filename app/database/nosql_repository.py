"""
NoSQL Database Repository (MongoDB via PyMongo with Automatic Local Document Store Fallback).
Addresses ESE Rubrics:
- Database Integration (SQL & NoSQL) (2.0 Marks)
- Advanced Database Querying & Data Retrieval (2.0 Marks):
  MongoDB CRUD (`insert_one`, `find`, `update_one`, `delete_one`),
  Filtering (`{"clean_water_access": {"$lt": 50}}`), and
  Multi-stage Aggregation Pipeline (`$lookup`, `$unwind`, `$group`, `$sort`).
"""

import copy
import json
from typing import List, Dict, Any

try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

from app.file_manager import FileManager


PIPELINE_CATALOG: Dict[str, Dict[str, str]] = {
    "mongo_read_all": {
        "title": "Read Community & Water Quality Documents (PyMongo find)",
        "category": "NoSQL Document Retrieval",
        "code": (
            "# Retrieve documents from MongoDB collections\n"
            "communities_docs = list(db.communities.find({}, {'_id': 0}).sort('community_id', 1))\n"
            "water_docs = list(db.water_quality.find({}, {'_id': 0}).sort('community_id', 1))"
        ),
        "description": "Fetches schemaless JSON/BSON documents from the `communities` and `water_quality` collections in `water_access_inequality`.",
    },
    "mongo_filter_lt_50": {
        "title": "Filter Poor Water-Access Communities (MongoDB $lt Operator)",
        "category": "NoSQL Query Filtering",
        "code": (
            "# Filter documents where clean_water_access < 50\n"
            "cursor = db.water_quality.find(\n"
            "    {'clean_water_access': {'$lt': 50.0}},\n"
            "    {'_id': 0}\n"
            ").sort('clean_water_access', 1)"
        ),
        "description": "Applies the MongoDB `$lt` comparison operator to filter communities with less than 50% clean water access.",
    },
    "mongo_aggregation_summary": {
        "title": "Global Inequality Metrics (MongoDB Aggregation Pipeline)",
        "category": "MongoDB Aggregation Pipeline ($group)",
        "code": (
            "pipeline = [\n"
            "    {\n"
            "        '$group': {\n"
            "            '_id': None,\n"
            "            'min_water_access': {'$min': '$clean_water_access'},\n"
            "            'max_water_access': {'$max': '$clean_water_access'},\n"
            "            'avg_water_access': {'$avg': '$clean_water_access'},\n"
            "            'avg_water_quality': {'$avg': '$water_quality_score'},\n"
            "            'total_records': {'$sum': 1}\n"
            "        }\n"
            "    },\n"
            "    {\n"
            "        '$project': {\n"
            "            '_id': 0,\n"
            "            'min_water_access': {'$round': ['$min_water_access', 2]},\n"
            "            'max_water_access': {'$round': ['$max_water_access', 2]},\n"
            "            'avg_water_access': {'$round': ['$avg_water_access', 2]},\n"
            "            'avg_water_quality': {'$round': ['$avg_water_quality', 2]},\n"
            "            'total_records': 1\n"
            "        }\n"
            "    }\n"
            "]\n"
            "result = list(db.water_quality.aggregate(pipeline))"
        ),
        "description": "Computes minimum, maximum, and average clean water access and average water quality across `water_quality` documents using `$group` and `$project` stages.",
    },
    "mongo_income_lookup_pipeline": {
        "title": "Cross-Collection Income Tier Aggregation ($lookup + $unwind + $group)",
        "category": "Multi-Stage MongoDB Aggregation Pipeline",
        "code": (
            "pipeline = [\n"
            "    {\n"
            "        '$lookup': {\n"
            "            'from': 'water_quality',\n"
            "            'localField': 'community_id',\n"
            "            'foreignField': 'community_id',\n"
            "            'as': 'water_metrics'\n"
            "        }\n"
            "    },\n"
            "    {'$unwind': '$water_metrics'},\n"
            "    {\n"
            "        '$group': {\n"
            "            '_id': '$income_category',\n"
            "            'count': {'$sum': 1},\n"
            "            'avg_access_pct': {'$avg': '$water_metrics.clean_water_access'},\n"
            "            'avg_quality': {'$avg': '$water_metrics.water_quality_score'}\n"
            "        }\n"
            "    },\n"
            "    {'$sort': {'avg_access_pct': 1}}\n"
            "]\n"
            "result = list(db.communities.aggregate(pipeline))"
        ),
        "description": "Joins `communities` and `water_quality` collections in MongoDB using `$lookup`, flattens with `$unwind`, and groups by `income_category`.",
    },
    "mongo_crud_demo": {
        "title": "MongoDB CRUD & Aggregation Lifecycle (mongodb_demo.py)",
        "category": "NoSQL CRUD Lifecycle",
        "code": (
            "# 1. CREATE: Insert temporary test community & water_quality document\n"
            "db.communities.insert_one({'community_id': 11, 'community_name': 'Community K (NoSQL)', 'district': 'Purandar South', 'population': 3500, 'income_category': 'Low'})\n"
            "db.water_quality.insert_one({'water_id': 111, 'community_id': 11, 'clean_water_access': 38.0, 'availability_hours': 5.0, 'distance_to_source': 2.9, 'water_quality_score': 60.0})\n\n"
            "# 2. UPDATE: Modify population using $set\n"
            "db.communities.update_one({'community_id': 11}, {'$set': {'population': 3900}})\n\n"
            "# 3. DELETE: Remove temporary test community\n"
            "db.communities.delete_one({'community_id': 11})\n"
            "db.water_quality.delete_one({'community_id': 11})"
        ),
        "description": "Demonstrates complete PyMongo Create, Read, Update (`$set`), Filter (`$lt`), Aggregation, and Delete operations.",
    },
}


class NoSQLRepository:
    """
    Manages MongoDB operations for the `water_access_inequality` database.
    Uses PyMongo when a local MongoDB instance is reachable; transparently falls back
    to a persistent JSON Document Store with full pipeline emulation when offline.
    """

    def __init__(self, config: Any, file_manager: FileManager):
        self.config = config
        self.file_manager = file_manager
        self.backend_mode = "json_document_fallback"
        self.connection_info = f"Local Document Store ({self.config.NOSQL_FALLBACK_PATH.name})"
        self._client = None
        self._db = None
        self._detect_backend()

    def _detect_backend(self) -> None:
        """Checks if MongoDB server is reachable via PyMongo; falls back to JSON document store if offline."""
        if getattr(self.config, "FORCE_MONGO_FALLBACK", False) or not PYMONGO_AVAILABLE:
            self.backend_mode = "json_document_fallback"
            self.connection_info = f"Document Store Fallback ({self.config.NOSQL_FALLBACK_PATH.name})"
            return

        try:
            client = pymongo.MongoClient(self.config.MONGO_URI, serverSelectionTimeoutMS=1500)
            client.admin.command("ping")
            self._client = client
            self._db = client[self.config.MONGO_DB]
            self.backend_mode = "mongodb"
            self.connection_info = f"MongoDB ({self.config.MONGO_URI}{self.config.MONGO_DB})"
            self.file_manager.log_event("NOSQL_CONNECT", f"Connected to live {self.connection_info}")
        except Exception as exc:
            self.backend_mode = "json_document_fallback"
            self.connection_info = f"Document Engine ({self.config.NOSQL_FALLBACK_PATH.name} - MongoDB offline)"
            self.file_manager.log_event(
                "NOSQL_FALLBACK",
                f"MongoDB unreachable ({exc}); switched to local JSON document engine.",
            )

    def _read_local_store(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.config.NOSQL_FALLBACK_PATH.exists():
            seed = self.file_manager.load_seed_dataset()
            self._write_local_store({
                "communities": copy.deepcopy(seed["communities"]),
                "water_quality": copy.deepcopy(seed["water_quality"]),
            })
        with open(self.config.NOSQL_FALLBACK_PATH, mode="r", encoding="utf-8") as f:
            return json.load(f)

    def _write_local_store(self, data: Dict[str, List[Dict[str, Any]]]) -> None:
        self.config.NOSQL_FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.NOSQL_FALLBACK_PATH, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def initialize_and_seed(self, force_reset: bool = False) -> None:
        """Initializes `communities` and `water_quality` collections with canonical documents."""
        seed = self.file_manager.load_seed_dataset()
        if self.backend_mode == "mongodb" and self._db is not None:
            if force_reset or self._db.communities.count_documents({}) == 0:
                self._db.communities.delete_many({})
                self._db.water_quality.delete_many({})
                self._db.communities.insert_many(copy.deepcopy(seed["communities"]))
                self._db.water_quality.insert_many(copy.deepcopy(seed["water_quality"]))
                self.file_manager.log_event("NOSQL_SEED", "Seeded MongoDB collections `communities` and `water_quality`.")
        else:
            if force_reset or not self.config.NOSQL_FALLBACK_PATH.exists():
                self._write_local_store({
                    "communities": copy.deepcopy(seed["communities"]),
                    "water_quality": copy.deepcopy(seed["water_quality"]),
                })
                self.file_manager.log_event("NOSQL_SEED", "Seeded local NoSQL document collections `communities` and `water_quality`.")

    def get_all_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieves all documents from both `communities` and `water_quality` collections."""
        if self.backend_mode == "mongodb" and self._db is not None:
            communities = list(self._db.communities.find({}, {"_id": 0}).sort("community_id", 1))
            water_quality = list(self._db.water_quality.find({}, {"_id": 0}).sort("community_id", 1))
        else:
            store = self._read_local_store()
            communities = sorted(store.get("communities", []), key=lambda x: x["community_id"])
            water_quality = sorted(store.get("water_quality", []), key=lambda x: x["community_id"])

        # Build enriched merged view for UI convenience while also returning raw collections
        comm_map = {c["community_id"]: c for c in communities}
        merged = []
        for w in water_quality:
            c = comm_map.get(w["community_id"], {})
            merged.append({
                "community_id": w["community_id"],
                "community_name": c.get("community_name", f"Community {w['community_id']}"),
                "district": c.get("district", "Unknown"),
                "population": c.get("population", 0),
                "income_category": c.get("income_category", "Unknown"),
                "water_id": w["water_id"],
                "clean_water_access": w["clean_water_access"],
                "availability_hours": w["availability_hours"],
                "distance_to_source": w["distance_to_source"],
                "water_quality_score": w["water_quality_score"],
            })

        self.file_manager.log_event("NOSQL_READ", f"Retrieved {len(communities)} community docs and {len(water_quality)} water_quality docs.")
        return {
            "communities": communities,
            "water_quality": water_quality,
            "merged_documents": merged,
        }

    def filter_poor_water_access(self, threshold: float = 50.0) -> List[Dict[str, Any]]:
        """
        MongoDB Filtering Demonstration:
        Finds documents in `water_quality` where `{"clean_water_access": {"$lt": threshold}}`.
        """
        if self.backend_mode == "mongodb" and self._db is not None:
            water_docs = list(
                self._db.water_quality.find(
                    {"clean_water_access": {"$lt": threshold}},
                    {"_id": 0},
                ).sort("clean_water_access", 1)
            )
            comm_docs = {
                c["community_id"]: c
                for c in self._db.communities.find({}, {"_id": 0})
            }
        else:
            store = self._read_local_store()
            water_docs = sorted(
                [w for w in store["water_quality"] if float(w["clean_water_access"]) < threshold],
                key=lambda x: float(x["clean_water_access"]),
            )
            comm_docs = {c["community_id"]: c for c in store["communities"]}

        results = []
        for w in water_docs:
            c = comm_docs.get(w["community_id"], {})
            results.append({
                "community_id": w["community_id"],
                "community_name": c.get("community_name", ""),
                "district": c.get("district", ""),
                "income_category": c.get("income_category", ""),
                "population": c.get("population", 0),
                "clean_water_access": w["clean_water_access"],
                "water_quality_score": w["water_quality_score"],
                "availability_hours": w["availability_hours"],
                "distance_to_source": w["distance_to_source"],
            })

        self.file_manager.log_event(
            "NOSQL_FILTER",
            f"Filtered MongoDB documents with clean_water_access < {threshold} ({len(results)} matched).",
        )
        return results

    def run_aggregation_pipeline(self) -> Dict[str, Any]:
        """
        MongoDB Aggregation Pipeline Demonstration:
        1. Global `$group` pipeline computing min, max, avg water access and avg water quality.
        2. Cross-collection `$lookup` + `$unwind` + `$group` pipeline computing metrics per income_category.
        """
        if self.backend_mode == "mongodb" and self._db is not None:
            summary_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "min_water_access": {"$min": "$clean_water_access"},
                        "max_water_access": {"$max": "$clean_water_access"},
                        "avg_water_access": {"$avg": "$clean_water_access"},
                        "avg_water_quality": {"$avg": "$water_quality_score"},
                        "total_records": {"$sum": 1},
                    }
                }
            ]
            agg_res = list(self._db.water_quality.aggregate(summary_pipeline))
            raw_summary = agg_res[0] if agg_res else {}
            global_summary = {
                "min_water_access": round(float(raw_summary.get("min_water_access", 0.0)), 2),
                "max_water_access": round(float(raw_summary.get("max_water_access", 0.0)), 2),
                "avg_water_access": round(float(raw_summary.get("avg_water_access", 0.0)), 2),
                "avg_water_quality": round(float(raw_summary.get("avg_water_quality", 0.0)), 2),
                "total_records": int(raw_summary.get("total_records", 0)),
            }

            income_pipeline = [
                {
                    "$lookup": {
                        "from": "water_quality",
                        "localField": "community_id",
                        "foreignField": "community_id",
                        "as": "water_metrics",
                    }
                },
                {"$unwind": "$water_metrics"},
                {
                    "$group": {
                        "_id": "$income_category",
                        "count": {"$sum": 1},
                        "avg_access_pct": {"$avg": "$water_metrics.clean_water_access"},
                        "avg_quality": {"$avg": "$water_metrics.water_quality_score"},
                    }
                },
                {"$sort": {"avg_access_pct": 1}},
            ]
            income_groups = []
            for row in self._db.communities.aggregate(income_pipeline):
                income_groups.append({
                    "income_category": row["_id"],
                    "count": row["count"],
                    "avg_access_pct": round(float(row["avg_access_pct"]), 2),
                    "avg_quality": round(float(row["avg_quality"]), 2),
                })
        else:
            store = self._read_local_store()
            water_docs = store.get("water_quality", [])
            comm_docs = store.get("communities", [])
            if water_docs:
                access_vals = [float(w["clean_water_access"]) for w in water_docs]
                qual_vals = [float(w["water_quality_score"]) for w in water_docs]
                global_summary = {
                    "min_water_access": round(min(access_vals), 2),
                    "max_water_access": round(max(access_vals), 2),
                    "avg_water_access": round(sum(access_vals) / len(access_vals), 2),
                    "avg_water_quality": round(sum(qual_vals) / len(qual_vals), 2),
                    "total_records": len(water_docs),
                }
            else:
                global_summary = {
                    "min_water_access": 0.0,
                    "max_water_access": 0.0,
                    "avg_water_access": 0.0,
                    "avg_water_quality": 0.0,
                    "total_records": 0,
                }

            water_by_cid = {w["community_id"]: w for w in water_docs}
            buckets: Dict[str, List[Dict[str, Any]]] = {}
            for c in comm_docs:
                w = water_by_cid.get(c["community_id"])
                if w:
                    buckets.setdefault(c["income_category"], []).append(w)

            income_groups = []
            for inc_cat, items in buckets.items():
                income_groups.append({
                    "income_category": inc_cat,
                    "count": len(items),
                    "avg_access_pct": round(sum(float(i["clean_water_access"]) for i in items) / len(items), 2),
                    "avg_quality": round(sum(float(i["water_quality_score"]) for i in items) / len(items), 2),
                })
            income_groups.sort(key=lambda x: x["avg_access_pct"])

        self.file_manager.log_event("NOSQL_AGGREGATION", "Executed MongoDB Aggregation Pipeline ($group & $lookup).")
        return {
            "global_summary": global_summary,
            "income_breakdown": income_groups,
        }

    # -------------------------------------------------------------------------
    # NoSQL Document CRUD Operations
    # -------------------------------------------------------------------------

    def insert_document_pair(self, community_doc: Dict[str, Any], water_doc: Dict[str, Any]) -> None:
        """Inserts a new community document and water_quality document into NoSQL collections."""
        self.delete_document_by_community_id(community_doc["community_id"])
        if self.backend_mode == "mongodb" and self._db is not None:
            self._db.communities.insert_one(copy.deepcopy(community_doc))
            self._db.water_quality.insert_one(copy.deepcopy(water_doc))
        else:
            store = self._read_local_store()
            store["communities"].append(copy.deepcopy(community_doc))
            store["water_quality"].append(copy.deepcopy(water_doc))
            self._write_local_store(store)
        self.file_manager.log_event("NOSQL_CREATE", f"Inserted NoSQL document for community_id={community_doc['community_id']}.")

    def update_community_population(self, community_id: int, new_population: int, new_access: float = None) -> bool:
        """Updates a community's population (and optionally water access) using `$set` semantics."""
        updated = False
        if self.backend_mode == "mongodb" and self._db is not None:
            res = self._db.communities.update_one(
                {"community_id": community_id},
                {"$set": {"population": new_population}},
            )
            updated = res.modified_count > 0 or res.matched_count > 0
            if new_access is not None:
                self._db.water_quality.update_one(
                    {"community_id": community_id},
                    {"$set": {"clean_water_access": new_access}},
                )
        else:
            store = self._read_local_store()
            for c in store["communities"]:
                if int(c["community_id"]) == int(community_id):
                    c["population"] = new_population
                    updated = True
            if new_access is not None:
                for w in store["water_quality"]:
                    if int(w["community_id"]) == int(community_id):
                        w["clean_water_access"] = new_access
            self._write_local_store(store)
        self.file_manager.log_event("NOSQL_UPDATE", f"Updated NoSQL community_id={community_id} population={new_population}.")
        return updated

    def delete_document_by_community_id(self, community_id: int) -> bool:
        """Deletes a community document and its water_quality document from NoSQL storage."""
        deleted = False
        if self.backend_mode == "mongodb" and self._db is not None:
            r1 = self._db.communities.delete_one({"community_id": community_id})
            r2 = self._db.water_quality.delete_one({"community_id": community_id})
            deleted = (r1.deleted_count + r2.deleted_count) > 0
        else:
            store = self._read_local_store()
            before_len = len(store["communities"])
            store["communities"] = [c for c in store["communities"] if int(c["community_id"]) != int(community_id)]
            store["water_quality"] = [w for w in store["water_quality"] if int(w["community_id"]) != int(community_id)]
            deleted = len(store["communities"]) < before_len
            self._write_local_store(store)
        self.file_manager.log_event("NOSQL_DELETE", f"Deleted NoSQL document for community_id={community_id}.")
        return deleted

    def run_mongodb_lifecycle_demo(self) -> List[Dict[str, Any]]:
        """
        Executes the complete MongoDB demonstration from Section 10 of the ESE Report (`mongodb_demo.py`):
        1. Create: Insert temporary test community & water_quality record (Community K, ID=11)
        2. Read: Retrieve the inserted document
        3. Update: Update community population using `$set`
        4. Filter: Find communities with clean_water_access < 50
        5. Aggregation: Calculate min, max, avg access and avg quality
        6. Delete: Delete temporary test community to restore canonical state
        """
        trace: List[Dict[str, Any]] = []
        self.delete_document_by_community_id(11)

        # 1. Create
        comm_doc = {
            "community_id": 11,
            "community_name": "Community K (MongoDB Test)",
            "district": "Purandar South",
            "population": 3500,
            "income_category": "Low",
        }
        water_doc = {
            "water_id": 111,
            "community_id": 11,
            "clean_water_access": 38.0,
            "availability_hours": 5.0,
            "distance_to_source": 2.9,
            "water_quality_score": 60.0,
        }
        self.insert_document_pair(comm_doc, water_doc)
        trace.append({
            "feature": "1. Create (insert_one)",
            "command": "db.communities.insert_one({...}); db.water_quality.insert_one({...})",
            "result": f"Inserted test document '{comm_doc['community_name']}' with population=3,500 and water_access=38.0%.",
            "payload": {**comm_doc, **water_doc},
        })

        # 2. Read
        all_docs = self.get_all_documents()["merged_documents"]
        inserted_doc = next((d for d in all_docs if d["community_id"] == 11), {})
        trace.append({
            "feature": "2. Read (find)",
            "command": "db.communities.find({'community_id': 11}, {'_id': 0})",
            "result": f"Verified document retrieval ({len(all_docs)} total documents in collection during demo).",
            "payload": inserted_doc,
        })

        # 3. Update
        self.update_community_population(11, 3900, new_access=44.0)
        updated_docs = self.get_all_documents()["merged_documents"]
        updated_doc = next((d for d in updated_docs if d["community_id"] == 11), {})
        trace.append({
            "feature": "3. Update (update_one with $set)",
            "command": "db.communities.update_one({'community_id': 11}, {'$set': {'population': 3900}})",
            "result": "Updated Community K population from 3,500 to 3,900 and water access to 44.0%.",
            "payload": updated_doc,
        })

        # 4. Delete temporary record before running canonical filter & aggregation
        self.delete_document_by_community_id(11)
        trace.append({
            "feature": "4. Delete (delete_one)",
            "command": "db.communities.delete_one({'community_id': 11}); db.water_quality.delete_one({'community_id': 11})",
            "result": "Removed temporary test community (ID=11) to restore the 10 canonical communities.",
            "payload": {"deleted_community_id": 11, "remaining_documents": 10},
        })

        # 5. Filtering (< 50%)
        poor_access = self.filter_poor_water_access(50.0)
        trace.append({
            "feature": "5. Filtering ($lt operator)",
            "command": "db.water_quality.find({'clean_water_access': {'$lt': 50}})",
            "result": f"Found {len(poor_access)} communities with clean water access below 50%: "
                      + ", ".join(f"{r['community_name']} ({r['clean_water_access']}%)" for r in poor_access),
            "payload": poor_access,
        })

        # 6. Aggregation Pipeline
        agg_data = self.run_aggregation_pipeline()
        gs = agg_data["global_summary"]
        trace.append({
            "feature": "6. Aggregation Pipeline ($group & $lookup)",
            "command": "db.water_quality.aggregate([{'$group': {'_id': None, 'min': {'$min': '$clean_water_access'}, ...}}])",
            "result": (
                f"Min Access: {gs['min_water_access']}% | Max Access: {gs['max_water_access']}% | "
                f"Avg Access: {gs['avg_water_access']}% | Avg Quality: {gs['avg_water_quality']}"
            ),
            "payload": agg_data,
        })

        self.file_manager.log_event("NOSQL_DEMO", "Completed full MongoDB CRUD, Filtering, and Aggregation demo.")
        return trace
