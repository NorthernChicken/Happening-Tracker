import sqlite3
import datetime
import subprocess
import json
import os
import time
from playwright.sync_api import sync_playwright

#if you want head or not
head = False
GRADES_URL = "url"
#systemd perms and pyenv mess this up in prod so its hardcoded now
AUTH_PATH = os.path.join(os.path.dirname(__file__), "auth.json")

def reauthenticate():
    print("\nAuth failed or expired. Re-authing..")
    
    #When testing over ssh ts is needed
    # fake x server on linux
    result = subprocess.run(
        [
            "xvfb-run",
            "-a",
            "/opt/Happening-Tracker/venv/bin/python",
            "setup_auth.py"
        ],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )

    
    if result.returncode != 0:
        raise RuntimeError("Re-authentication failed. run setup_auth.py manually")
    
    print("🇺🇸 Re-authentication successful 🇺🇸")

def fetch_and_store():
    now = datetime.datetime.now().isoformat(timespec="seconds")
    
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
            context = browser.new_context(storage_state=AUTH_PATH)
            page = context.new_page()
            
            print(f"Visiting {GRADES_URL}...")
            #fahh cookies problems
            page.goto("https://creanlutheran.instructure.com/", wait_until="networkidle")
            page.goto(GRADES_URL, wait_until="networkidle")

            if "/login" in page.url:
                raise RuntimeError("auth cookies rejected")


            page.wait_for_selector(
                "table.course_details.student_grades tbody tr",
                timeout=30_000
            )


            courses_data = []
            #???
            rows = page.query_selector_all(
                "table.course_details.student_grades tbody tr"
            )


            for row in rows:
                name_el = row.query_selector("td.course a")
                score_el = row.query_selector("td.percent")
                
                if name_el and score_el:
                    course_name = name_el.inner_text().strip()
                    score_text = score_el.inner_text().strip().replace('%', '')
                    
                    try:
                        score = float(score_text)
                        courses_data.append((now, course_name, score))
                        print(f"Found: {course_name} - {score}%")
                    except ValueError:
                        print(f"Skipping {course_name} (No numerical grade)")

            browser.close()
            
            if courses_data:
                save_to_db(courses_data)
            else:
                time.sleep(10)
                print("No grades found")
    
    except (json.JSONDecodeError, ValueError, IOError, OSError) as e:
        print(f"Error loading auth: {e}")
        reauthenticate()
        # should catch expired auth here too but idk how well
        # edit: it doesnt.
        fetch_and_store()
def save_to_db(data):
    conn = sqlite3.connect('grades.db')
    #idk how this works
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
