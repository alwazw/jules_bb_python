import json
import os
import requests
import sys
from datetime import datetime
import xml.etree.ElementTree as ET

# --- Path Configuration ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CHAT_LOG_FILE = os.path.join(PROJECT_ROOT, 'customer_service', 'chat_history', 'chat_log.json')
SECRETS_FILE = os.path.join(PROJECT_ROOT, 'secrets.txt')
CP_HISTORY_LOG_FILE = os.path.join(PROJECT_ROOT, 'logs', 'canada_post', 'cp_shipping_history_log.json')

# Add project root to the Python path
sys.path.insert(0, PROJECT_ROOT)
from common.utils import get_canada_post_credentials
from shipping.canada_post.cp_shipping.validate_cp_shipment import get_tracking_summary as get_cp_tracking_summary

def load_gemini_api_key():
    """Loads the Gemini API key from the secrets file."""
    try:
        with open(SECRETS_FILE, "r") as f:
            for line in f:
                if line.startswith("GEMINI_API_KEY="):
                    return line.strip().split("=")[1]
    except FileNotFoundError:
        print(f"Error: {SECRETS_FILE} not found.")
        return None
    return None

API_KEY = load_gemini_api_key()
API_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
HEADERS = {"Content-Type": "application/json"}

def log_chat(session_id, user_message, bot_response, intent):
    """Logs a chat interaction to the chat_log.json file."""
    log_entry = {
        'session_id': session_id,
        'timestamp': datetime.now().isoformat(),
        'user_message': user_message,
        'bot_response': bot_response,
        'intent': intent
    }

    log_data = []
    if os.path.exists(CHAT_LOG_FILE):
        with open(CHAT_LOG_FILE, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError:
                pass

    log_data.append(log_entry)

    os.makedirs(os.path.dirname(CHAT_LOG_FILE), exist_ok=True)
    with open(CHAT_LOG_FILE, 'w') as f:
        json.dump(log_data, f, indent=2)

def call_gemini_api(prompt):
    """Calls the Gemini API with a given prompt."""
    if not API_KEY:
        return "Error: GEMINI_API_KEY not configured."

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(API_ENDPOINT, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status()
        response_json = response.json()
        return response_json['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.RequestException as e:
        return f"Error calling Gemini API: {e}"
    except (KeyError, IndexError) as e:
        return f"Error parsing Gemini API response: {e}"

def get_intent(message):
    """Uses the Gemini API to determine the user's intent."""
    prompt = f"""
    Analyze the following user message and classify it into one of these intents:
    - check_order_status
    - request_return
    - change_address
    - general_inquiry

    User message: "{message}"

    Intent:
    """
    intent = call_gemini_api(prompt).strip()
    if intent in ["check_order_status", "request_return", "change_address", "general_inquiry"]:
        return intent
    return "general_inquiry"

def extract_order_id(message):
    """Uses the Gemini API to extract the order ID from a user message."""
    prompt = f"""
    Extract the order ID from the following user message. The order ID is usually in the format 'XXX-XXXXXXX-X' or a similar alphanumeric string.
    If no order ID is found, return 'None'.

    User message: "{message}"

    Order ID:
    """
    order_id = call_gemini_api(prompt).strip()
    return order_id if order_id != 'None' else None

def get_tracking_pin_for_order(order_id):
    """
    Retrieves the tracking pin for a given order ID from the shipping history log.
    """
    if not os.path.exists(CP_HISTORY_LOG_FILE):
        return None

    with open(CP_HISTORY_LOG_FILE, 'r') as f:
        try:
            history = json.load(f)
            for entry in history:
                details = entry.get("shipment_details", "")
                if f"<customer-ref-no>{order_id}</customer-ref-no>" in details:
                    root = ET.fromstring(details)
                    tracking_pin_element = root.find(".//{http://www.canadapost.ca/ws/shipment-v8}tracking-pin")
                    if tracking_pin_element is not None:
                        return tracking_pin_element.text
        except (json.JSONDecodeError, ET.ParseError):
            return None
    return None

def handle_check_order_status(user_message):
    """Handles the check_order_status intent."""
    order_id = extract_order_id(user_message)
    if not order_id:
        return "I couldn't find an order ID in your message. Please provide your order ID so I can check the status."

    tracking_pin = get_tracking_pin_for_order(order_id)
    if not tracking_pin:
        return f"I couldn't find any shipping information for order {order_id}. It's possible the order hasn't shipped yet or the order ID is incorrect."

    api_user, api_password, _, _, _ = get_canada_post_credentials()
    if not all([api_user, api_password]):
        return "I'm sorry, I'm unable to connect to the shipping provider at the moment. Please try again later."

    tracking_summary = get_cp_tracking_summary(api_user, api_password, tracking_pin)

    if tracking_summary:
        # This is a simplification. A more robust implementation would parse the XML and format it nicely.
        return f"Here is the tracking summary for your order {order_id}:\n\n{tracking_summary}"
    else:
        return f"I found a tracking number for your order ({tracking_pin}), but I was unable to get the current status from Canada Post. Please try again later or use the tracking number on the Canada Post website."


def handle_request_return(user_message):
    """Handles the request_return intent."""
    order_id = extract_order_id(user_message)
    if not order_id:
        return "I couldn't find an order ID in your message. Please provide your order ID to request a return."
    return f"I am processing a return for order {order_id}. This feature is coming soon!"

def handle_change_address(user_message):
    """Handles the change_address intent."""
    order_id = extract_order_id(user_message)
    if not order_id:
        return "I couldn't find an order ID in your message. Please provide your order ID to change the address."
    return f"I am handling an address change for order {order_id}. This feature is coming soon!"

def handle_general_inquiry(message):
    """Handles general inquiries using the Gemini API."""
    return call_gemini_api(f"Answer the following user question: {message}")

def chat(session_id, user_message):
    """Main chat function."""
    intent = get_intent(user_message)

    if intent == "check_order_status":
        bot_response = handle_check_order_status(user_message)
    elif intent == "request_return":
        bot_response = handle_request_return(user_message)
    elif intent == "change_address":
        bot_response = handle_change_address(user_message)
    else:
        bot_response = handle_general_inquiry(user_message)

    log_chat(session_id, user_message, bot_response, intent)
    return bot_response

import time

if __name__ == '__main__':
    session_id = "session_123"
    print("User: I want to track my order 261221057-A.")
    print(f"Bot: {chat(session_id, 'I want to track my order 261221057-A.')}")
    time.sleep(5)
    print("\nUser: I need to return order 260842103-A.")
    print(f"Bot: {chat(session_id, 'I need to return order 260842103-A.')}")
    time.sleep(5)
    print("\nUser: I want to change my shipping address for order 261047886-A.")
    print(f"Bot: {chat(session_id, 'I want to change my shipping address for order 261047886-A.')}")
    time.sleep(5)
    print("\nUser: What's the capital of France?")
    print(f"Bot: {chat(session_id, 'What is the capital of France?')}")
