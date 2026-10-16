import subprocess
import re
import sqlite3

conn = sqlite3.connect('xv6_analytics.db')
cursor = conn.cursor()

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
    tat_ticks INTEGER DEFAULT 0,
    rt_ticks INTEGER DEFAULT 0
)
''')
conn.commit()

print("[+] Collector active & logging LIVE Priority Scheduler metrics only...")

process = subprocess.Popen(['make', 'qemu'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

metric_pattern = re.compile(r'METRIC_LOG:\s*pid=(\d+),\s*priority=(\d+),\s*wait=(\d+),\s*exec=(\d+)')

try:
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
        
        match = metric_pattern.search(line)
        if match:
            pid = int(match.group(1))
            prio = int(match.group(2))
            wait = int(match.group(3))
            exec_ticks = int(match.group(4))
            
            tat = exec_ticks + wait
            rt = wait
            
            # ONLY Priority Scheduler real metric logged
            cursor.execute('''
                INSERT INTO process_metrics (exp_id, pid, priority, algo_type, start_time, execution_time_ticks, wait_time_ticks, tat_ticks, rt_ticks)
                VALUES (300, ?, ?, 'Priority', 0, ?, ?, ?, ?)
            ''', (pid, prio, exec_ticks, wait, tat, rt))
            
            conn.commit()
            print(f"  [+] LIVE PRIORITY METRIC LOGGED -> PID: {pid}")

except KeyboardInterrupt:
    print("\n[+] Stopping Collector...")
finally:
    conn.close()
    process.terminate()