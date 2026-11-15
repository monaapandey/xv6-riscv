import tempfile
import unittest
from pathlib import Path

from dbms_store import (
    delete_experiment,
    initialize_database,
    list_experiments,
    save_experiment,
)


class ExperimentStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        initialize_database(self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def experiment(self, **overrides):
        values = {
            "name": "Baseline",
            "scheduler": "Priority",
            "paging": "FIFO",
            "workload": "short-processes",
            "notes": "",
        }
        values.update(overrides)
        return values

    def test_create_search_update_and_delete(self):
        created = save_experiment(self.experiment(), database_path=self.database_path)
        self.assertEqual(created["name"], "Baseline")
        self.assertEqual(len(list_experiments("short", self.database_path)), 1)

        updated = save_experiment(
            self.experiment(name="Updated"),
            experiment_id=created["experiment_id"],
            database_path=self.database_path,
        )
        self.assertEqual(updated["name"], "Updated")
        self.assertEqual(list_experiments("Baseline", self.database_path), [])
        self.assertTrue(delete_experiment(created["experiment_id"], self.database_path))
        self.assertEqual(list_experiments(database_path=self.database_path), [])

    def test_validation_rejects_invalid_scheduler(self):
        with self.assertRaises(ValueError):
            save_experiment(
                self.experiment(scheduler="not-a-scheduler"),
                database_path=self.database_path,
            )

    def test_update_missing_record_returns_none(self):
        self.assertIsNone(
            save_experiment(
                self.experiment(),
                experiment_id=99,
                database_path=self.database_path,
            )
        )


if __name__ == "__main__":
    unittest.main()
