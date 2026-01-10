# THIS IS JUST TO MAKE A PRETTY FAKE GRAPH FOR A SCREENSHOT
# DO NOT ACTUALLY RUN TS

import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta

conn = sqlite3.connect('fake_grades.db')

conn.execute("""
CREATE TABLE IF NOT EXISTS grades (
    date TEXT,
    course TEXT,
    score REAL
)
""")

courses = [
    "AP US Hist.",
    "AP Lang",
    "AP Calc BC",
    "(H) Physics"
]

start_date = datetime.now() - timedelta(days=14)
data = []

for i in range(15):
    day = start_date + timedelta(days=i)
    for course in courses:
        score = round(random.uniform(70, 100), 2)
        data.append((day.strftime("%Y-%m-%d"), course, score))

conn.executemany("INSERT INTO grades (date, course, score) VALUES (?, ?, ?)", data)
conn.commit()
conn.close()

print("Fake grades.db created!")
