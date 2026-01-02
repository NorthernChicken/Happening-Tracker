import sqlite3
import datetime
import subprocess
import json
import os
from playwright.sync_api import sync_playwright

#if you want head or not
head = False
GRADES_URL = "canvas grade URL" 

def reauthenticate():
    """Run setup_auth.py to refresh authentication."""
    print("\n⚠️🇮🇱🇮🇱🇮🇱 Authentication failed or expired. Re-authenticating...🇮🇱🇮🇱🇮🇱🇮")
    print("Set GOOGLE_EMAIL and GOOGLE_PASSWORD env variables")
    
    if not os.getenv("GOOGLE_EMAIL") or not os.getenv("GOOGLE_PASSWORD"):
        print("Error: GOOGLE_EMAIL and GOOGLE_PASSWORD env variables are not set")
        print("Set them:")
        print("  export GOOGLE_EMAIL='email@gmail.com'")
        print("  export GOOGLE_PASSWORD='password'")
        raise EnvironmentError("Missing Google credentials")
    
    result = subprocess.run(["python3", "setup_auth.py"], cwd=os.path.dirname(os.path.abspath(__file__)))
    
    if result.returncode != 0:
        raise RuntimeError("Re-authentication failed. run setup_auth.py manually")
    
    print("🇺🇸 Re-authentication successful 🇺🇸")

def fetch_and_store():
    today = datetime.date.today().isoformat()
    
    auth_file = "auth.json"
    auth_valid = False
    
    if os.path.exists(auth_file):
        try:
            with open(auth_file, 'r') as f:
                json.load(f)
            auth_valid = True
        except (json.JSONDecodeError, ValueError):
            print("auth.json is corrupted or empty.")
            auth_valid = False
    else:
        print("auth.json not found.")
        auth_valid = False
    
    # Re-authenticate if it doesnt exist but doesnt check for expiry
    if not auth_valid:
        reauthenticate()
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not head)
            context = browser.new_context(storage_state="auth.json")
            page = context.new_page()
            
            print(f"Visiting {GRADES_URL}...")
            page.goto(GRADES_URL)

            page.wait_for_selector("table.course_details") 

            courses_data = []
            rows = page.query_selector_all("table.course_details tr")
            
            for row in rows:
                name_el = row.query_selector("td.course a")
                score_el = row.query_selector("td.percent")
                
                if name_el and score_el:
                    course_name = name_el.inner_text().strip()
                    score_text = score_el.inner_text().strip().replace('%', '')
                    
                    try:
                        score = float(score_text)
                        courses_data.append((today, course_name, score))
                        print(f"Found: {course_name} - {score}%")
                    except ValueError:
                        print(f"Skipping {course_name} (No numerical grade)")

            browser.close()
            
            if courses_data:
                save_to_db(courses_data)
            else:
                print("No grades found")
    
    except (json.JSONDecodeError, ValueError, IOError, OSError) as e:
        print(f"Error loading auth: {e}")
        reauthenticate()
        # should catch expired auth here too but idk how well
        fetch_and_store()
def save_to_db(data):
    conn = sqlite3.connect('grades.db')
    #idk what this does
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS grades 
                 (date TEXT, course TEXT, score REAL, 
                 UNIQUE(date, course) ON CONFLICT REPLACE)''')
    
    c.executemany('INSERT INTO grades VALUES (?,?,?)', data)
    conn.commit()
    conn.close()
    print("Database updated.")

if __name__ == "__main__":
    fetch_and_store()