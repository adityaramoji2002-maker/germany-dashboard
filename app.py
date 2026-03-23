from flask import Flask, render_template, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

FILE_PATH = "Germany Plan 2026.xlsx"


# Load Excel Data
def load_data():
    xl = pd.ExcelFile(FILE_PATH)
    return {
        sheet: xl.parse(sheet).fillna("").to_dict(orient="records")
        for sheet in xl.sheet_names
    }


@app.route("/")
def index():
    xl = pd.ExcelFile(FILE_PATH)
    sheets = xl.sheet_names
    data = {}

    total_tasks = 0
    completed_tasks = 0
    total_expense = 0
    university_status = {}

    for sheet in sheets:
        df = xl.parse(sheet).fillna("")

        # Store data
        records = df.to_dict(orient="records") if not df.empty else []
        data[sheet] = records

        # Count total rows
        total_tasks += len(df)

        # Loop through columns safely
        for col in df.columns:

            # Completed tasks logic
            if "status" in col.lower():
                completed_tasks += len(
                    df[df[col].astype(str).str.lower().isin(["done", "yes", "completed"])]
                )

                # University status chart
                for val in df[col]:
                    if val:
                        university_status[val] = university_status.get(val, 0) + 1

            # Expense calculation
            if "amount" in col.lower():
                total_expense += pd.to_numeric(df[col], errors="coerce").sum()

    return render_template(
        "index.html",
        sheets=sheets,
        data=data,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        total_expense=total_expense,
        university_status=university_status
    )


@app.route("/update", methods=["POST"])
def update():
    sheet = request.json.get("sheet")
    row_index = request.json.get("row")
    column = request.json.get("column")
    value = request.json.get("value")

    df = pd.read_excel(FILE_PATH, sheet_name=sheet)

    df.at[row_index, column] = value

    with pd.ExcelWriter(FILE_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df.to_excel(writer, sheet_name=sheet, index=False)

    return jsonify({"status": "success"})


# Run app (Render compatible)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
