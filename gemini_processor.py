import os
import google.generativeai as genai
import json
import re
from dotenv import load_dotenv

def initialize_gemini():
    """Initializes and returns the Gemini Pro model."""
    load_dotenv()  # Load environment variables from .env file
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("FATAL: GEMINI_API_KEY not found in .env file.")
        return None
    
    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash", # Using a powerful and efficient model
    )
    return model

def analyze_message_with_gemini(model, message_text):
    """
    Analyzes a single WhatsApp message to extract structured data about auto parts.

    Args:
        model: The initialized Gemini model.
        message_text: The raw text of the WhatsApp message.

    Returns:
        A dictionary containing the extracted information, or None if parsing fails.
    """
    if not model:
        print("Cannot analyze message: Gemini model is not initialized.")
        return None

    # This is the structured prompt for the AI
    prompt = f"""
    You are an expert data extractor for an auto parts sales agent. 
    Your task is to analyze a WhatsApp message and extract structured information.

    Analyze the following message text:
    ---
    {message_text}
    ---

    Extract the following fields and return the result as a single line of valid JSON:
    - "product": The specific part being requested or sold (e.g., "Bumper", "Headlight", "Nosecut").
    - "make": The car brand (e.g., "Toyota", "Nissan", "Mazda"). If not mentioned, use "N/A".
    - "type": The specific model of the car (e.g., "Harrier", "Belta", "Fielder"). If not mentioned, use "N/A".
    - "year": The manufacturing year of the car or part. If not mentioned, use "N/A".
    - "price_ksh": The price in Kenya Shillings. Extract only the number, no commas or currency symbols. If not mentioned, use 0.
    - "other_details": Any other relevant information like color, side (left/right), condition (new/used), or contact info. If none, use "N/A".

    Example 1:
    Message: "Hi can i get nosecut for toyato belta?"
    JSON Output: {{"product": "Nosecut", "make": "Toyota", "type": "Belta", "year": "N/A", "price_ksh": 0, "other_details": "N/A"}}

    Example 2:
    Message: "Both sides Back lights Bei poa"
    JSON Output: {{"product": "Back lights", "make": "N/A", "type": "N/A", "year": "N/A", "price_ksh": 0, "other_details": "Both sides, Bei poa"}}
    
    Example 3:
    Message: "I need a front bumper for a 2015 Toyota Harrier, silver. Price?"
    JSON Output: {{"product": "Bumper", "make": "Toyota", "type": "Harrier", "year": "2015", "price_ksh": 0, "other_details": "Front, silver"}}

    Now, provide the JSON output for the message above.
    """

    try:
        response = model.generate_content(prompt)
        # A more robust regex to find either a JSON object or array
        match = re.search(r'(\[.*\]|\{.*\})', response.text, re.DOTALL)
        if match:
            json_string = match.group(0)
            return json.loads(json_string)
        else:
            print(f"Warning: Could not find a valid JSON object or array in Gemini's response.")
            print(f"Raw response was: {response.text}")
            return []
    except Exception as e:
        print(f"Error during Gemini matching call or JSON parsing: {e}")
        print(f"Raw response was: {response.text if 'response' in locals() else 'N/A'}")
        return []

def classify_message_type(model, message_text):
    """
    Classifies a message as either a 'BUYING_REQUEST' or 'OTHER'.

    Returns:
        A string 'BUYING_REQUEST' or 'OTHER'.
    """
    if not model:
        print("Cannot classify message: Gemini model is not initialized.")
        return "OTHER"

    prompt = f'''
    You are a message classifier for an auto parts sales group. Your task is to determine if a message is a request to buy a part.
    - If the message is a request to buy, asking for a part, or inquiring about availability, classify it as "BUYING_REQUEST".
    - For all other messages (e.g., greetings, sales offers, replies with prices), classify it as "OTHER".

    Analyze the following message:
    ---
    {message_text}
    ---

    Examples:
    Message: "Hi can i get nosecut for toyato belta?" -> BUYING_REQUEST
    Message: "I have a bumper for sale, 15000ksh" -> OTHER
    Message: "Good morning everyone" -> OTHER
    Message: "Still available" -> OTHER
    Message: "Looking for side mirror for Honda Fit" -> BUYING_REQUEST

    What is the classification of the message above? Respond with only "BUYING_REQUEST" or "OTHER".
    '''
    try:
        response = model.generate_content(prompt)
        classification = response.text.strip()
        if classification in ["BUYING_REQUEST", "OTHER"]:
            return classification
        return "OTHER" # Default if the response is unexpected
    except Exception as e:
        print(f"Error during message classification: {e}")
        return "OTHER"

def find_matches_in_catalog(model, buying_request_text, catalog_items):
    """
    Compares a buying request to a list of catalog items and finds matches.

    Args:
        model: The initialized Gemini model.
        buying_request_text: The text of the buyer's message.
        catalog_items: A list of dictionaries, where each dictionary is a catalog item.

    Returns:
        A list of dictionaries of the matching items, or an empty list.
    """
    if not model:
        print("Cannot find matches: Gemini model is not initialized.")
        return []
    
    if not catalog_items:
        print("Cannot find matches: Seller catalog is empty.")
        return []

    # Format the catalog items for the prompt
    catalog_string = "\n".join([f"- {json.dumps(item)}" for item in catalog_items])

    prompt = f'''
    You are an intelligent auto parts matching agent. Your goal is to find relevant items from a seller's catalog that match a customer's buying request.

    This is the seller's catalog:
    ---
    {catalog_string}
    ---

    This is the customer's buying request:
    ---
    {buying_request_text}
    ---

    Your task:
    1. Analyze the customer's request.
    2. Compare the request against every item in the catalog. A good match should consider the product, make, type, and year. The "other_details" field should also be considered for relevance.
    3. Return a single valid JSON array containing ONLY the full JSON objects of the items from the catalog that are a good match.
    4. If there are no matches, return an empty JSON array `[]`.

    Do not include any other text, explanations, or markdown formatting in your response. Only the JSON array.

    Example:
    If the catalog contains `{{"id": 1, "product": "Bumper", "make": "Toyota", "type": "Harrier", "price_ksh": 15000}}` and the request is "I need a harrier bumper", your response must be:
    `[{{"id": 1, "product": "Bumper", "make": "Toyota", "type": "Harrier", "price_ksh": 15000}}]`
    '''

    try:
        response = model.generate_content(prompt)
        # Clean the response to ensure it's valid JSON
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error during Gemini matching call or JSON parsing: {e}")
        print(f"Raw response was: {response.text if 'response' in locals() else 'N/A'}")
        return []

def detect_fraud_report_with_gemini(model, message_text):
    """
    Analyzes a message to determine if it's a fraud report and extracts details.

    Args:
        model: The initialized Gemini model.
        message_text: The raw text of the WhatsApp message.

    Returns:
        A dictionary with "phone_number" and "reason" if it's a fraud report, otherwise None.
    """
    if not model:
        print("Cannot analyze for fraud: Gemini model is not initialized.")
        return None

    prompt = f'''
    You are a security analyst for a sales group. Your task is to determine if a message is reporting a fraudulent number.
    A fraud report typically contains a phone number and a reason, like "is a conman", "scammer", "don't trust", "stole from me".

    Analyze the following message:
    ---
    {message_text}
    ---

    If this is a fraud report, extract the phone number being reported and the reason.
    Return the result as a single line of valid JSON with two keys: "phone_number" and "reason".
    The phone number should be in the format +254XXXXXXXXX.

    If this is NOT a fraud report, return a JSON object with null values: {{"phone_number": null, "reason": null}}

    Examples:
    Message: "Beware of +254712345678, he is a conman." -> {{"phone_number": "+254712345678", "reason": "He is a conman."}}
    Message: "That guy 0712345678 is a scammer" -> {{"phone_number": "+254712345678", "reason": "Is a scammer"}}
    Message: "I have a bumper for sale" -> {{"phone_number": null, "reason": null}}
    Message: "Thank you for the part" -> {{"phone_number": null, "reason": null}}

    Provide the JSON output for the message above.
    '''
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            json_string = match.group(0)
            data = json.loads(json_string)
            if data.get("phone_number"):
                return data
        return None
    except Exception as e:
        print(f"Error during fraud detection call or JSON parsing: {e}")
        return None
