# Confluence Page Copier Tool

## Summary

This Confluence Page Copier Tool is designed to facilitate the copying and managing of Confluence pages between different parent pages. The tool provides both a Streamlit-based graphical interface (`app.py`) for easy interaction and command-line options for more advanced users. The code base leverages the Confluence REST API and provides additional functionalities like managing environment variables, reading and writing CSV files, and handling Confluence page tree operations.

## How to Use

### Prerequisites

- Python 3.x
- Confluence account with required permissions
- API Token for the Confluence account
- Installation of required packages (defined in `requirements.txt`)

### Setup
1. **Clone the Repository:**
   ```sh
   git clone http://gitlab.lab2demo.com/cogni-test/confluence-api-tools.git
   cd gitlab-api-tools
   ```

2. **Create a Virtual Environment:**
   - **On Windows:**
     ```sh
     python -m venv .venv
     .\.venv\Scripts\activate
     ```
   - **On Linux:**
     ```sh
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install the Necessary Dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Create a `.env` File to manually add credentials or proceed to the next section to add them through the frontend:**
   - In the root directory of the project, create a `.env` file with the following environment variables:
     ```sh
     USERNAME=your_confluence_username
     API_TOKEN=your_confluence_api_token
     BASE_URL=your_confluence_base_url
     ```

### Using the Frontend Interface

Start the Streamlit application:
```sh
streamlit run app.py
```

#### Features:

- **Set Environment Variables**: Update and save the `.env` file directly from the sidebar.
- **Edit Operations**: View and edit the copy operations from a CSV file.
- **Manage Homepage IDs**: Add or remove homepage IDs, which serve as parent pages for the copied content.

### Using the Command-Line Interface

1. **Update `copy_operations.csv`**: Any page copy operations should be defined here. It should contain the following columns:
    ```
    from,to,prefix
    <from_page_id>,<destination_parent_id>,<prefix>
    ```
    - **from**: Source page ID
    - **to**: Destination parent page ID
    - **prefix**: Optional prefix for the copied page title, if left empty, the source page name will retain the same name.

2. **Run the copy operations**: Use the following command:
    ```sh
    python main.py
    ```

## Project Python Modules and Files 

```sh
.
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── .env
├── data/
│   ├── copy_operations.csv
│   ├── homepages.csv
├── logs/
│   ├── app.log
├── modules/
│   ├── __init__.py
│   ├── copy_module.py
│   ├── delete_module.py
│   ├── homepages_id_module.py
│   ├── log_utils.py
│   ├── retrieve.py
```

### `app.py`

This is the primary Streamlit application that provides a graphical user interface for setting up and managing Confluence page copy operations. It allows users to set environment variables, manage homepage IDs, and run copy operations interactively.

### `copy_module.py`

Handles the core logic for copying Confluence pages. It interacts with the Confluence API to copy pages, manage attachments, descendants, permissions, and labels. It also includes error handling and retry mechanisms.

### `delete_module.py`

Provides functionality to delete pages from Confluence. It reads a list of homepage IDs from a CSV file and deletes all child pages under these homepages, using a thread pool for concurrent deletion.

### `hompage_id_module.py`

Manages homepage IDs by reading and writing to a CSV file. It interacts with the Confluence API to fetch page titles and child pages. It includes functions for reading and writing CSV files, updating environment variables, and managing homepage IDs. 

### `log_utils.py`

Configures logging for the application. It includes a custom log filter to suppress non-critical errors and a decorator for logging function calls. This module ensures that detailed logs are maintained, aiding in debugging and monitoring.

### `main.py`

Orchestrates the entire copy operation. It initializes the various modules and manages concurrency for running the copy operations. It reads from `copy_operations.csv`, deduplicates operations, and handles errors and retries using a thread pool.

### `copy_operations.csv`

A sample CSV file where you define the page copy operations. Each row includes a source page ID, a destination parent page ID, and an optional title prefix.

### `homepages.csv`

Consists of two columns: the first column contains the homeage IDs and a second column called 'protected' if set to true, or empty it will be protected from deletion, else if  false, It is will be protected from deletion. 
