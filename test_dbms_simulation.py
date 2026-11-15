import tempfile
import unittest
from pathlib import Path

from dbms_simulation import (
    delete_simulation,
    list_simulations,
    save_paging_simulation,
    save_scheduling_simulation,
    simulate_paging,
    simulate_scheduling,
)
from dbms_store import initialize_database


class SimulationAlgorithmTests(unittest.TestCase):
    def test_fcfs_accounts_for_arrival_time(self):
        result = simulate_scheduling({
            "name": "FCFS test",
            "algorithm": "FCFS",
            "processes": [
                {"arrival_time": 0, "burst_time": 5, "priority": 2},
                {"arrival_time": 2, "burst_time": 3, "priority": 1},
            ],
        })
        self.assertEqual(result["results"][1]["completion_time"], 8)
        self.assertEqual(result["results"][1]["waiting_time"], 3)
        self.assertEqual(result["summary"]["average_turnaround_time"], 5.5)

    def test_srtf_preempts_the_running_process(self):
        result = simulate_scheduling({
            "name": "SRTF test",
            "algorithm": "SRTF",
            "processes": [
                {"arrival_time": 0, "burst_time": 8, "priority": 2},
                {"arrival_time": 1, "burst_time": 4, "priority": 1},
            ],
        })
        self.assertEqual(result["results"][0]["completion_time"], 12)
        self.assertEqual(result["results"][1]["completion_time"], 5)

    def test_round_robin_respects_quantum(self):
        result = simulate_scheduling({
            "name": "RR test",
            "algorithm": "Round Robin",
            "quantum": 2,
            "processes": [
                {"arrival_time": 0, "burst_time": 5, "priority": 1},
                {"arrival_time": 0, "burst_time": 3, "priority": 1},
            ],
        })
        self.assertEqual(
            [process["completion_time"] for process in result["results"]],
            [8, 7],
        )

    def test_priority_uses_lower_number_first(self):
        result = simulate_scheduling({
            "name": "Priority test",
            "algorithm": "Priority",
            "processes": [
                {"arrival_time": 0, "burst_time": 2, "priority": 5},
                {"arrival_time": 0, "burst_time": 1, "priority": 1},
            ],
        })
        self.assertEqual(result["results"][1]["start_time"], 0)
        self.assertEqual(result["results"][0]["start_time"], 1)

    def test_fifo_and_lru_count_faults_for_their_own_policies(self):
        references = "1 2 3 1 4 2 5"
        fifo = simulate_paging({
            "name": "FIFO test",
            "algorithm": "FIFO",
            "frame_count": 3,
            "references": references,
        })
        lru = simulate_paging({
            "name": "LRU test",
            "algorithm": "LRU",
            "frame_count": 3,
            "references": references,
        })
        self.assertEqual(fifo["summary"]["faults"], 5)
        self.assertEqual(lru["summary"]["faults"], 6)

    def test_rejects_empty_or_invalid_simulation_input(self):
        with self.assertRaises(ValueError):
            simulate_scheduling({
                "name": "invalid",
                "algorithm": "FCFS",
                "processes": [],
            })
        with self.assertRaises(ValueError):
            simulate_paging({
                "name": "invalid",
                "algorithm": "LRU",
                "frame_count": 2,
                "references": "1 x 3",
            })
        with self.assertRaises(ValueError):
            simulate_scheduling({
                "name": "invalid",
                "algorithm": ["FCFS"],
                "processes": [
                    {"arrival_time": 0, "burst_time": 1, "priority": 1},
                ],
            })


class SimulationPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "simulation.db"
        initialize_database(self.database_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_simulations_are_stored_and_deleted_separately(self):
        schedule = save_scheduling_simulation({
            "name": "Schedule run",
            "algorithm": "FCFS",
            "processes": [
                {"arrival_time": 0, "burst_time": 4, "priority": 1},
            ],
        }, self.database_path)
        paging = save_paging_simulation({
            "name": "Paging run",
            "algorithm": "FIFO",
            "frame_count": 2,
            "references": "1, 2, 1",
        }, self.database_path)

        saved = list_simulations(self.database_path)
        self.assertEqual([run["simulation_type"] for run in saved], ["paging", "scheduling"])
        self.assertEqual(len(saved[0]["results"]), 3)
        self.assertEqual(len(saved[1]["results"]), 1)
        self.assertTrue(delete_simulation(schedule["run_id"], self.database_path))
        self.assertEqual(
            [run["simulation_type"] for run in list_simulations(self.database_path)],
            ["paging"],
        )


if __name__ == "__main__":
    unittest.main()
