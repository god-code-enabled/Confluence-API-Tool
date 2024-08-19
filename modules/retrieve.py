import requests
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Confluence credentials and instance setup
API_TOKEN = os.getenv('API_TOKEN')
BASE_URL = os.getenv('BASE_URL')
USERNAME = os.getenv('USERNAME')
SPACE_KEY = "Cognita"  # Replace with your space key

# Headers for the API requests
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_trashed_pages(space_key):
    url = f"{BASE_URL}/wiki/rest/api/content?spaceKey={space_key}&status=trashed&limit=200"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        print(f"Failed to retrieve trashed content. Status code: {response.status_code}")
        return []

# Step 2: Filter the Pages (excluding "Published")
def filter_pages(pages):
    return [page for page in pages if "Published" not in page['title']]

# Step 3: Restore the Pages
def restore_page(page_id):
    url = f"{BASE_URL}/wiki/pages/dorestoretrashitem.action"
    data = {"key": SPACE_KEY, "contentId": page_id}
    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        print(f"Successfully restored page with ID: {page_id}")
    else:
        print(f"Failed to restore page with ID: {page_id}. Status code: {response.status_code}")

if __name__ == "__main__":
    trashed_pages = get_trashed_pages(SPACE_KEY)

    if trashed_pages:
        # Filter out the pages with "Published" in their title
        pages_to_restore = filter_pages(trashed_pages)

        for page in pages_to_restore:
            page_id = page['id']
            print(f"Restoring page ID: {page_id}, Title: {page['title']}")
            restore_page(page_id)
    else:
        print("No trashed content found in the specified space.")
