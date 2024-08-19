import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from modules.log_utils import log_function_call, logger
from dotenv import load_dotenv
from modules.delete_module import delete_pages_from_csv
from modules.copy_module import copy_page  # Assuming you have a function named `copy_page` in `copy_module.py`
import os

# Load environment variables from the .env file
load_dotenv()

@log_function_call
def read_csv_to_dict(file_path):
    with open(file_path, mode='r') as file:
        return list(csv.DictReader(file))

@log_function_call
def deduplicate_operations(operations):
    seen = set()
    deduplicated_list = []
    for operation in operations:
        # Create a tuple of identifying properties for checking duplicates
        operation_tuple = (operation["from"], operation["to"])
        if operation_tuple not in seen:
            seen.add(operation_tuple)
            deduplicated_list.append(operation)
    return deduplicated_list

@log_function_call
def run_copy_process(source_page_id, destination_page_id, prefix_title):
    try:
        result = copy_page(source_page_id, destination_page_id, prefix_title)
        logger.info(f"Copy from {source_page_id} to {destination_page_id} with prefix '{prefix_title}' succeeded.")
        return 0, result, []
    except Exception as e:
        logger.error(f"Error copying from {source_page_id} to {destination_page_id} with prefix '{prefix_title}': {e}")
        return 1, [], [str(e)]

def run_copy_operations():
    file_path = "data/copy_operations.csv"
    homepages_csv_file = "data/homepages.csv"
    
    # Step 1: Perform the deletion based on the CSV before copying the pages
    delete_pages_from_csv(file_path, homepages_csv_file)

    copy_operations_list = read_csv_to_dict(file_path)

    # Deduplicate operations to avoid attempting to copy the same page twice
    deduplicated_operations_list = deduplicate_operations(copy_operations_list)

    with ThreadPoolExecutor(max_workers=2) as executor:  # Adjust `max_workers` as needed
        futures = []

        for operation in deduplicated_operations_list:
            # Delay to manage Confluence rate-limiting, and avoid hitting API too rapidly
            sleep(1)
            futures.append(executor.submit(run_copy_process, operation["from"], operation["to"], operation["prefix"]))

        for future in as_completed(futures):
            returncode, stdout, stderr = future.result()

            if returncode == 0:
                logger.info(f"Process Completed Successfully. Output: {stdout}")
            else:
                logger.error(f"Process failed with returncode {returncode}. Error: {stderr}")

    logger.info("Finished executing all copy operations from the CSV.")

if __name__ == "__main__":
    run_copy_operations()
