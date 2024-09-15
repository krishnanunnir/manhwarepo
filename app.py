from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Supabase configuration
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


@app.route("/")
def index():
    # Fetch Manhwa list from Supabase
    response = supabase.table("Manhwa").select("*").execute()
    manhwa_list = response.data

    # Render the template with the fetched data
    return render_template("index.html", manhwa_list=manhwa_list)


@app.route("/api/search", methods=["GET"])
def search_manhwa():
    title = request.args.get("title", "")
    if not title:
        return jsonify({"error": "Title parameter is required"}), 400

    response = (
        supabase.table("Manhwa").select("*").ilike("title", f"%{title}%").execute()
    )
    results = response.data

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
