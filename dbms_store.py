from contextlib import contextmanager
import sqlite3
from pathlib import Path


DATABASE_PATH = Path(__file__).resolve().with_name("xv6_analytics.db")
SCHEMA_PATH = Path(__file__).resolve().with_name("dbms_schema.sql")
SCHEDULERS = {"Priority", "Round Robin", "FCFS", "SJF", "SRTF", "LJF", "Other"}
PAGING_POLICIES = {"FIFO", "LRU", "Other"}
FIELDS = ("name", "scheduler", "paging", "workload", "notes")


@contextmanager
def connect(database_path=DATABASE_PATH):
    connection = sqlite3.connect(database_path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path=DATABASE_PATH):
    with open(SCHEMA_PATH, encoding="utf-8") as schema_file:
        schema = schema_file.read()
    with connect(database_path) as connection:
        connection.executescript(schema)


def _validate_experiment(experiment):
    if not isinstance(experiment, dict):
        raise ValueError("Expected an experiment object.")

    values = {}
    for field in FIELDS:
        value = experiment.get(field, "")
        if not isinstance(value, str):
            raise ValueError(f"{field} must be text.")
        values[field] = value.strip()

    if not values["name"] or len(values["name"]) > 100:
        raise ValueError("Name must contain 1 to 100 characters.")
    if values["scheduler"] not in SCHEDULERS:
        raise ValueError("Choose a supported scheduler.")
    if values["paging"] not in PAGING_POLICIES:
        raise ValueError("Choose a supported paging policy.")
    if not values["workload"] or len(values["workload"]) > 120:
        raise ValueError("Workload must contain 1 to 120 characters.")
    if len(values["notes"]) > 1000:
        raise ValueError("Notes must be 1000 characters or fewer.")
    return values


def list_experiments(search="", database_path=DATABASE_PATH):
    if not isinstance(search, str):
        raise ValueError("Search must be text.")
    search = search.strip()
    if len(search) > 100:
        raise ValueError("Search must be 100 characters or fewer.")

    query = """
        SELECT experiment_id, name, scheduler, paging, workload, notes,
               created_at, updated_at
        FROM dbms_experiments
    """
    parameters = ()
    if search:
        query += """
            WHERE name LIKE ? OR scheduler LIKE ? OR paging LIKE ?
               OR workload LIKE ? OR notes LIKE ?
        """
        pattern = f"%{search}%"
        parameters = (pattern,) * 5
    query += " ORDER BY experiment_id DESC"

    with connect(database_path) as connection:
        return [dict(row) for row in connection.execute(query, parameters)]


def save_experiment(experiment, experiment_id=None, database_path=DATABASE_PATH):
    values = _validate_experiment(experiment)
    with connect(database_path) as connection:
        if experiment_id is None:
            cursor = connection.execute(
                """
                INSERT INTO dbms_experiments
                    (name, scheduler, paging, workload, notes)
                VALUES (:name, :scheduler, :paging, :workload, :notes)
                """,
                values,
            )
            saved_id = cursor.lastrowid
        else:
            if not isinstance(experiment_id, int) or experiment_id < 1:
                raise ValueError("Experiment ID must be a positive integer.")
            cursor = connection.execute(
                """
                UPDATE dbms_experiments
                SET name = :name, scheduler = :scheduler, paging = :paging,
                    workload = :workload, notes = :notes,
                    updated_at = CURRENT_TIMESTAMP
                WHERE experiment_id = :experiment_id
                """,
                {**values, "experiment_id": experiment_id},
            )
            if cursor.rowcount == 0:
                return None
            saved_id = experiment_id
        row = connection.execute(
            """
            SELECT experiment_id, name, scheduler, paging, workload, notes,
                   created_at, updated_at
            FROM dbms_experiments
            WHERE experiment_id = ?
            """,
            (saved_id,),
        ).fetchone()
        return dict(row)


def delete_experiment(experiment_id, database_path=DATABASE_PATH):
    if not isinstance(experiment_id, int) or experiment_id < 1:
        raise ValueError("Experiment ID must be a positive integer.")
    with connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM dbms_experiments WHERE experiment_id = ?",
            (experiment_id,),
        )
        return cursor.rowcount > 0
