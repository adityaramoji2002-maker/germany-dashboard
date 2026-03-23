
from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

FILE_PATH = "Germany Plan 2026.xlsx"

def load_data():
    xl = pd.ExcelFile(FILE_PATH)
    return {sheet: xl.parse(sheet).fillna("").to_dict(orient="records") for sheet in xl.sheet_names}

@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", data=data, sheets=list(data.keys()))

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
