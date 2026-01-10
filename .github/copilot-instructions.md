# Canvas Grade Tracker - AI Agent Instructions

## Project Overview
A Python-based grade scraping and visualization system that automatically fetches grades from Canvas LMS (Instructure), stores them in SQLite, and displays trends via a Streamlit dashboard.

## Architecture
The project uses a **three-module pipeline**:
1. **setup_auth.py** - One-time authentication setup that saves browser cookies/session state to `auth.json`
2. **fetch_grades.py** - Scheduled scraper using Playwright and stored auth to extract grades from Canvas
3. **dashboard.py** - Streamlit web UI that visualizes grade trends and provides manual refresh button

**Data Flow**: Auth tokens → Playwright scraper → SQLite database → Streamlit charts

## Key Technologies & Patterns

### Browser Automation (Playwright)
- Uses `sync_playwright()` with headless Chrome for automated Canvas navigation
- **Critical**: Authentication is **session-based** via `storage_state` parameter, not credentials
  - `context = browser.new_context(storage_state="auth.json")` loads pre-authenticated session
  - This avoids storing passwords; `auth.json` contains browser cookies/tokens
- **DOM selectors** are school-specific and may require adjustment:
  - Current: `table#grades_summary` (main container) and `table.course_details tbody tr` (individual rows)
  - Course name: `td.course a`, Score: `td.percent`
  - Comment in code: "we might need to tweak it based on your school's HTML"

### Database Schema (SQLite)
```sql
CREATE TABLE grades (
  date TEXT,
  course TEXT,
  score REAL,
  UNIQUE(date, course) ON CONFLICT REPLACE  -- Prevents duplicates, replaces on conflict
)
```
- Single table design; constraints ensure idempotent inserts
- No explicit migrations; schema created on first run

### Streamlit Dashboard
- Single-page app in `dashboard.py`
- **Refresh mechanism**: Button calls `subprocess.run(["python3", "fetch_grades.py"])` to trigger scraper
- **Charts**: Line chart with date on x-axis, score on y-axis, colored by course
- **Data display**: Shows latest grade snapshot from max date in database

## Developer Workflows

### Initial Setup
1. Run `python3 setup_auth.py` - Opens browser for manual SAML login
2. After login, press Enter in terminal to save `auth.json`
3. Move `auth.json` to server/deployment environment

### Manual Scraping
```bash
python3 fetch_grades.py  # Fetches grades and updates grades.db
```

### Running Dashboard
```bash
streamlit run dashboard.py
```
Access at `http://localhost:8501`

### Canvas URL Configuration
**School-specific URLs** in both files:
- `setup_auth.py`: `CANVAS_URL = "https://creanlutheran.instructure.com/login/saml"`
- `fetch_grades.py`: `GRADES_URL = "https://creanlutheran.instructure.com/grades"`

These **must be updated** for different Canvas instances; currently hardcoded for Crean Lutheran High School.

## Critical Troubleshooting Points

### DOM Selector Failures
If `fetch_grades.py` returns "No grades found":
1. The HTML selectors have likely changed (Canvas updates frequently)
2. Use browser DevTools to inspect current grade table structure
3. Update selectors in: `page.wait_for_selector()`, `page.query_selector_all()`, `query_selector()`
4. Common alternatives to try: `.student_assignment_grade`, `.course_grade`, `[data-testid="grade"]`

### Auth Failures
- `auth.json` contains session cookies with expiration times (visible in JSON)
- If scraper fails with 401/403, re-run `setup_auth.py` to refresh cookies
- Browser errors indicate headless/SAML issues, not code logic

### Database Corruption
- Delete `grades.db` to force fresh table creation on next scrape
- `ON CONFLICT REPLACE` means duplicate date+course pairs update existing records

## Code Patterns to Maintain

1. **Hardcoded school URLs** - These are intentional per-instance configs, not DRY violations
2. **Manual login flow** - Uses browser UI instead of API credentials for security (SAML/SSO compatible)
3. **Subprocess execution** - Dashboard refreshes via subprocess.run(), not direct function calls (process isolation)
4. **Loose HTML parsing** - Uses selectors only, no regex/parsing libraries; fragile by design but simple

## Common Modifications

### Add Different Canvas Instance
1. Update `CANVAS_URL` in `setup_auth.py`
2. Update `GRADES_URL` in `fetch_grades.py`
3. Run `setup_auth.py` with new URL
4. Test selectors against new school's HTML

### Schedule Automatic Scrapes
Add cron job (Linux/Mac) or Task Scheduler (Windows):
```bash
0 9 * * * cd /home/ajw/grades && python3 fetch_grades.py
```

### Change Grade Display Format
Modify dashboard: `st.dataframe(latest_df[['course', 'score']].style.format({"score": "{:.2f}%"}))`

### Add Database Backups
Append to `save_to_db()`: `shutil.copy('grades.db', f'grades_backup_{datetime.date.today()}.db')`

## Testing Notes
- Exit code 130 (from last terminal session) = SIGINT (manual interrupt); not an error
- Playwright requires Chrome/Chromium; install via `pip install playwright && playwright install`
- Streamlit requires `pip install streamlit pandas sqlite3` (or `requirements.txt`)
