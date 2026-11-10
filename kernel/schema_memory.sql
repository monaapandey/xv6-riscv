CREATE TABLE IF NOT EXISTS system_memory_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_memory INTEGER NOT NULL,
    used_memory INTEGER NOT NULL,
    free_memory INTEGER NOT NULL,
    utilization_percentage REAL NOT NULL,
    allocated_pages INTEGER NOT NULL,
    free_pages INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS process_memory_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    pid INTEGER NOT NULL,
    asid INTEGER NOT NULL,
    is_thread INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    virtual_memory INTEGER NOT NULL,
    resident_memory INTEGER NOT NULL,
    resident_pages INTEGER NOT NULL,
    process_state INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sys_time ON system_memory_snapshots(timestamp);
CREATE INDEX IF NOT EXISTS idx_proc_pid ON process_memory_stats(pid);
CREATE INDEX IF NOT EXISTS idx_proc_asid ON process_memory_stats(asid);