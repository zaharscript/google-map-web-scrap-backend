# app.py
import os
import csv
import pandas as pd
import requests
import re  # Import regex module
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_restful import Api, Resource

# Initialize app
app = Flask(__name__)
CORS(app)
api = Api(app)

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

def remove_arabic(text):
    # Remove Arabic characters using regex
    return re.sub(r'[\u0600-\u06FF]', '', text)

# ---------- Class: Search Places ----------
class SearchAPI(Resource):
    def post(self):
        data = request.get_json()
        query = data.get("query")

        if not query:
            return {"error": "Missing 'query' in request body"}, 400

        # Call Nominatim API
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": query,
            "format": "json",
            "limit": 20
        }
        headers = {
            "User-Agent": "my-flask-app"
        }

        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            return {"error": "Failed to fetch from Nominatim API"}, 500

        results = []
        for place in response.json():
            display_name = place.get("display_name", "")
            name, *address_parts = display_name.split(", ")
            address = ", ".join(address_parts)

            # Clean Arabic characters from name and address
            name = remove_arabic(name)
            address = remove_arabic(address)

            results.append({
                "name": name.strip(),
                "address": address.strip(),
                "lat": place.get("lat"),
                "lon": place.get("lon"),
                "type": place.get("type")
            })

        # Save to CSV
        csv_file = os.path.join(EXPORT_DIR, "places.csv")
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "address", "lat", "lon", "type"])
            writer.writeheader()
            writer.writerows(results)

        # Save to Excel
        excel_file = os.path.join(EXPORT_DIR, "places.xlsx")
        df = pd.DataFrame(results)
        df.to_excel(excel_file, index=False)

        return results, 200

# ---------- Class: Download CSV/Excel ----------
class DownloadAPI(Resource):
    def get(self, filetype):
        if filetype not in ["csv", "excel"]:
            return {"error": "Invalid file type"}, 400

        filename = f"places.{ 'csv' if filetype == 'csv' else 'xlsx' }"
        return send_from_directory(EXPORT_DIR, filename, as_attachment=True)

# ---------- Register Routes ----------
api.add_resource(SearchAPI, "/search")
api.add_resource(DownloadAPI, "/download/<string:filetype>")

# ---------- Run Server ----------
if __name__ == "__main__":
    app.run(debug=True)
