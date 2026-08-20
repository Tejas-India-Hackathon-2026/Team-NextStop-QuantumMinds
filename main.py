import sqlite3

DATABASE_NAME = "transactions.db"


def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False
    )

    return connection


def create_tables():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            amount REAL NOT NULL,

            timestamp TEXT,

            device TEXT,

            location TEXT,

            beneficiary TEXT,

            risk_score INTEGER,

            decision TEXT

        )
    """)

    connection.commit()

    connection.close()