

import sqlite3
from gemini_processor import initialize_gemini, find_matches_in_catalog

def main():
    """
    Tests the AI matching function by comparing a sample buying request
    against the items in the seller's catalog.
    """
    model = initialize_gemini()
    if not model:
        return

    # --- This is our sample buying request ---
    BUYING_REQUEST = "I need a bumper for a Toyota Harrier"
    # -----------------------------------------

    conn = sqlite3.connect('sales_agent.db')
    # We use row_factory to get results as dictionaries, which is what our function expects
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        print("Fetching items from the seller's catalog...")
        cursor.execute("SELECT id, product, make, type, year, price_ksh, other_details FROM seller_catalog")
        catalog_items_raw = cursor.fetchall()
        # Convert the sqlite3.Row objects to plain dictionaries
        catalog_items = [dict(item) for item in catalog_items_raw]
    except sqlite3.OperationalError as e:
        print(f"Error fetching catalog: {e}")
        conn.close()
        return
        
    conn.close()

    if not catalog_items:
        print("The seller_catalog table is empty. Please add some items via the app to test matching.")
        return

    print(f"--- Testing AI Matching ---")
    print(f"Buying Request: \"{BUYING_REQUEST}\"")
    print(f"Catalog contains {len(catalog_items)} item(s).")
    print("Catalog being sent to AI:")
    for item in catalog_items:
        print(f"  - {item}")

    matching_items = find_matches_in_catalog(model, BUYING_REQUEST, catalog_items)

    print(f"\nAI found {len(matching_items)} match(es):")
    if matching_items:
        for item in matching_items:
            print(f"  -> {item}")
    else:
        print("  -> No matches found.")
        
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    main()

