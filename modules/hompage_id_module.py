import pandas as pd
from atlassian import Confluence
from dotenv import load_dotenv, set_key
import os

# Load existing .env variables
load_dotenv()

def initialize_confluence():
    """Initialize and return a Confluence object."""
    API_TOKEN = os.getenv('API_TOKEN')
    BASE_URL = os.getenv('BASE_URL')
    USERNAME = os.getenv('USERNAME')

    # Check if the environment variables are set
    if not USERNAME or not API_TOKEN or not BASE_URL:
        raise ValueError("Missing required environment variables. Please ensure USERNAME, API_TOKEN, and BASE_URL are set in the .env file.")

    # Initialize and return the Confluence object
    return Confluence(
        url=BASE_URL,
        username=USERNAME,
        password=API_TOKEN
    )

def read_csv(file_path):
    return pd.read_csv(file_path, dtype=str)  # Read as strings to prevent .0 issue

def write_csv(file_path, dataframe):
    dataframe.dropna(how='all', inplace=True)  # Remove rows where all values are None
    dataframe.fillna('', inplace=True)  # Replace NaN with empty strings
    dataframe.to_csv(file_path, index=False)

def update_env_file(env_file, key, value):
    set_key(env_file, key, value)

def get_page_title(page_id):
    """Fetch the title of a page given its ID."""
    confluence = initialize_confluence()
    try:
        page = confluence.get_page_by_id(page_id, expand='title')
        return page['title']
    except Exception as e:
        return f"Error fetching title for page ID {page_id}: {e}"

def get_child_page_ids_and_titles(homepage_id):
    confluence = initialize_confluence()
    try:
        child_pages = confluence.get_child_pages(homepage_id)
        return [(child['id'], child['title']) for child in child_pages] if child_pages else []
    except Exception as e:
        return f"An error occurred while fetching child pages for homepage {homepage_id}: {e}"

def append_to_csv(file_path, from_id, to_id, prefix):
    df = read_csv(file_path)
    new_row = pd.DataFrame([[from_id, to_id, prefix]], columns=["from", "to", "prefix"])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    write_csv(file_path, updated_df)

def read_homepages(file_path):
    """Read homepage IDs from a file into a list."""
    if os.path.exists(file_path):
        try:
            data = pd.read_csv(file_path, dtype=str, header=None)
            if data.empty:
                return []  # Return an empty list if the file is empty
            
            # If data contains only one column, convert it to a list
            if len(data.columns) == 1:
                return data[0].tolist()
            else:
                raise ValueError("Homepage file should only have one column.")
        except pd.errors.EmptyDataError:
            return []  # Handle the case where the CSV is empty
        except Exception as e:
            return [f"An error occurred: {e}"]
    else:
        return []

def write_homepages(file_path, homepages):
    """Write a list of homepage IDs to a file, ensuring uniqueness."""
    unique_homepages = pd.Series(homepages).drop_duplicates().dropna().tolist()
    pd.Series(unique_homepages).to_csv(file_path, index=False, header=False)

def add_homepage(file_path, homepage_id):
    """Add a homepage ID to the list, ensuring no duplicates."""
    homepages = read_homepages(file_path)
    if homepage_id not in homepages:
        homepages.append(homepage_id)
        write_homepages(file_path, homepages)
        return f"Homepage ID {homepage_id} added."
    else:
        return f"Homepage ID {homepage_id} is already in the list."

def remove_homepage(file_path, homepage_id):
    """Remove a homepage ID from the list."""
    homepages = read_homepages(file_path)
    if homepage_id in homepages:
        homepages.remove(homepage_id)
        write_homepages(file_path, homepages)
        return f"Homepage ID {homepage_id} removed."
    else:
        return f"Homepage ID {homepage_id} not found in the list."
