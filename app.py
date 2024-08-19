import streamlit as st
from main import run_copy_operations
import pandas as pd
from modules.hompage_id_module import (
    read_csv, write_csv, update_env_file, get_child_page_ids_and_titles, append_to_csv,
    read_homepages, write_homepages, add_homepage, remove_homepage, get_page_title
)
import os
from dotenv import load_dotenv

# Define the path to your CSV files and .env file
CSV_FILE_PATH = "data/copy_operations.csv"
HOMEPAGES_FILE_PATH = "data/homepages.csv"
ENV_FILE_PATH = ".env"

# Initialize variables
username, api_token, base_url = None, None, None

# Streamlit app layout
st.title("Confluence Page Copy Tool")

# Check if the .env file exists
if os.path.exists(ENV_FILE_PATH):
    # Load the environment variables
    load_dotenv(ENV_FILE_PATH)
    username = os.getenv("USERNAME")
    api_token = os.getenv("API_TOKEN")
    base_url = os.getenv("BASE_URL")
    
    if not username or not api_token or not base_url:
        st.warning("Some environment variables are not set. Please enter your credentials to continue.")
else:
    st.warning("The .env file does not exist. Please enter your credentials to continue.")

# Side panel for setting .env variables
with st.sidebar:
    st.header("Set Environment Variables")
    
    # If environment variables were not loaded, default to empty strings
    username = st.text_input("USERNAME", username if username else "")
    api_token = st.text_input("API_TOKEN", api_token if api_token else "", type="password")
    base_url = st.text_input("BASE_URL", base_url if base_url else "")

    # Save .env variables button
    if st.button("Save .env"):
        update_env_file(ENV_FILE_PATH, "USERNAME", username)
        update_env_file(ENV_FILE_PATH, "API_TOKEN", api_token)
        update_env_file(ENV_FILE_PATH, "BASE_URL", base_url)
        
        # Reload the environment variables after saving
        load_dotenv(ENV_FILE_PATH)
        
        # Update local variables after reloading .env
        username = os.getenv("USERNAME")
        api_token = os.getenv("API_TOKEN")
        base_url = os.getenv("BASE_URL")
        
        st.success("Environment variables saved to .env file.")

# Only proceed if all environment variables are set
if username and api_token and base_url:
    # Load the homepage IDs from homepages.csv
    homepages_df = pd.read_csv(HOMEPAGES_FILE_PATH)
    homepages = [(row['homepage_id'], get_page_title(row['homepage_id'])) for _, row in homepages_df.iterrows()]

    # Filter out protected homepage IDs for the 'to' column dropdown
    unprotected_homepages = [(row['homepage_id'], get_page_title(row['homepage_id'])) for _, row in homepages_df.iterrows() if not row.get('protected', 'true')]

    # Get all child pages for all homepage IDs
    all_child_pages = []
    for hp in homepages:
        child_pages = get_child_page_ids_and_titles(hp[0])
        all_child_pages.extend(child_pages)

    # Main panel layout
    tab1, tab2 = st.tabs(["📋 Edit Operations", "🏠 Manage Homepage IDs"])

    with tab1:
        st.header("Edit Operations")

        # Load the CSV file into a DataFrame and initialize session state if needed
        if 'edited_data' not in st.session_state:
            csv_df = read_csv(CSV_FILE_PATH)
            csv_df.fillna('', inplace=True)  # Replace NaN with empty strings
            st.session_state['edited_data'] = csv_df.copy()

        # Editable table at the top
        edited_df = st.data_editor(st.session_state['edited_data'], num_rows="dynamic")

        # Check for row deletions
        if len(edited_df) < len(st.session_state['edited_data']):
            st.session_state['edited_data'] = edited_df
            write_csv(CSV_FILE_PATH, edited_df)
            st.success("Row deleted and CSV file has been updated.")
            st.rerun()

        # Update button to save changes to the CSV
        if st.button("Update CSV"):
            # Write the updated DataFrame to the CSV
            write_csv(CSV_FILE_PATH, edited_df)
            st.success("CSV file has been updated.")

        # Add a button to trigger the copy operations
        if st.button("Copy to Confluence"):
            with st.spinner("Running copy operations..."):
                run_copy_operations()
            st.success("Copy operations completed successfully!")    

        st.header("Add Page IDs from Confluence")

        # Initialize session state for homepage ID and child pages
        if 'homepage_id' not in st.session_state:
            st.session_state['homepage_id'] = homepages[0][0] if homepages else None
        if 'child_pages' not in st.session_state:
            st.session_state['child_pages'] = []

        # Automatically fetch child pages when a homepage is selected
        homepage_id = st.selectbox("Select Homepage to Fetch Child Pages", options=homepages, format_func=lambda x: f"{x[1]} ({x[0]})")
        
        if homepage_id:
            st.session_state['homepage_id'] = homepage_id[0]  # Use the ID part of the tuple
            st.session_state['child_pages'] = get_child_page_ids_and_titles(homepage_id[0])
            page_title = homepage_id[1]  # Get the title part of the tuple

        # Display child pages and allow selection
        if st.session_state['child_pages']:
            st.write(f"Child pages for homepage: {page_title}")
            selected_page = st.selectbox("Select a page to add", options=st.session_state['child_pages'], format_func=lambda x: f"{x[1]} ({x[0]})")
            
            if selected_page:
                from_id, _ = selected_page
                to_id = st.selectbox("Select Destination Homepage", options=unprotected_homepages, format_func=lambda x: f"{x[1]} ({x[0]})")
                prefix = st.text_input("Enter Prefix (Optional)")
                
                if st.button("Add to CSV"):
                    append_to_csv(CSV_FILE_PATH, from_id, to_id[0], prefix)
                    st.success(f"Added page ID {from_id} to the CSV.")
                    # Update the CSV file immediately in the table
                    st.session_state['edited_data'] = read_csv(CSV_FILE_PATH)
                    st.rerun()  # Refresh the page to show the new row
        else:
            if st.session_state['homepage_id']:
                st.warning(f"No child pages found for homepage: {page_title}")

    with tab2:
        st.header("Manage Homepage IDs")

        # Load homepages data
        homepages_df = pd.read_csv(HOMEPAGES_FILE_PATH)

        # Ensure homepage_id is treated as a string to avoid dtype conflicts
        homepages_df['homepage_id'] = homepages_df['homepage_id'].astype(str)

        # Add a column to display the homepage title
        homepages_df['homepage_title'] = homepages_df['homepage_id'].apply(get_page_title)

        # Rearrange the columns for better display
        display_df = homepages_df[['homepage_title', 'homepage_id', 'protected']]

        # Editable table for homepage IDs and their protection status
        st.subheader("Edit Homepage IDs")
        original_display_df = display_df.copy()  # Copy to check for deletions later
        edited_display_df = st.data_editor(display_df, num_rows="dynamic", key='homepages_editor')

        # Detect if rows have been deleted by comparing the original and edited DataFrame lengths
        if len(edited_display_df) < len(original_display_df):
            st.warning("Rows have been deleted. Updating the CSV file...")
            # Sync changes back to the original DataFrame before saving
            edited_homepages_df = homepages_df.copy()
            edited_homepages_df['homepage_id'] = edited_display_df['homepage_id'].astype(str)
            edited_homepages_df['protected'] = edited_display_df['protected']

            # Write the updated DataFrame to the CSV file
            write_csv(HOMEPAGES_FILE_PATH, edited_homepages_df[['homepage_id', 'protected']])
            st.success("Homepage IDs and protection status have been updated.")
            st.rerun()  # Refresh the page to reflect the changes

        # Button to save changes made in the table
        if st.button("Update Homepage IDs"):
            # Sync changes back to the original DataFrame before saving
            edited_homepages_df = homepages_df.copy()
            edited_homepages_df['homepage_id'] = edited_display_df['homepage_id'].astype(str)
            edited_homepages_df['protected'] = edited_display_df['protected']

            # Write the updated DataFrame to the CSV file
            write_csv(HOMEPAGES_FILE_PATH, edited_homepages_df[['homepage_id', 'protected']])
            st.success("Homepage IDs and protection status have been updated.")

        st.subheader("Add New Homepage ID")

        new_homepage_id = st.text_input("New Homepage ID")
        new_protected_status = st.checkbox("Mark as Protected", value=False)

        if st.button("Add Homepage ID"):
            if new_homepage_id:
                if new_homepage_id in homepages_df['homepage_id'].values:
                    st.error(f"Homepage ID {new_homepage_id} already exists.")
                else:
                    new_entry = pd.DataFrame([{'homepage_id': new_homepage_id, 'protected': new_protected_status}])

                    # Use pd.concat to add the new row to the DataFrame
                    homepages_df = pd.concat([homepages_df, new_entry], ignore_index=True)

                    # Write the updated DataFrame to the CSV file and update the displayed table
                    write_csv(HOMEPAGES_FILE_PATH, homepages_df[['homepage_id', 'protected']])
                    st.success(f"Added new homepage ID {new_homepage_id} with protection status set to {new_protected_status}.")

                    # Refresh the table after adding
                    display_df = homepages_df[['homepage_title', 'homepage_id', 'protected']]
                    display_df['homepage_id'] = display_df['homepage_id'].astype(str)
                    st.rerun()
            else:
                st.error("Please enter a valid homepage ID.")
        


else:
    st.stop()  # Stop the script if environment variables are not set
