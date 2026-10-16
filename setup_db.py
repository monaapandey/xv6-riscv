import sqlite3

def setup_database():
    # Ye xv6_analytics.db naam ki file banayega (agar nahi hai to)
    conn = sqlite3.connect('xv6_analytics.db')
    cursor = conn.cursor()

    # 1. Experiments table: Track karega ki data Original ka hai ya Modified ka
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiments (
            exp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            kernel_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Process Metrics table: xv6 se aane wala har process ka data yahan aayega
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS process_metrics (
            metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exp_id INTEGER,
            pid INTEGER,
            priority INTEGER,
            wait_time_ticks INTEGER,
            execution_time_ticks INTEGER,
            FOREIGN KEY(exp_id) REFERENCES experiments(exp_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("Success: Database 'xv6_analytics.db' aur tables successfully create ho gaye hain!")

if __name__ == "__main__":
    setup_database()