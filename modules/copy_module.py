import requests
import json
import sys
from time import sleep
from dotenv import load_dotenv
import os
from modules.log_utils import logger  # Adjusted import path

# Load environment variables from .env file
load_dotenv()

USERNAME = os.getenv('USERNAME')
API_TOKEN = os.getenv('API_TOKEN')
BASE_URL = os.getenv('BASE_URL')
api_base_url = f"{BASE_URL}/wiki/rest/api/content"

def check_task_status(task_url, headers, auth):
    for _ in range(3):
        response = requests.get(task_url, headers=headers, auth=auth, timeout=30)
        if response.status_code == 200:
            try:
                json_response = response.json()
                if json_response.get("state") == "SUCCESS":
                    return True
                elif json_response.get("state") == "FAILED":
                    logger.error("Task failed with state 'FAILED'.")
                    return False
            except (requests.exceptions.JSONDecodeError, ValueError):
                logger.error("Failed to decode JSON response while checking task status.")
        else:
            logger.error(f"Task status check failed with status code: {response.status_code}")
        sleep(5)
    return False

def copy_page(source_page_id, destination_page_id, prefix_title, retries=3):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_TOKEN}"
    }

    payload = {
        "copyAttachments": True,
        "copyDescendants": True,
        "copyPermissions": True,
        "copyLabels": True,
        "destinationPageId": destination_page_id,
        "titleOptions": {"prefix": prefix_title}
    }

    for attempt in range(retries):
        logger.debug(f"Attempt {attempt + 1} to copy page {source_page_id} to {destination_page_id} with prefix '{prefix_title}'")
        response = requests.post(f"{api_base_url}/{source_page_id}/pagehierarchy/copy",
                                 headers=headers, auth=(USERNAME, API_TOKEN),
                                 data=json.dumps(payload), timeout=60)

        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response content: {response.text}")

        if response.status_code in [200, 202]:
            if response.status_code == 202:
                try:
                    task_url = f"{BASE_URL}{response.json()['links']['status']}"
                    if check_task_status(task_url, headers, (USERNAME, API_TOKEN)):
                        logger.info(f"Successfully copied page {source_page_id} to {destination_page_id} with prefix '{prefix_title}'")
                        return 0
                except (requests.exceptions.JSONDecodeError, ValueError):
                    logger.error("JSON decode error during task status check.")
            else:
                logger.info(f"Successfully copied page {source_page_id} to {destination_page_id} with prefix '{prefix_title}'")
                return 0
        else:
            # Check if the error is related to conflicting titles
            if response.status_code == 400:
                error_message = response.json().get("message", "")
                if "conflicting titles" in error_message:
                    logger.info(f"Skipping conflicting title error: {error_message}")
                    return 0  # Treat this as a success for known non-critical issues
                else:
                    logger.error(f"Attempt {attempt + 1} failed with status code: {response.status_code}, response: {response.text}")
            else:
                logger.error(f"Attempt {attempt + 1} failed with status code: {response.status_code}, response: {response.text}")
            sleep(5)  # Delay before retrying

    logger.error(f"Failed to copy page {source_page_id} after {retries} attempts.")
    return 1

if __name__ == "__main__":
    if len(sys.argv) == 4:
        source_page_id, destination_page_id, prefix_title = sys.argv[1:]
        result = copy_page(source_page_id, destination_page_id, prefix_title)
        sys.exit(result)
    else:
        logger.error("Invalid arguments provided.")
        sys.exit(1)
