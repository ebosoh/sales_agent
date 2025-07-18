

import time
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
DEBUGGING_PORT = 9223
# ---------------------

def get_my_number(page):
    """
    Navigates to the profile section and scrapes the user's own phone number.
    """
    print("Attempting to scrape your phone number...")
    try:
        # 1. Click on the user's own profile picture/icon to open the profile sidebar.
        # This is usually the first button in the header.
        profile_button_selector = 'header button'
        print("Clicking the profile button...")
        page.locator(profile_button_selector).first.click()
        
        # 2. Wait for the profile sidebar to appear.
        # The user's name/number is usually in an editable div.
        profile_panel_selector = 'div[contenteditable="true"]'
        print("Waiting for the profile panel to appear...")
        profile_panel = page.locator(profile_panel_selector).first
        profile_panel.wait_for(timeout=10000)

        # 3. Extract the number/name from a span inside the editable div.
        my_identifier = profile_panel.locator('span').first.inner_text()
        print(f"Successfully found identifier: '{my_identifier}'")
        
        # 4. Close the profile panel by clicking the 'back' button
        back_button_selector = 'button[aria-label="Back"]'
        page.locator(back_button_selector).click()
        
        return my_identifier

    except Exception as e:
        print(f"Error: Could not scrape your phone number.")
        print(f"Please ensure you are logged in and the main chat list is visible.")
        print(f"Playwright error: {e}")
        return None

def main():
    with sync_playwright() as p:
        try:
            print(f"Attempting to connect to browser on port {DEBUGGING_PORT}...")
            browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUGGING_PORT}")
            context = browser.contexts[0]
            page = context.pages[0]
            print("Successfully connected to the browser.")

            my_number = get_my_number(page)
            
            if my_number:
                print(f"\n--- SUCCESS ---")
                print(f"Detected your WhatsApp identifier as: {my_number}")
                print(f"-----------------")
            else:
                print("\n--- FAILED ---")
                print("Could not automatically detect your identifier.")
                print("--------------")

        except Exception as e:
            print(f"Error: Could not connect to the browser on port {DEBUGGING_PORT}.")
            print(f"Playwright error: {e}")
        
        print("\nTest finished.")

if __name__ == "__main__":
    main()

