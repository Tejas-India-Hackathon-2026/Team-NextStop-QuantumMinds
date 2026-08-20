import sqlite3

connection = sqlite3.connect(
    "transactions.db",
    check_same_thread=False
)

cursor = connection.cursor()

cursor.execute("""

CREATE TABLE IF NOT EXISTS transactions(

id INTEGER PRIMARY KEY AUTOINCREMENT,

amount REAL,

timestamp TEXT,

device TEXT,

location TEXT,

beneficiary TEXT,

risk_score INTEGER,

decision TEXT

)

""")

connection.commit()