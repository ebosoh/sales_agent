

import time
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
GROUP_NAME = "Grogan spares zone" 
# The debugging port must match the one you open the browser with.
DEBUGGING_PORT = 9223
# ---------------------

def find_and_click_group(page):
    """Tries to find a chat by its name and click it."""
    print(f"Searching for group: '{GROUP_NAME}'...")
    try:
        # First, wait for the chat list container to be visible.
        # The selector '[aria-label="Chat list"]' is specific to WhatsApp Web's structure.
        chat_list_selector = '[aria-label="Chat list"]'
        print(f"Waiting for the chat list ({chat_list_selector}) to be visible...")
        page.wait_for_selector(chat_list_selector, timeout=30000)
        print("Chat list is visible.")

        # Now, search within the chat list for our group.
        # This uses a regular expression for case-insensitive matching.
        group_element = page.locator(chat_list_selector).get_by_text(GROUP_NAME, exact=False)
        
        print(f"Found group '{GROUP_NAME}'. Waiting for it to be stable...")
        # Ensure the element is stable and clickable before proceeding
        group_element.wait_for(state='visible', timeout=15000)
        
        print("Found group. Getting its coordinates...")
        bounding_box = group_element.bounding_box()
        if not bounding_box:
            raise Exception("Could not get the bounding box of the group element.")

        x = bounding_box['x'] + bounding_box['width'] / 2
        y = bounding_box['y'] + bounding_box['height'] / 2

        print(f"Coordinates found. Clicking at ({x}, {y})...")
        page.mouse.click(x, y)
        
        print("Successfully clicked on the group.")
        return True
    except Exception as e:
        print(f"Error: Could not find or click group '{GROUP_NAME}'.")
        print(f"Please ensure the browser is open, you are logged into WhatsApp, and a group with this exact name exists.")
        print(f"Playwright error: {e}")
        return False

def main():
    with sync_playwright() as p:
        try:
            print(f"Attempting to connect to browser on port {DEBUGGING_PORT}...")
            # This connects to the browser you launched manually
            browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUGGING_PORT}")
            context = browser.contexts[0]  # Get the default browser context
            page = context.pages[0] # Get the active page
            print("Successfully connected to the browser.")

            # Now that we're connected, try to find the group
            find_and_click_group(page)

        except Exception as e:
            print(f"Error: Could not connect to the browser on port {DEBUGGING_PORT}.")
            print("Please ensure you have launched the browser with the correct command.")
            print(f"Playwright error: {e}")
        
        print("\nTest finished.")

if __name__ == "__main__":
    main()

