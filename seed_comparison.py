import sqlite3

conn = sqlite3.connect('xv6_analytics.db')
cursor = conn.cursor()

# 1. Existing table mein missing columns safely add karte hain
new_columns = [
    ("algo_type", "TEXT DEFAULT 'Priority'"),
    ("start_time", "INTEGER DEFAULT 0"),
    ("tat_ticks", "INTEGER DEFAULT 0"),
    ("rt_ticks", "INTEGER DEFAULT 0")
]

for col_name, col_type in new_columns:
    try:
        cursor.execute(f"ALTER TABLE process_metrics ADD COLUMN {col_name} {col_type};")
    except sqlite3.OperationalError:
        # Column pehle se majood hai to skip karo
        pass

# 2. Round Robin benchmark data insert karte hain (Exact column names ke saath)
rr_data = [
    (100, 4, 0, 'Round Robin', 2, 4, 12, 16, 3),
    (100, 5, 0, 'Round Robin', 2, 7, 18, 25, 5),
    (100, 6, 0, 'Round Robin', 3, 3, 15, 18, 4),
    (100, 7, 0, 'Round Robin', 3, 3, 20, 23, 6),
]

for row in rr_data:
    cursor.execute('''
        INSERT INTO process_metrics (exp_id, pid, priority, algo_type, start_time, execution_time_ticks, wait_time_ticks, tat_ticks, rt_ticks)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', row)

# 3. Existing Priority Scheduler records ki values calculate aur update karte hain
cursor.execute("UPDATE process_metrics SET algo_type = 'Priority' WHERE algo_type IS NULL OR algo_type = ''")
cursor.execute("UPDATE process_metrics SET tat_ticks = execution_time_ticks + wait_time_ticks WHERE tat_ticks = 0 OR tat_ticks IS NULL")
cursor.execute("UPDATE process_metrics SET rt_ticks = wait_time_ticks WHERE rt_ticks = 0 OR rt_ticks IS NULL")

conn.commit()
conn.close()
print("[+] Comparison Data successfully integrated into existing database schema!")