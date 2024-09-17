import os
from supabase import create_client, Client
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List
from openai import OpenAI

# Load environment variables
load_dotenv()

# Load environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

client = OpenAI()


class ManhwaList(BaseModel):
    title: str = Field(description="The title of the manhwa list")
    description: str = Field(description="A brief description of the manhwa list")
    manhwas: List[str] = Field(description="A list of manhwa titles in the list")


def create_manhwa_list(manhwa_names, list_title, list_description):
    """
    Create a new list, link it with specified manhwa, and return the new list ID.

    Args:
    manhwa_names (list): Names of manhwa to include in the list.
    list_title (str): Title of the new list.
    list_description (str): Description of the new list.

    Returns:
    int: ID of the newly created list.
    """
    # Get manhwa details and create new list
    manhwa_data = (
        supabase.table("Manhwa")
        .select("id, title")
        .in_("title", manhwa_names)
        .execute()
        .data
    )
    list_response = (
        supabase.table("List")
        .insert(
            {
                "name": list_title,
                "description": list_description,
                "slug": list_title.lower().replace(" ", "-"),
            }
        )
        .execute()
    )
    list_id = list_response.data[0]["id"]

    # Link manhwa to the new list
    for manhwa in manhwa_data:
        supabase.table("ListManhwa").insert(
            {"list": list_id, "manhwa": manhwa["id"]}
        ).execute()

    return list_id


def get_manhwa_details_by_list_slug(list_slug):
    """
    Retrieve all Manhwa details associated with a given List slug using joins.

    Parameters:
    list_slug (str): The slug of the List to query.

    Returns:
    list: A list of dictionaries containing Manhwa details.
    """
    response = (
        supabase.table("List")
        .select("Manhwa:ListManhwa(Manhwa(*))")
        .eq("slug", list_slug)
        .execute()
    )

    if not response.data:
        return []  # Return an empty list if no matching list is found

    # Extract Manhwa details from the nested structure
    manhwa_list = response.data[0].get("Manhwa", [])
    return [item["Manhwa"] for item in manhwa_list if item["Manhwa"]]


def get_manhwa_list_data_from_text(text):

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract the event information."},
            {
                "role": "user",
                "content": text,
            },
        ],
        response_format=ManhwaList,
    )

    manhwa_data = completion.choices[0].message.parsed
    return manhwa_data


def create_manhwa_list_data_from_text(text):
    # Get the manhwa list data from the text
    manhwa_list_data = get_manhwa_list_data_from_text(text)

    # Create a new list in the database
    list_id = create_manhwa_list(
        manhwa_list_data.manhwas, manhwa_list_data.title, manhwa_list_data.description
    )
    return list_id
