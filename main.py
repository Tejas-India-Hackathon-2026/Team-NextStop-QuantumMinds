import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self, db_name="bharat_pragati.db"):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                transaction_time TEXT NOT NULL,
                is_new_recipient INTEGER NOT NULL,
                recipient_history INTEGER NOT NULL,
                risk_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                risk_factors TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database '{self.db_name}' initialized successfully!")
    
    def save_transaction(self, amount, transaction_time, is_new_recipient, 
                        recipient_history, risk_score, risk_level, 
                        risk_factors, recommendation):
        """Save transaction to database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions 
                (amount, transaction_time, is_new_recipient, recipient_history, 
                 risk_score, risk_level, risk_factors, recommendation, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                amount,
                str(transaction_time),
                1 if is_new_recipient else 0,
                recipient_history,
                risk_score,
                risk_level,
                str(risk_factors),
                recommendation,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error saving transaction: {e}")
            return False
    
    def get_all_transactions(self):
        """Get all transactions from database"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, amount, transaction_time, is_new_recipient, 
                       recipient_history, risk_score, risk_level, timestamp
                FROM transactions
                ORDER BY id DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            transactions = []
            for row in rows:
                transactions.append({
                    "ID": row[0],
                    "Amount (₹)": row[1],
                    "Time": row[2],
                    "New Recipient": "Yes" if row[3] else "No",
                    "History Count": row[4],
                    "Risk Score": row[5],
                    "Risk Level": row[6],
                    "Analyzed At": row[7]
                })
            
            return transactions
        except Exception as e:
            print(f"❌ Error fetching transactions: {e}")
            return []
    
    def get_transaction_stats(self):
        """Get transaction statistics"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Total transactions
            cursor.execute('SELECT COUNT(*) FROM transactions')
            total = cursor.fetchone()[0]
            
            # High risk count
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE risk_score >= 70")
            high_risk = cursor.fetchone()[0]
            
            # Medium risk count
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE risk_score >= 40 AND risk_score < 70")
            medium_risk = cursor.fetchone()[0]
            
            # Low risk count
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE risk_score < 40")
            low_risk = cursor.fetchone()[0]
            
            # Average risk score
            cursor.execute("SELECT AVG(risk_score) FROM transactions")
            avg_risk = cursor.fetchone()[0] or 0
            
            # Total amount analyzed
            cursor.execute("SELECT SUM(amount) FROM transactions")
            total_amount = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total": total,
                "high_risk": high_risk,
                "medium_risk": medium_risk,
                "low_risk": low_risk,
                "average_risk": round(avg_risk, 2),
                "total_amount": total_amount
            }
        except Exception as e:
            print(f"❌ Error fetching stats: {e}")
            return {}
    
    def delete_all_transactions(self):
        """Clear all transactions (useful for testing)"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transactions')
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error deleting transactions: {e}")
            return False