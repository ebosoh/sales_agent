

import time
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
# The exact name of the group you want to test with
# IMPORTANT: You must have a group with this exact name in your WhatsApp
GROUP_NAME = "Grogan spares zone" 
# ---------------------

def find_and_click_group(page):
    """Tries to find a chat by its name and click it."""
    print(f"Searching for group: '{GROUP_NAME}'...")
    try:
        # WhatsApp Web uses specific selectors. We'll use one that finds a span with the group title.
        # The `get_by_text` locator is a reliable way to find elements by their visible text.
        # We set a timeout to allow time for the chat list to load.
        group_element = page.get_by_text(GROUP_NAME, exact=True)
        
        # Wait for the element to be visible, just in case it's slow to render
        group_element.wait_for(timeout=15000)
        
        print(f"Found group '{GROUP_NAME}'. Clicking it...")
        group_element.click()
        print("Successfully clicked on the group.")
        return True
    except Exception as e:
        print(f"Error: Could not find or click group '{GROUP_NAME}'.")
        print(f"Please ensure a group with this exact name exists and is visible in your chat list.")
        print(f"Playwright error: {e}")
        return False

def main():
    with sync_playwright() as p:
        # We use a persistent context to save login sessions
        # This creates a 'user_data' folder where cookies and session data are stored
        context = p.chromium.launch_persistent_context(
            user_data_dir="wa_user_data",
            headless=False,
            slow_mo=50  # Slows down actions to make it easier to see what's happening
        )
        page = context.new_page()
        
        print("Navigating to WhatsApp Web...")
        page.goto("https://web.whatsapp.com")
        
        print("\n" + "="*50)
        print("ACTION REQUIRED: Please scan the QR code if you are not logged in.")
        print("The script will automatically continue once the chat list is loaded.")
        print("="*50 + "\n")
        
        try:
            # We wait for a known element that indicates the main chat interface has loaded.
            # The selector for the "Chats" header is a good candidate.
            page.wait_for_selector("h1:has-text('Chats')", timeout=90000)
            print("WhatsApp is loaded. Waiting a few seconds for the chat list to populate...")
            time.sleep(5) # Extra wait for chats to appear
            
            find_and_click_group(page)
            
        except Exception as e:
            print(f"Error: Failed to load WhatsApp Web main page. Timeout? Error: {e}")
        
        print("\nTest finished. The browser will remain open for 10 seconds.")
        time.sleep(10)
        context.close()

if __name__ == "__main__":
    main()

