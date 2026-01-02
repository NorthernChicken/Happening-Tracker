import streamlit as st
import sqlite3
import pandas as pd
import subprocess
import altair as alt

st.set_page_config(page_title="Grade Tracker", layout="wide")

st.title("Canvas Grade Tracker")

if "show_log" not in st.session_state:
    st.session_state.show_log = False
if "log_output" not in st.session_state:
    st.session_state.log_output = ""

col1, col2, col3 = st.columns([1, 1, 6], gap="small")
with col1:
    if st.button('Refresh'):
        with st.spinner('Scraping Canvas...'):
            result = subprocess.run(["python3", "fetch_grades.py"], capture_output=True, text=True)
            if result.returncode == 0:
                st.session_state.log_output = result.stdout
                st.session_state.show_log = True
                st.success("Refreshed!")
            else:
                st.session_state.log_output = result.stderr
                st.session_state.show_log = True
                st.error("Error refreshing.")

with col2:
    if st.button('View Log'):
        st.session_state.show_log = True

# ts NOT a modal popup 🥀🥀
if st.session_state.show_log:
    modal = st.container()
    with modal:
        col1, col2 = st.columns([9, 1])
        with col1:
            st.subheader("Refresh Log")
        with col2:
            if st.button("X", key="close_log", width='content'):
                st.session_state.show_log = False
                st.rerun()
        
        st.code(st.session_state.log_output, language="text")

# DB
conn = sqlite3.connect('grades.db')
df = pd.read_sql("SELECT * FROM grades", conn)
conn.close()

if not df.empty:
    df['date'] = pd.to_datetime(df['date'])
    
    #Graph
    st.subheader("Grade Trends")
    
    chart = alt.Chart(df).mark_line(point=True).encode(
        x='date:T',
        y='score:Q',
        color=alt.Color('course:N', legend=alt.Legend(orient='right'))
    ).properties(height=400)
    
    st.altair_chart(chart, width='stretch')
    
    #Table
    st.subheader("Latest Grades")
    latest_date = df['date'].max()
    latest_df = df[df['date'] == latest_date]
    st.dataframe(latest_df[['course', 'score']].style.format({"score": "{:.2f}%"}))
else:
    st.warning("No data found yet. Click Refresh")