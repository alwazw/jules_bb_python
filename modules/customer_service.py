import json
import os
import requests
from datetime import datetime, timedelta

# --- Configuration ---
LOGS_DIR = os.path.join('logs')
CS_LOGS_DIR = os.path.join(LOGS_DIR, 'customer_service')
MESSAGES_FILE = os.path.join(CS_LOGS_DIR, 'messages.json')
API_BASE_URL = "https://marketplace.bestbuy.ca/api"

from core.utils import get_best_buy_api_key

# --- Message Fetching and Processing ---

def get_new_messages(api_key):
    """ Fetches new message threads from the Mirakl API. """
    print("Connecting to Mirakl API to check for new messages...")
    headers = {"Authorization": api_key}
    updated_since = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    params = {"with_messages": "true", "updated_since": updated_since}
    all_threads = []
    next_page_token = None
    while True:
        if next_page_token:
            params["page_token"] = next_page_token
        try:
            response = requests.get(f"{API_BASE_URL}/inbox/threads", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            all_threads.extend(data.get("data", []))
            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break
        except requests.exceptions.RequestException as e:
            print(f"Error fetching messages: {e}")
            return []
    print(f"Found {len(all_threads)} updated threads.")
    return all_threads

def transform_threads_to_messages(threads):
    """ Transforms the raw thread data from the API into a simplified message format. """
    transformed_messages = []
    for thread in threads:
        if thread.get("messages"):
            last_message = thread["messages"][-1]
            transformed_messages.append({
                "message_id": last_message["id"],
                "thread_id": thread["id"],
                "order_id": thread["entities"][0]["id"] if thread.get("entities") else "N/A",
                "customer_id": last_message["from"].get("id", "N/A"),
                "subject": thread["topic"]["value"],
                "message": last_message["body"],
                "timestamp": last_message["date_created"],
                "status": "UNREAD"
            })
    return transformed_messages

def save_messages_to_json(messages, file_path=MESSAGES_FILE):
    """ Saves a list of messages to a JSON file. """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with open(file_path, "r") as f:
            existing_messages = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_messages = []
    existing_ids = {msg["message_id"] for msg in existing_messages}
    new_messages = [msg for msg in messages if msg["message_id"] not in existing_ids]
    if not new_messages:
        print("No new messages to save.")
        return
    updated_messages = existing_messages + new_messages
    with open(file_path, "w") as f:
        json.dump(updated_messages, f, indent=4)
    print(f"Successfully saved {len(new_messages)} new messages to {file_path}.")

# --- Main Orchestrator ---

def main_orchestrator():
    """ Main function to run the customer service message aggregation phase. """
    print("\n=============================================")
    print("===      Customer Service Aggregation     ===")
    print("=============================================")
    api_key = get_best_buy_api_key()
    if not api_key:
        print("Could not load API key. Aborting.")
        return
    try:
        threads = get_new_messages(api_key)
        if threads:
            messages = transform_threads_to_messages(threads)
            save_messages_to_json(messages)
        print("--- Customer Service Aggregation Complete ---")
    except Exception as e:
        print(f"An error occurred during the customer service phase: {e}")
    print("=============================================")

if __name__ == "__main__":
    main_orchestrator()
