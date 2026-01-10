from playwright.sync_api import sync_playwright
import os

#head or no head
head = False
CANVAS_URL = "url"

# Google trying to prevent bots so this is trying to make it look like a real person
# this might break in like a month tho
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

def save_auth():
    # Screw proper security measures, env variables were too annoying. Im just hardcoding ts email and password
    google_email = "email"
    google_password = "password"
    
    with sync_playwright() as p:
        # Anti anti bot
        browser = p.chromium.launch(
            headless=not head,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )

        context = browser.new_context(user_agent=USER_AGENT)

        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
        """)

        print(f"Opening {CANVAS_URL}...")
        page.goto(CANVAS_URL)

        page.wait_for_load_state("networkidle")

        # chatgpted all ts playwright lmao
        try:
            google_button = page.query_selector("button:has-text('Google')")
            if google_button:
                google_button.click()
                page.wait_for_load_state("networkidle")
        except:
            pass
        
        print("Entering email")
        try:
            email_input = page.wait_for_selector("input[type='email']", timeout=5000)
            email_input.fill(google_email)

            next_button = page.query_selector("button:has-text('Next')")
            if next_button:
                next_button.click()
            else:
                email_input.press("Enter")
            
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Warning: Could not find email input: {e}")
        
        print("Entering password")
        try:
            password_input = page.wait_for_selector("input[type='password']", timeout=5000)
            password_input.fill(google_password)
            
            next_button = page.query_selector("button:has-text('Next')")
            if next_button:
                next_button.click()
            else:
                password_input.press("Enter")
            
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Warning: Could not find password input: {e}")
        
        print("Waiting for authentication to complete")
        page.wait_for_load_state("domcontentloaded")
        
        try:
            page.wait_for_selector("table#grades_summary", timeout=10000)
            print("Successfully logged in")
        except:
            print("Note: Could not verify grades page loaded, check browser window")
            print("If login failed, close the browser and try again with correct credentials")

        context.storage_state(path="auth.json")
        print("IT PROBABLY WORKED auth.json saved.")
        browser.close()

if __name__ == "__main__":
    save_auth()
