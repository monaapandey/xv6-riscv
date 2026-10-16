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
    tat_ticks INTEGER DEFAULT 0
)
''')
conn.commit()

print("[+] Collector active & logging metrics ...")

process = subprocess.Popen(['make', 'qemu'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# Regex jo is_thread flag bhi catch kare (kexit update ke mutabiq)
metric_pattern = re.compile(r'METRIC_LOG:\s*pid=(\d+),\s*priority=(\d+),\s*wait=(\d+),\s*exec=(\d+),\s*is_thread=(\d+)')

try:
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
        
        match = metric_pattern.search(line)
        if match:
            pid = int(match.group(1))
            prio = int(match.group(2))
            wait = int(match.group(3))
            exec_ticks = int(match.group(4))
            is_thread = int(match.group(5))
            
            tat = exec_ticks + wait
            
            # Agar process thread hai toh 'Priority (Thread)', warna normal 'Priority'
            algo_name = 'Priority (Thread)' if is_thread == 1 else 'Priority'
            
            cursor.execute('''
                INSERT INTO process_metrics (exp_id, pid, priority, algo_type, start_time, execution_time_ticks, wait_time_ticks, tat_ticks)
                VALUES (300, ?, ?, ?, 0, ?, ?, ?)
            ''', (pid, prio, algo_name, exec_ticks, wait, tat))
            
            conn.commit()
            print(f"  [+] LIVE METRIC LOGGED -> PID: {pid} [{algo_name}]")

except KeyboardInterrupt:
    print("\n[+] Stopping Collector...")
finally:
    conn.close()
    process.terminate()