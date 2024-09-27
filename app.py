import os
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, render_template, request
from supabase import Client, create_client
from utils import (
    create_manhwa_list,
    get_manhwa_details_by_list_slug,
    create_manhwa_list_data_from_text,
)

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
    return render_template(
        "index.html",
        title="Manhwa",
        description="List of all Manhwas",
        manhwa_list=manhwa_list,
    )


@app.route("/category/<string:category>")
def by_category(category):

    category = " ".join(
        word.capitalize() for word in category.replace("_", " ").split()
    )
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
        description=f"List of all {category} Manhwas",
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
        no_space_category = category.replace(" ", "_").lower()
        loc.text = f"{request.url_root}category/{no_space_category}"

    # Create the XML string
    xml_string = minidom.parseString(tostring(root)).toprettyxml(indent="  ")

    response = make_response(xml_string)
    response.headers["Content-Type"] = "application/xml"
    return response


@app.route("/create-list", methods=["POST"])
def create_list():
    data = request.json
    manhwa_names = data.get("manhwa_names", [])
    list_title = data.get("list_title", "")
    list_description = data.get("list_description", "")

    if not manhwa_names or not list_title:
        return jsonify({"error": "Manhwa names and list title are required"}), 400

    try:
        list_id = create_manhwa_list(manhwa_names, list_title, list_description)
        return jsonify({"success": True, "list_id": list_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/create-list-from-text", methods=["POST"])
def create_list_from_text():
    text = request.json.get("text")
    if not text:
        return jsonify({"error": "Text is required in the request body"}), 400

    try:
        list_id = create_manhwa_list_data_from_text(text)
        return jsonify({"success": True, "list_id": list_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/list/<string:list_slug>")
def render_by_list_slug(list_slug):
    manhwa_list = get_manhwa_details_by_list_slug(list_slug)

    if not manhwa_list:
        return render_template("404.html"), 404

    return render_template(
        "index.html",
        title=f"Manhwa List: {list_slug}",
        manhwa_list=manhwa_list,
    )


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
