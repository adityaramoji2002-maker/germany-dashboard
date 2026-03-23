from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "database.db"


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


init_db()


# -----------------------------
# LOAD DATA
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

                if "status" in key.lower():
                    if str(value).lower() in ["done", "yes", "completed"]:
                        completed_tasks += 1

                    if value:
                        university_status[value] = university_status.get(value, 0) + 1

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

    cursor.execute("""
        INSERT INTO dashboard (sheet, column_name, value, row_index)
        VALUES (?, ?, ?, ?)
    """, (sheet, column, value, row))

    conn.commit()
    conn.close()

    return jsonify({"status": "saved"})


# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
