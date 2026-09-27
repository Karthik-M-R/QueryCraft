
import sqlite3
from pathlib import Path
import sqlparse

DB_PATH = Path(__file__).parent / "data" / "company.db"


def create_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        conn.executescript("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                salary INTEGER NOT NULL,
                department_id INTEGER NOT NULL,
                FOREIGN KEY (department_id)
                    REFERENCES departments(id)
            );

            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                budget INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                FOREIGN KEY (employee_id)
                    REFERENCES employees(id)
            );
        """)

        if conn.execute(
            "SELECT COUNT(*) FROM departments"
        ).fetchone()[0] == 0:

            conn.executemany(
                "INSERT INTO departments VALUES (?, ?, ?)",
                [
                    (1, "Engineering", "Bangalore"),
                    (2, "Marketing", "Mumbai"),
                    (3, "Finance", "Delhi")
                ]
            )

            conn.executemany(
                "INSERT INTO employees VALUES (?, ?, ?, ?)",
                [
                    (1, "Rahul", 95000, 1),
                    (2, "Priya", 85000, 1),
                    (3, "Karthik", 75000, 1),
                    (4, "Ananya", 65000, 2),
                    (5, "Rohit", 60000, 2),
                    (6, "Sneha", 80000, 3)
                ]
            )

            conn.executemany(
                "INSERT INTO projects VALUES (?, ?, ?, ?)",
                [
                    (1, "AI Assistant", 200000, 1),
                    (2, "Web Platform", 150000, 2),
                    (3, "Mobile App", 120000, 3),
                    (4, "Ad Campaign", 90000, 4),
                    (5, "SEO Project", 50000, 5),
                    (6, "Finance Dashboard", 110000, 6)
                ]
            )

    print("Database initialized successfully!")






def validate_sql(sql):
    """
    Allow only one SELECT statement.
    Reject other SQL commands.
    """
    statements = sqlparse.parse(sql)
    #This parses the SQL and lets us check whether Gemini generated a single SELECT statement. It rejects ordinary DELETE, UPDATE
    #  and multi-statement queries. The parser alone is not a complete security control.

    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    statement = statements[0]

    if statement.get_type() != "SELECT":
        raise ValueError("Only SELECT queries are allowed.")

    return sql.strip()


def execute_query(sql):
    """
    Validate and execute generated SQL
    using a read-only SQLite connection.
    """
    sql = validate_sql(sql)

    # Open the existing database in read-only mode.
    db_uri = DB_PATH.resolve().as_uri() + "?mode=ro"

    with sqlite3.connect(
        db_uri,
        uri=True,
        timeout=5
    ) as conn:

        conn.execute("PRAGMA query_only = ON")

        # Prevent SQL from changing the database.
        def authorize(action, arg1, arg2, db, source):
            allowed = {
                sqlite3.SQLITE_SELECT,
                sqlite3.SQLITE_READ,
                sqlite3.SQLITE_FUNCTION,
            }

            if action == sqlite3.SQLITE_FUNCTION:
                if str(arg2).lower() == "load_extension":
                    return sqlite3.SQLITE_DENY

            if action in allowed:
                return sqlite3.SQLITE_OK

            return sqlite3.SQLITE_DENY

        conn.set_authorizer(authorize)

        # Interrupt queries that take too many VM steps.
        steps = 0

        def progress():
            nonlocal steps
            steps += 1
            return 1 if steps > 1000 else 0

        conn.set_progress_handler(progress, 1000)

        cursor = conn.execute(sql)

        columns = [
            description[0]
            for description in cursor.description
        ]

        # Limit the amount of data returned.
        rows = cursor.fetchmany(101)

        if len(rows) > 100:
            raise ValueError(
                "Query returned more than 100 rows."
            )

        return columns, rows

if __name__ == "__main__":
    create_database()