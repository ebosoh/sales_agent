

import time
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
DEBUGGING_PORT = 9223
# ---------------------

def scrape_active_chat(page):
    """Scrapes messages from the currently active chat panel."""
    print("Attempting to scrape messages from the active chat...")
    try:
        # This is the new, more specific selector for the main chat panel.
        chat_panel_selector = '#app > div > div.x78zum5.xdt5ytf.x5yr21d > div > div.x9f619.x1n2onr6.xyw6214.x5yr21d.x6ikm8r.x10wlt62.x17dzmu4.x1i1dayz.x2ipvbc.x1w8yi2h.xyyilfv.x1iyjqo2.xpilrb4.x1t7ytsu.x1m2ixmg'
        page.wait_for_selector(chat_panel_selector, timeout=15000)
        print("Active chat panel is visible.")

        # This is the new selector for an individual message. We'll find all of them.
        message_selector = '#main > div.x1n2onr6.x1vjfegm.x1cqoux5.x14yy4lh > div > div.x10l6tqk.x13vifvy.x1o0tod.xyw6214.x9f619.x78zum5.xdt5ytf.xh8yej3.x5yr21d.x6ikm8r.x1rife3k.xjbqb8w.x1ewm37j > div.x3psx0u.xwib8y2.x1c1uobl.xrmvbpv.xh8yej3.xquzyny.xvc5jky.x11t971q > div'
        
        # Wait for at least one message to be present
        page.wait_for_selector(message_selector, timeout=15000)
        
        messages = page.query_selector_all(message_selector)
        print(f"Found {len(messages)} message containers in the current view.")

        if not messages:
            print("No messages found in the active chat panel.")
            return

        print("\n--- SCRAPED MESSAGES ---")
        for i, msg_element in enumerate(messages[-5:]): # Print the last 5 messages
            try:
                # Within each message container, we look for the actual text.
                # This selector targets the span with the selectable text.
                text_element = msg_element.query_selector('span.selectable-text')
                
                # We also try to get the sender's info, which is in a different element
                # This looks for the name/number, usually in a div with a specific data-pre-plain-text attribute
                meta_element = msg_element.query_selector('div[data-pre-plain-text]')
                
                message_text = text_element.inner_text() if text_element else "N/A"
                sender_info = meta_element.get_attribute('data-pre-plain-text') if meta_element else "N/A"

                print(f"  Message {i+1}:")
                print(f"    Sender Info: {sender_info.strip()}")
                print(f"    Text: {message_text.strip()}")
                print("-" * 20)

            except Exception as e:
                print(f"  Could not parse a message element: {e}")
        print("--- END OF SCRAPED MESSAGES ---\n")

    except Exception as e:
        print(f"Error: Could not scrape messages. Is a chat open and active?")
        print(f"Playwright error: {e}")

def main():
    with sync_playwright() as p:
        try:
            print(f"Attempting to connect to browser on port {DEBUGGING_PORT}...")
            browser = p.chromium.connect_over_cdp(f"http://localhost:{DEBUGGING_PORT}")
            context = browser.contexts[0]
            page = context.pages[0]
            print("Successfully connected to the browser.")

            print("Pausing execution for interactive selector discovery.")
            print("Please inspect the page in the browser to find the correct selectors.")
            page.pause()

            scrape_active_chat(page)

        except Exception as e:
            print(f"Error: Could not connect to the browser on port {DEBUGGING_PORT}.")
            print(f"Playwright error: {e}")
        
        print("\nTest finished.")

if __name__ == "__main__":
    main()

