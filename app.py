from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from flask import make_response
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

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
    return render_template("index.html", title="Manhwa", manhwa_list=manhwa_list)


@app.route("/category/<string:category>")
def by_category(category):
    category = category.capitalize()
    response = supabase.table("Manhwa").select("*").execute()

    # Get the data from the response
    all_manhwas = response.data

    # Filter manhwas with the specified category
    filtered_manhwas = [
        manhwa for manhwa in all_manhwas if category in manhwa.get("categories", [])
    ]

    return render_template(
        "index.html",
        title=f"{category} Manhwas",
        manhwa_list=filtered_manhwas,
    )


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


@app.route("/sitemap.xml")
def sitemap():
    root = Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Add home page
    url = SubElement(root, "url")
    loc = SubElement(url, "loc")
    loc.text = request.url_root

    # Add category pages
    response = supabase.table("Manhwa").select("categories").execute()
    categories = set()
    for manhwa in response.data:
        categories.update(manhwa.get("categories", []))

    for category in categories:
        url = SubElement(root, "url")
        loc = SubElement(url, "loc")
        loc.text = f"{request.url_root}category/{category}"

    # Create the XML string
    xml_string = minidom.parseString(tostring(root)).toprettyxml(indent="  ")

    response = make_response(xml_string)
    response.headers["Content-Type"] = "application/xml"
    return response


if __name__ == "__main__":
    app.run(debug=True)
