CREATE TABLE IF NOT EXISTS dbms_experiments (
    experiment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 100),
    scheduler TEXT NOT NULL,
    paging TEXT NOT NULL,
    workload TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dbms_experiments_created_at
    ON dbms_experiments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dbms_experiments_scheduler
    ON dbms_experiments(scheduler);

CREATE TABLE IF NOT EXISTS dbms_simulation_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 100),
    simulation_type TEXT NOT NULL CHECK(simulation_type IN ('scheduling', 'paging')),
    algorithm TEXT NOT NULL,
    inputs_json TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dbms_simulation_runs_created_at
    ON dbms_simulation_runs(created_at DESC);

CREATE TABLE IF NOT EXISTS dbms_schedule_results (
    run_id INTEGER NOT NULL REFERENCES dbms_simulation_runs(run_id) ON DELETE CASCADE,
    process_order INTEGER NOT NULL,
    pid TEXT NOT NULL,
    arrival_time INTEGER NOT NULL,
    burst_time INTEGER NOT NULL,
    priority INTEGER NOT NULL,
    start_time INTEGER NOT NULL,
    completion_time INTEGER NOT NULL,
    turnaround_time INTEGER NOT NULL,
    waiting_time INTEGER NOT NULL,
    response_time INTEGER NOT NULL,
    PRIMARY KEY (run_id, process_order)
);

CREATE TABLE IF NOT EXISTS dbms_paging_steps (
    run_id INTEGER NOT NULL REFERENCES dbms_simulation_runs(run_id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    page INTEGER NOT NULL,
    hit INTEGER NOT NULL CHECK(hit IN (0, 1)),
    frames_json TEXT NOT NULL,
    evicted_page INTEGER,
    PRIMARY KEY (run_id, step_index)
);
