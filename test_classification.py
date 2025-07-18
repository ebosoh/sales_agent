

import sqlite3
from gemini_processor import initialize_gemini, classify_message_type

def main():
    """
    Tests the message classification function by fetching sample messages
    and printing their classification.
    """
    model = initialize_gemini()
    if not model:
        return

    conn = sqlite3.connect('sales_agent.db')
    cursor = conn.cursor()

    try:
        # Get some buying requests and some other messages to test both cases
        cursor.execute("""
            SELECT message_text FROM (
                SELECT message_text FROM messages WHERE message_text LIKE '%need%' OR message_text LIKE '%looking for%' OR message_text LIKE '%pata%' LIMIT 3
            )
            UNION ALL
            SELECT message_text FROM (
                SELECT message_text FROM messages WHERE message_text NOT LIKE '%need%' AND message_text NOT LIKE '%looking for%' AND message_text NOT LIKE '%pata%' LIMIT 3
            )
        """)
        sample_messages = cursor.fetchall()
    except sqlite3.OperationalError as e:
        print(f"Error fetching messages: {e}")
        conn.close()
        return
        
    conn.close()

    if not sample_messages:
        print("No messages found in the database to test.")
        return

    print("--- Testing Gemini Message Classification ---")
    for i, msg_tuple in enumerate(sample_messages):
        message_text = msg_tuple[0]
        classification = classify_message_type(model, message_text)
        print(f"\n[{i+1}] Message: \"{message_text}\"")
        print(f"  -> AI Classification: {classification}")
        
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()

