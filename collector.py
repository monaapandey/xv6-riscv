import subprocess
import re
import sqlite3

# Tumhara existing database use kar rahe hain
conn = sqlite3.connect('xv6_analytics.db')
cursor = conn.cursor()

# 1. Existing Scheduling Metrics Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS process_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    exp_id INTEGER,
    pid INTEGER,
    priority INTEGER,
    algo_type TEXT DEFAULT 'Priority',
    start_time INTEGER DEFAULT 0,
    execution_time_ticks INTEGER DEFAULT 0,
    wait_time_ticks INTEGER DEFAULT 0,
    tat_ticks INTEGER DEFAULT 0
)
''')

# 2. NEW System Memory Snapshots Table
cursor.execute('''
CREATE TABLE IF NOT EXISTS system_memory_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_memory INTEGER NOT NULL,
    used_memory INTEGER NOT NULL,
    free_memory INTEGER NOT NULL,
    utilization_percentage REAL NOT NULL,
    allocated_pages INTEGER NOT NULL,
    free_pages INTEGER NOT NULL
)
''')

# 3. NEW Process Memory Stats Table
cursor.execute('''
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
)
''')
conn.commit()

print("[+] Collector active & logging BOTH Scheduling and Memory metrics ...")

process = subprocess.Popen(['make', 'qemu'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# Regex Patterns (Existing + New)
metric_pattern = re.compile(r'METRIC_LOG:\s*pid=(\d+),\s*priority=(\d+),\s*wait=(\d+),\s*exec=(\d+),\s*is_thread=(\d+)')
sys_pattern = re.compile(r"SYS_MEM_LOG:\s*total=(\d+),\s*free=(\d+),\s*used=(\d+),\s*allocs=(\d+),\s*frees=(\d+)")
proc_pattern = re.compile(r"PROC_MEM_LOG:\s*pid=(\d+),\s*asid=(\d+),\s*is_thread=(\d+),\s*name=(\S+),\s*vmem=(\d+),\s*rpages=(\d+),\s*state=(\d+)")

try:
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
        
        # --- 1. SCHEDULING METRICS LOGIC (Existing) ---
        match = metric_pattern.search(line)
        if match:
            pid = int(match.group(1))
            prio = int(match.group(2))
            wait = int(match.group(3))
            exec_ticks = int(match.group(4))
            is_thread = int(match.group(5))
            
            tat = exec_ticks + wait
            algo_name = 'Priority (Thread)' if is_thread == 1 else 'Priority'
            
            cursor.execute('''
                INSERT INTO process_metrics (exp_id, pid, priority, algo_type, start_time, execution_time_ticks, wait_time_ticks, tat_ticks)
                VALUES (300, ?, ?, ?, 0, ?, ?, ?)
            ''', (pid, prio, algo_name, exec_ticks, wait, tat))
            conn.commit()
            print(f"  [+] SCHEDULING LOGGED -> PID: {pid} [{algo_name}]")
        
        # --- 2. SYSTEM MEMORY LOGIC (New) ---
        sys_match = sys_pattern.search(line)
        if sys_match:
            total, free, used, allocs, frees = map(int, sys_match.groups())
            utilization = (used / total * 100.0) if total > 0 else 0.0
            
            cursor.execute('''
                INSERT INTO system_memory_snapshots 
                (total_memory, used_memory, free_memory, utilization_percentage, allocated_pages, free_pages)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (total * 4096, used * 4096, free * 4096, utilization, allocs, frees))
            conn.commit()
            print(f"  [+] SYS_MEM LOGGED -> Used: {used} pages")

        # --- 3. PROCESS MEMORY LOGIC (New) ---
        proc_match = proc_pattern.search(line)
        if proc_match:
            pid, asid, is_thread, name, vmem, rpages, state = proc_match.groups()
            pid, asid, is_thread = int(pid), int(asid), int(is_thread)
            vmem, rpages, state = int(vmem), int(rpages), int(state)
            rmem = rpages * 4096

            cursor.execute('''
                INSERT INTO process_memory_stats 
                (pid, asid, is_thread, process_name, virtual_memory, resident_memory, resident_pages, process_state)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pid, asid, is_thread, name, vmem, rmem, rpages, state))
            conn.commit()
            # print(f"  [+] PROC_MEM LOGGED -> PID: {pid} Resident: {rpages} pages")

except KeyboardInterrupt:
    print("\n[+] Stopping Collector...")
finally:
    conn.close()
    process.terminate()