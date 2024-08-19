import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from atlassian import Confluence
import os
from time import sleep

# Load environment variables
load_dotenv()

def initialize_confluence():
    USERNAME = os.getenv('USERNAME')
    API_TOKEN = os.getenv('API_TOKEN')
    BASE_URL = os.getenv('BASE_URL')

    # Check if the environment variables are set
    if not USERNAME or not API_TOKEN or not BASE_URL:
        raise ValueError("Missing required environment variables. Please ensure USERNAME, API_TOKEN, and BASE_URL are set in the .env file.")

    # Setup Confluence client
    return Confluence(
        url=BASE_URL,
        username=USERNAME,
        password=API_TOKEN
    )

def fetch_unique_homepage_ids(csv_file):
    """Fetch and deduplicate homepage IDs from the 'to' column in the CSV."""
    unique_homepage_ids = set()
    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            homepage_id = row['to']
            unique_homepage_ids.add(homepage_id)
    return list(unique_homepage_ids)

def get_protected_homepage_ids(hompages_csv_file):
    """Fetch homepage IDs marked as protected from the homepages.csv."""
    protected_homepage_ids = set()
    with open(hompages_csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row.get('protected', '').lower() == 'true':
                protected_homepage_ids.add(row['homepage_id'])
    return protected_homepage_ids

def get_child_page_ids(confluence, homepage_id):
    """Fetch child page IDs from a given homepage ID."""
    try:
        child_pages = confluence.get_child_pages(homepage_id)
        child_ids = [child['id'] for child in child_pages]
        return child_ids
    except Exception as e:
        print(f"An error occurred while fetching child pages for homepage ID {homepage_id}: {e}")
        return []

def delete_page(confluence, page_id):
    """Deletes the page and its children given a page ID."""
    try:
        confluence.remove_page(page_id, recursive=True)
        print(f"Page ID {page_id} deleted successfully.")
    except Exception as e:
        print(f"An error occurred while deleting page ID {page_id}: {e}")

def delete_pages_from_csv(file_path, hompages_csv_file, max_workers=4):
    """Processes the CSV content, retrieves all descendant IDs, and deletes them if not protected."""
    confluence = initialize_confluence()

    homepage_ids = fetch_unique_homepage_ids(file_path)
    protected_homepage_ids = get_protected_homepage_ids(hompages_csv_file)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []

        for homepage_id in homepage_ids:
            if homepage_id in protected_homepage_ids:
                print(f"Skipping deletion for protected homepage ID {homepage_id}.")
                continue
            
            print(f"\nProcessing deletion for homepage ID {homepage_id}...")

            # Fetch all descendant pages IDs under the homepage
            all_page_ids = get_child_page_ids(confluence, homepage_id)
            if not all_page_ids:
                print(f"No pages found under homepage {homepage_id} to delete.")
                continue

            # Schedule deletion for each page ID
            for page_id in all_page_ids:
                futures.append(executor.submit(delete_page, confluence, page_id))
                sleep(1)  # Rate limiting

            # Process future results
            for future in as_completed(futures):
                future.result()

        # Verify if all pages have been deleted
        for homepage_id in homepage_ids:
            if homepage_id in protected_homepage_ids:
                continue
            remaining_pages = get_child_page_ids(confluence, homepage_id)
            if remaining_pages:
                print(f"Warning: Pages under homepage ID {homepage_id} were not fully deleted.")
            else:
                print(f"All pages under homepage ID {homepage_id} successfully deleted.")

# Example usage:
# Uncomment the line below to run this script directly
# delete_pages_from_csv('data/copy_operations.csv', 'data/homepages.csv')
