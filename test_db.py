from database import execute_query

sql = """
SELECT *
FROM projects
WHERE budget = (
    SELECT MAX(budget)
    FROM projects
);
"""

columns, rows = execute_query(sql)

print("Columns:", columns)
print("Rows:", rows)