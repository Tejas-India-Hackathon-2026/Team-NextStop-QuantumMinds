import sqlite3

DATABASE = "SecureFlow-AI.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ============================================================
# TEST DATABASE CONNECTION
# ============================================================

def test_connection():
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
            """)

            tables = cursor.fetchall()

        print()
        print("=" * 60)
        print("       SECUREFLOW-AI DATABASE CONNECTION")
        print("=" * 60)
        print()
        print("Database connected successfully!")
        print()
        print("Tables found:")

        if tables:
            for table in tables:
                print("  ✓", table["name"])
        else:
            print("  No tables found.")

        print()

    except sqlite3.Error as error:
        print()
        print("DATABASE ERROR:", error)
        print()


# ============================================================
# GET ALL USERS
# ============================================================

def get_all_users():
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    user_id,
                    name,
                    phone,
                    average_transaction,
                    normal_start_time,
                    normal_end_time,
                    typical_daily_transactions,
                    known_device,
                    common_location
                FROM users
                ORDER BY user_id
            """)

            return cursor.fetchall()

    except sqlite3.Error as error:
        print("Error getting users:", error)
        return []


# ============================================================
# DISPLAY ALL USERS
# ============================================================

def show_users():
    users = get_all_users()

    print()
    print("=" * 70)
    print("                    USER PROFILES")
    print("=" * 70)

    if not users:
        print("No users found.")
        return

    for user in users:
        print()
        print("User ID                  :", user["user_id"])
        print("Name                     :", user["name"])
        print("Phone                    :", user["phone"])
        print("Average Transaction      :", user["average_transaction"])
        print(
            "Normal Time              :",
            user["normal_start_time"],
            "to",
            user["normal_end_time"]
        )
        print(
            "Typical Daily Transactions:",
            user["typical_daily_transactions"]
        )
        print("Known Device             :", user["known_device"])
        print("Common Location          :", user["common_location"])
        print("-" * 70)


# ============================================================
# FIND USER BY NAME
# ============================================================

def find_user(name):
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    user_id,
                    name,
                    phone,
                    average_transaction,
                    normal_start_time,
                    normal_end_time,
                    typical_daily_transactions,
                    known_device,
                    common_location
                FROM users
                WHERE name LIKE ?
            """, (f"%{name}%",))

            return cursor.fetchall()

    except sqlite3.Error as error:
        print("Error searching user:", error)
        return []


# ============================================================
# DISPLAY SPECIFIC USER
# ============================================================

def show_user(name):
    users = find_user(name)

    print()
    print("=" * 70)
    print("                     USER SEARCH")
    print("=" * 70)

    if not users:
        print()
        print("No user found:", name)
        print()
        return

    for user in users:
        print()
        print("User ID             :", user["user_id"])
        print("Name                :", user["name"])
        print("Phone               :", user["phone"])
        print("Average Amount      :", user["average_transaction"])
        print(
            "Normal Time         :",
            user["normal_start_time"],
            "to",
            user["normal_end_time"]
        )
        print(
            "Daily Transactions  :",
            user["typical_daily_transactions"]
        )
        print("Known Device        :", user["known_device"])
        print("Common Location     :", user["common_location"])

    print()


# ============================================================
# GET BENEFICIARIES
# ============================================================

def get_beneficiaries(user_id):
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    beneficiary_id,
                    beneficiary_name,
                    upi_id,
                    transaction_count,
                    average_amount,
                    last_transaction_time,
                    is_known
                FROM beneficiaries
                WHERE user_id = ?
                ORDER BY beneficiary_id
            """, (user_id,))

            return cursor.fetchall()

    except sqlite3.Error as error:
        print("Error getting beneficiaries:", error)
        return []


# ============================================================
# DISPLAY BENEFICIARIES
# ============================================================

def show_beneficiaries():
    users = get_all_users()

    print()
    print("=" * 70)
    print("                    BENEFICIARIES")
    print("=" * 70)

    if not users:
        print("No users found.")
        return

    for user in users:
        print()
        print("USER:", user["name"])
        print("-" * 70)

        beneficiaries = get_beneficiaries(user["user_id"])

        if not beneficiaries:
            print("No beneficiaries found.")
            continue

        for beneficiary in beneficiaries:
            print(
                "ID:", beneficiary["beneficiary_id"],
                "| Name:", beneficiary["beneficiary_name"],
                "| UPI:", beneficiary["upi_id"]
            )

            print(
                "Transactions:", beneficiary["transaction_count"],
                "| Average Amount:", beneficiary["average_amount"]
            )

            print(
                "Known:",
                "YES" if beneficiary["is_known"] else "NO"
            )

            print()


# ============================================================
# SHOW ALL TRANSACTIONS
# ============================================================

def show_transactions():
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    transaction_id,
                    user_name,
                    amount,
                    transaction_time,
                    device_id,
                    location,
                    risk_score,
                    risk_level,
                    action
                FROM risk_analysis
                ORDER BY risk_score DESC
            """)

            transactions = cursor.fetchall()

    except sqlite3.Error as error:
        print("Error getting transactions:", error)
        return

    print()
    print("=" * 95)
    print("                    TRANSACTION RISK ANALYSIS")
    print("=" * 95)
    print()

    if not transactions:
        print("No transactions found.")
        return

    for transaction in transactions:
        print(
            transaction["transaction_id"],
            "|",
            transaction["user_name"]
        )

        print(
            "Amount:", transaction["amount"],
            "| Risk Score:", transaction["risk_score"],
            "| Level:", transaction["risk_level"],
            "| Action:", transaction["action"]
        )

        print(
            "Time:", transaction["transaction_time"],
            "| Device:", transaction["device_id"]
        )

        print(
            "Location:", transaction["location"]
        )

        print("-" * 95)


# ============================================================
# GET RISK RESULT FOR A SPECIFIC USER
# ============================================================

def get_user_risk_results(user_name):
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    transaction_id,
                    user_name,
                    amount,
                    risk_score,
                    risk_level,
                    action
                FROM risk_analysis
                WHERE user_name LIKE ?
                ORDER BY risk_score DESC
            """, (f"%{user_name}%",))

            return cursor.fetchall()

    except sqlite3.Error as error:
        print("Error getting risk results:", error)
        return []


# ============================================================
# DISPLAY USER RISK
# ============================================================

def show_user_risk(user_name):
    results = get_user_risk_results(user_name)

    print()
    print("=" * 70)
    print("                 RISK RESULT")
    print("=" * 70)
    print()
    print("User:", user_name)
    print()

    if not results:
        print("No risk analysis found.")
        return

    for result in results:
        print(
            result["transaction_id"],
            "| Score:", result["risk_score"],
            "|", result["risk_level"],
            "|", result["action"]
        )

    print()


# ============================================================
# SHOW RISK FACTORS
# ============================================================

def show_risk_factors():
    try:
        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute("""
                SELECT
                    factor_id,
                    factor_name,
                    weight,
                    description
                FROM risk_factor_definitions
                ORDER BY factor_id
            """)

            factors = cursor.fetchall()

    except sqlite3.Error as error:
        print("Error getting risk factors:", error)
        return

    print()
    print("=" * 70)
    print("                 SECUREFLOW RISK FACTORS")
    print("=" * 70)
    print()

    if not factors:
        print("No risk factors found.")
        return

    for factor in factors:
        print(
            factor["factor_id"],
            ".",
            factor["factor_name"],
            "→",
            factor["weight"]
        )

        print("   ", factor["description"])

    print()
    print("Maximum Risk Score = 100")
    print()


# ============================================================
# COMPLETE USER PROFILE
# ============================================================

def show_complete_user_profile(user_name):
    users = find_user(user_name)

    if not users:
        print("User not found.")
        return

    for user in users:
        print()
        print("=" * 80)
        print("             COMPLETE SECUREFLOW USER PROFILE")
        print("=" * 80)

        print()
        print("USER INFORMATION")
        print("-" * 80)

        print("User ID              :", user["user_id"])
        print("Name                 :", user["name"])
        print("Phone                :", user["phone"])
        print("Average Transaction  :", user["average_transaction"])
        print(
            "Normal Time          :",
            user["normal_start_time"],
            "to",
            user["normal_end_time"]
        )
        print(
            "Daily Transactions   :",
            user["typical_daily_transactions"]
        )
        print("Known Device         :", user["known_device"])
        print("Common Location      :", user["common_location"])

        print()
        print("BENEFICIARIES")
        print("-" * 80)

        beneficiaries = get_beneficiaries(user["user_id"])

        if not beneficiaries:
            print("No beneficiaries found.")
        else:
            for beneficiary in beneficiaries:
                print(
                    beneficiary["beneficiary_id"],
                    "|",
                    beneficiary["beneficiary_name"],
                    "|",
                    beneficiary["upi_id"],
                    "| Known:",
                    "YES" if beneficiary["is_known"] else "NO"
                )

        print()
        print("RISK RESULTS")
        print("-" * 80)

        risk_results = get_user_risk_results(user["name"])

        if not risk_results:
            print("No risk results found.")
        else:
            for result in risk_results:
                print(
                    result["transaction_id"],
                    "| Amount:", result["amount"],
                    "| Score:", result["risk_score"],
                    "|", result["risk_level"],
                    "|", result["action"]
                )

        print()


# ============================================================
# PROGRAM MENU
# ============================================================

def menu():
    while True:
        print()
        print("=" * 60)
        print("              SECUREFLOW-AI DATABASE")
        print("=" * 60)
        print()
        print("1. Show all users")
        print("2. Search user")
        print("3. Show beneficiaries")
        print("4. Show all transactions")
        print("5. Show user risk")
        print("6. Show risk factors")
        print("7. Show complete user profile")
        print("8. Test database connection")
        print("9. Exit")
        print()

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            show_users()

        elif choice == "2":
            name = input("Enter user name: ").strip()
            show_user(name)

        elif choice == "3":
            show_beneficiaries()

        elif choice == "4":
            show_transactions()

        elif choice == "5":
            name = input("Enter user name: ").strip()
            show_user_risk(name)

        elif choice == "6":
            show_risk_factors()

        elif choice == "7":
            name = input("Enter user name: ").strip()
            show_complete_user_profile(name)

        elif choice == "8":
            test_connection()

        elif choice == "9":
            print()
            print("Closing SecureFlow-AI...")
            print()
            break

        else:
            print()
            print("Invalid choice. Please try again.")


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":
    print()
    print("Starting SecureFlow-AI Database Module...")

    test_connection()
    menu()