from playwright.sync_api import sync_playwright
import os

#head or no head
head = False
CANVAS_URL = "https://creanlutheran.instructure.com/login/saml"

def save_auth():
    google_email = os.getenv("GOOGLE_EMAIL")
    google_password = os.getenv("GOOGLE_PASSWORD")
    
    if not google_email or not google_password:
        print("Error: GOOGLE_EMAIL and GOOGLE_PASSWORD env variables must be set")
        print("Usage: export GOOGLE_EMAIL='email@gmail.com' GOOGLE_PASSWORD='password'")
        print("Then : python3 setup_auth.py")
        return
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not head)
        context = browser.new_context()
        page = context.new_page()
        
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
        print("Success! auth.json saved. Move this file to your server.")
        browser.close()

if __name__ == "__main__":
    save_auth()