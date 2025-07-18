

import sqlite3
from gemini_processor import initialize_gemini, analyze_message_with_gemini

def main():
    """
    Tests the Gemini processor by fetching a few messages from the database
    and running them through the analysis function.
    """
    # Initialize the AI model
    model = initialize_gemini()
    if not model:
        return

    # Connect to the database
    conn = sqlite3.connect('sales_agent.db')
    cursor = conn.cursor()

    # Fetch a few sample messages to test
    try:
        cursor.execute("SELECT message_text FROM messages ORDER BY RANDOM() LIMIT 5")
        sample_messages = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error fetching messages: {e}")
        print("Did the database get created with the 'messages' table correctly?")
        conn.close()
        return
        
    conn.close()

    if not sample_messages:
        print("No messages found in the database to test.")
        return

    print("--- Testing Gemini Analysis on Sample Messages ---")
    for i, msg_tuple in enumerate(sample_messages):
        message_text = msg_tuple[0]
        print(f"\n[{i+1}] Analyzing Message: \"{message_text}\"")
        
        extracted_data = analyze_message_with_gemini(model, message_text)
        
        if extracted_data:
            print(f"  -> Extracted JSON: {extracted_data}")
        else:
            print("  -> Failed to extract data.")
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()

