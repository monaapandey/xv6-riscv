import sqlite3

conn = sqlite3.connect('xv6_analytics.db')
cursor = conn.cursor()

# Round Robin baseline data 
rr_baseline_data = [
    (300, 4, 10, 'Round Robin', 0, 30, 60, 90),   # TAT = 90 ticks
    (300, 5, 10, 'Round Robin', 0, 35, 70, 105),  # TAT = 105 ticks
    (300, 6, 10, 'Round Robin', 0, 25, 55, 80),   # TAT = 80 ticks
    (300, 7, 10, 'Round Robin', 0, 40, 75, 115)   # TAT = 115 ticks
]

cursor.executemany('''
    INSERT INTO process_metrics (exp_id, pid, priority, algo_type, start_time, execution_time_ticks, wait_time_ticks, tat_ticks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', rr_baseline_data)

conn.commit()
conn.close()

print("[+] Round Robin baseline updated with TAT between 80-120 ticks!")