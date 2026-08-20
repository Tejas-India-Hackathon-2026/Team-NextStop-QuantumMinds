def initialize_database():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            amount REAL NOT NULL,

            average_amount REAL,

            device TEXT,

            location TEXT,

            transaction_time TEXT,

            beneficiary TEXT,

            recent_transactions INTEGER,

            behaviour_score REAL,

            ml_score REAL,

            final_score REAL,

            risk_level TEXT,

            decision TEXT,

            reasons TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()