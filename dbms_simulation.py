from collections import deque
import json
import re

from dbms_store import DATABASE_PATH, connect, initialize_database


SCHEDULING_ALGORITHMS = {"FCFS", "SJF", "SRTF", "Priority", "Round Robin"}
PAGING_ALGORITHMS = {"FIFO", "LRU"}


def _validate_name(name):
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 100:
        raise ValueError("Run name must contain 1 to 100 characters.")
    return name.strip()


def _validate_integer(value, field, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} must be an integer.")
    if value < minimum or value > maximum:
        raise ValueError(f"{field} must be between {minimum} and {maximum}.")
    return value


def _validate_scheduling(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected a scheduling simulation object.")
    name = _validate_name(payload.get("name"))
    algorithm = payload.get("algorithm")
    if not isinstance(algorithm, str) or algorithm not in SCHEDULING_ALGORITHMS:
        raise ValueError("Choose a supported scheduling algorithm.")

    raw_processes = payload.get("processes")
    if not isinstance(raw_processes, list) or not 1 <= len(raw_processes) <= 20:
        raise ValueError("Enter between 1 and 20 processes.")

    processes = []
    for index, process in enumerate(raw_processes, start=1):
        if not isinstance(process, dict):
            raise ValueError(f"Process {index} must be an object.")
        processes.append({
            "arrival_time": _validate_integer(
                process.get("arrival_time"), f"Process {index} arrival time", 0, 100000
            ),
            "burst_time": _validate_integer(
                process.get("burst_time"), f"Process {index} burst time", 1, 10000
            ),
            "priority": _validate_integer(
                process.get("priority"), f"Process {index} priority", 0, 10
            ),
        })

    quantum = None
    if algorithm == "Round Robin":
        quantum = _validate_integer(payload.get("quantum"), "Time quantum", 1, 1000)
    return name, algorithm, processes, quantum


def simulate_scheduling(payload):
    name, algorithm, processes, quantum = _validate_scheduling(payload)
    count = len(processes)
    remaining = [process["burst_time"] for process in processes]
    starts = [None] * count
    completions = [None] * count
    time = 0

    if algorithm == "SRTF":
        finished = 0
        while finished < count:
            ready = [
                index for index, process in enumerate(processes)
                if process["arrival_time"] <= time and remaining[index] > 0
            ]
            if not ready:
                time = min(
                    process["arrival_time"]
                    for index, process in enumerate(processes)
                    if remaining[index] > 0
                )
                continue
            chosen = min(
                ready,
                key=lambda index: (
                    remaining[index], processes[index]["arrival_time"], index
                ),
            )
            if starts[chosen] is None:
                starts[chosen] = time
            remaining[chosen] -= 1
            time += 1
            if remaining[chosen] == 0:
                completions[chosen] = time
                finished += 1
    elif algorithm == "Round Robin":
        order = sorted(
            range(count),
            key=lambda index: (processes[index]["arrival_time"], index),
        )
        next_arrival = 0
        ready = deque()
        finished = 0
        while finished < count:
            if not ready:
                time = max(time, processes[order[next_arrival]]["arrival_time"])
            while (
                next_arrival < count
                and processes[order[next_arrival]]["arrival_time"] <= time
            ):
                ready.append(order[next_arrival])
                next_arrival += 1

            chosen = ready.popleft()
            if starts[chosen] is None:
                starts[chosen] = time
            duration = min(quantum, remaining[chosen])
            time += duration
            remaining[chosen] -= duration

            while (
                next_arrival < count
                and processes[order[next_arrival]]["arrival_time"] <= time
            ):
                ready.append(order[next_arrival])
                next_arrival += 1

            if remaining[chosen] > 0:
                ready.append(chosen)
            else:
                completions[chosen] = time
                finished += 1
    else:
        pending = set(range(count))
        while pending:
            ready = [
                index for index in pending
                if processes[index]["arrival_time"] <= time
            ]
            if not ready:
                time = min(processes[index]["arrival_time"] for index in pending)
                ready = [
                    index for index in pending
                    if processes[index]["arrival_time"] <= time
                ]

            if algorithm == "FCFS":
                key = lambda index: (processes[index]["arrival_time"], index)
            elif algorithm == "SJF":
                key = lambda index: (
                    processes[index]["burst_time"],
                    processes[index]["arrival_time"],
                    index,
                )
            else:
                key = lambda index: (
                    processes[index]["priority"],
                    processes[index]["arrival_time"],
                    index,
                )
            chosen = min(ready, key=key)
            starts[chosen] = time
            time += processes[chosen]["burst_time"]
            completions[chosen] = time
            pending.remove(chosen)

    results = []
    for index, process in enumerate(processes):
        turnaround = completions[index] - process["arrival_time"]
        results.append({
            "pid": f"P{index + 1}",
            **process,
            "start_time": starts[index],
            "completion_time": completions[index],
            "turnaround_time": turnaround,
            "waiting_time": turnaround - process["burst_time"],
            "response_time": starts[index] - process["arrival_time"],
        })

    summary = {
        "process_count": count,
        "average_turnaround_time": round(
            sum(result["turnaround_time"] for result in results) / count, 2
        ),
        "average_waiting_time": round(
            sum(result["waiting_time"] for result in results) / count, 2
        ),
        "average_response_time": round(
            sum(result["response_time"] for result in results) / count, 2
        ),
    }
    inputs = {"processes": processes, "quantum": quantum}
    return {
        "name": name,
        "simulation_type": "scheduling",
        "algorithm": algorithm,
        "inputs": inputs,
        "summary": summary,
        "results": results,
    }


def _validate_paging(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected a paging simulation object.")
    name = _validate_name(payload.get("name"))
    algorithm = payload.get("algorithm")
    if not isinstance(algorithm, str) or algorithm not in PAGING_ALGORITHMS:
        raise ValueError("Choose FIFO or LRU.")
    frame_count = _validate_integer(payload.get("frame_count"), "Frame count", 1, 32)

    raw_references = payload.get("references")
    if isinstance(raw_references, str):
        if len(raw_references) > 3000:
            raise ValueError("Page reference input is too long.")
        tokens = [token for token in re.split(r"[\s,]+", raw_references.strip()) if token]
        try:
            references = [int(token) for token in tokens]
        except ValueError as error:
            raise ValueError("References must be non-negative integers separated by commas or spaces.") from error
    elif isinstance(raw_references, list):
        references = raw_references
    else:
        raise ValueError("Enter a page reference string.")

    if not 1 <= len(references) <= 500:
        raise ValueError("Enter between 1 and 500 page references.")
    references = [
        _validate_integer(page, f"Reference {index}", 0, 1000000)
        for index, page in enumerate(references, start=1)
    ]
    return name, algorithm, frame_count, references


def simulate_paging(payload):
    name, algorithm, frame_count, references = _validate_paging(payload)
    frames = []
    steps = []
    hits = 0
    faults = 0

    for index, page in enumerate(references, start=1):
        evicted_page = None
        if page in frames:
            hits += 1
            if algorithm == "LRU":
                frames.remove(page)
                frames.append(page)
            hit = True
        else:
            faults += 1
            hit = False
            if len(frames) == frame_count:
                evicted_page = frames.pop(0)
            frames.append(page)
        steps.append({
            "step_index": index,
            "page": page,
            "hit": hit,
            "frames": list(frames),
            "evicted_page": evicted_page,
        })

    reference_count = len(references)
    summary = {
        "reference_count": reference_count,
        "hits": hits,
        "faults": faults,
        "hit_ratio_percent": round(hits * 100 / reference_count, 2),
        "fault_ratio_percent": round(faults * 100 / reference_count, 2),
    }
    inputs = {"frame_count": frame_count, "references": references}
    return {
        "name": name,
        "simulation_type": "paging",
        "algorithm": algorithm,
        "inputs": inputs,
        "summary": summary,
        "results": steps,
    }


def _save_run(simulation, database_path):
    initialize_database(database_path)
    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO dbms_simulation_runs
                (name, simulation_type, algorithm, inputs_json, summary_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                simulation["name"],
                simulation["simulation_type"],
                simulation["algorithm"],
                json.dumps(simulation["inputs"]),
                json.dumps(simulation["summary"]),
            ),
        )
        run_id = cursor.lastrowid
        if simulation["simulation_type"] == "scheduling":
            connection.executemany(
                """
                INSERT INTO dbms_schedule_results
                    (run_id, process_order, pid, arrival_time, burst_time, priority,
                     start_time, completion_time, turnaround_time, waiting_time,
                     response_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        index,
                        result["pid"],
                        result["arrival_time"],
                        result["burst_time"],
                        result["priority"],
                        result["start_time"],
                        result["completion_time"],
                        result["turnaround_time"],
                        result["waiting_time"],
                        result["response_time"],
                    )
                    for index, result in enumerate(simulation["results"])
                ],
            )
        else:
            connection.executemany(
                """
                INSERT INTO dbms_paging_steps
                    (run_id, step_index, page, hit, frames_json, evicted_page)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        step["step_index"],
                        step["page"],
                        int(step["hit"]),
                        json.dumps(step["frames"]),
                        step["evicted_page"],
                    )
                    for step in simulation["results"]
                ],
            )
    return get_simulation(run_id, database_path)


def save_scheduling_simulation(payload, database_path=DATABASE_PATH):
    return _save_run(simulate_scheduling(payload), database_path)


def save_paging_simulation(payload, database_path=DATABASE_PATH):
    return _save_run(simulate_paging(payload), database_path)


def get_simulation(run_id, database_path=DATABASE_PATH):
    if not isinstance(run_id, int) or run_id < 1:
        raise ValueError("Run ID must be a positive integer.")
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM dbms_simulation_runs WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None

        simulation = dict(row)
        simulation["inputs"] = json.loads(simulation.pop("inputs_json"))
        simulation["summary"] = json.loads(simulation.pop("summary_json"))
        if simulation["simulation_type"] == "scheduling":
            simulation["results"] = [
                dict(result)
                for result in connection.execute(
                    """
                    SELECT pid, arrival_time, burst_time, priority, start_time,
                           completion_time, turnaround_time, waiting_time,
                           response_time
                    FROM dbms_schedule_results
                    WHERE run_id = ? ORDER BY process_order
                    """,
                    (run_id,),
                )
            ]
        else:
            simulation["results"] = [
                {
                    "step_index": result["step_index"],
                    "page": result["page"],
                    "hit": bool(result["hit"]),
                    "frames": json.loads(result["frames_json"]),
                    "evicted_page": result["evicted_page"],
                }
                for result in connection.execute(
                    """
                    SELECT step_index, page, hit, frames_json, evicted_page
                    FROM dbms_paging_steps
                    WHERE run_id = ? ORDER BY step_index
                    """,
                    (run_id,),
                )
            ]
        return simulation


def list_simulations(database_path=DATABASE_PATH, limit=50):
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")
    with connect(database_path) as connection:
        run_ids = [
            row["run_id"]
            for row in connection.execute(
                "SELECT run_id FROM dbms_simulation_runs ORDER BY run_id DESC LIMIT ?",
                (limit,),
            )
        ]
    return [
        get_simulation(run_id, database_path)
        for run_id in run_ids
    ]


def delete_simulation(run_id, database_path=DATABASE_PATH):
    if not isinstance(run_id, int) or run_id < 1:
        raise ValueError("Run ID must be a positive integer.")
    with connect(database_path) as connection:
        cursor = connection.execute(
            "DELETE FROM dbms_simulation_runs WHERE run_id = ?",
            (run_id,),
        )
        return cursor.rowcount > 0
