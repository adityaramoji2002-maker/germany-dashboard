from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd
import os

app = Flask(__name__)

DB_PATH = "database.db"
EXCEL_FILE = "Germany Plan 2026.xlsx"


# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dashboard (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sheet TEXT,
        column_name TEXT,
        value TEXT,
        row_index INTEGER
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# IMPORT EXCEL → DB (ONE TIME)
# -----------------------------
def import_excel_to_db():
    if not os.path.exists(EXCEL_FILE):
        print("Excel file not found, skipping import")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    xl = pd.ExcelFile(EXCEL_FILE)

    for sheet in xl.sheet_names:
        df = xl.parse(sheet).fillna("")

        for i, row in df.iterrows():
            for col in df.columns:
                cursor.execute("""
                    INSERT INTO dashboard (sheet, column_name, value, row_index)
                    VALUES (?, ?, ?, ?)
                """, (sheet, col, str(row[col]), i))

    conn.commit()
    conn.close()
    print("Excel data imported successfully!")


# -----------------------------
# LOAD DATA FROM DB
# -----------------------------
def load_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT sheet, column_name, value, row_index FROM dashboard")
    rows = cursor.fetchall()

    data = {}

    for sheet, column, value, row in rows:
        if sheet not in data:
            data[sheet] = []

        while len(data[sheet]) <= row:
            data[sheet].append({})

        data[sheet][row][column] = value

    conn.close()
    return data


# -----------------------------
# HOME ROUTE
# -----------------------------
@app.route("/")
def index():
    data = load_data()
    sheets = list(data.keys())

    total_tasks = sum(len(rows) for rows in data.values())
    completed_tasks = 0
    total_expense = 0
    university_status = {}

    for sheet in data:
        for row in data[sheet]:
            for key, value in row.items():

                # Completed tasks
                if "status" in key.lower():
                    if str(value).lower() in ["done", "yes", "completed"]:
                        completed_tasks += 1

                    if value:
                        university_status[value] = university_status.get(value, 0) + 1

                # Expense
                if "amount" in key.lower():
                    try:
                        total_expense += float(value)
                    except:
                        pass

    return render_template(
        "index.html",
        sheets=sheets,
        data=data,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_expense=total_expense,
        university_status=university_status
    )


# -----------------------------
# UPDATE DATA
# -----------------------------
@app.route("/update", methods=["POST"])
def update():
    sheet = request.json.get("sheet")
    row = request.json.get("row")
    column = request.json.get("column")
    value = request.json.get("value")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Remove old value
    cursor.execute("""
        DELETE FROM dashboard
        WHERE sheet=? AND row_index=? AND column_name=?
    """, (sheet, row, column))

    # Insert new value
    cursor.execute("""
        INSERT INTO dashboard (sheet, column_name, value, row_index)
        VALUES (?, ?, ?, ?)
    """, (sheet, column, value, row))

    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})


# -----------------------------
# INITIALIZE
# -----------------------------
init_db()

# Import only if DB empty
init_db()

def is_db_empty():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM dashboard")
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0

# Import ONLY if no data
if is_db_empty():
    print("Database empty → importing Excel...")
    import_excel_to_db()


# -----------------------------
# RUN (Render Compatible)
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
