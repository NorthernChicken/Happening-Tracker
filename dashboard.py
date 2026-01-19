import streamlit as st
import sqlite3
import pandas as pd
import subprocess
import altair as alt
import hashlib
import secrets
import os
from datetime import datetime, timedelta
import json
import math

st.set_page_config(page_title="Grade Tracker", layout="wide")

# SECURITY 
# THIS SHOULD PROBABLY BE AN ENV VARIABLE BUT IM LAZY
ADMIN_PASSWORD = "password123"
TOKEN_EXPIRATION_HOURS = 168

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token() -> str:
    return secrets.token_urlsafe(32)

def verify_password(password: str) -> bool:
    return hash_password(password) == hash_password(ADMIN_PASSWORD)

def is_token_valid(token_data: dict) -> bool:
    if not token_data:
        return False
    
    try:
        exp_time = datetime.fromisoformat(token_data.get("expires_at", ""))
        return datetime.now() < exp_time
    except (ValueError, TypeError):
        return False

def get_new_token() -> dict:
    return {
        "token": generate_token(),
        "expires_at": (datetime.now() + timedelta(hours=TOKEN_EXPIRATION_HOURS)).isoformat()
    }

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
if "show_log" not in st.session_state:
    st.session_state.show_log = False
if "log_output" not in st.session_state:
    st.session_state.log_output = ""
if "show_auth_modal" not in st.session_state:
    st.session_state.show_auth_modal = False

# auth ui
def show_auth_modal():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container(border=True):
            st.markdown("### Authentication Required")
            st.write("This action requires a password.")
            
            password = st.text_input("Enter password:", type="password", key="modal_auth_password")
            
            col_auth1, col_auth2 = st.columns(2)
            with col_auth1:
                if st.button("Authenticate", key="modal_auth_button", use_container_width=True):
                    if verify_password(password):
                        token_data = get_new_token()
                        st.session_state.authenticated = True
                        st.session_state.auth_token = token_data
                        st.session_state.show_auth_modal = False
                        st.success("Authenticated, token valid for {} hours".format(TOKEN_EXPIRATION_HOURS))
                        st.rerun()
                    else:
                        st.error("Invalid password")
            with col_auth2:
                if st.button("Cancel", key="modal_cancel_button", use_container_width=True):
                    st.session_state.show_auth_modal = False
                    st.rerun()

def logout():
    st.session_state.authenticated = False
    st.session_state.auth_token = None
    st.rerun()

st.title("Canvas Grade Tracker")

# logout
col1, col2, col3, col4 = st.columns([3, 1, 1, 1], gap="small")

with col4:
    if st.session_state.authenticated and st.session_state.auth_token:
        if is_token_valid(st.session_state.auth_token):
            st.success("🔒 Authenticated")
            if st.button("Logout", key="logout_button"):
                logout()
        else:
            st.error("Token expired")
            if st.button("Login again", key="reauth_button"):
                st.session_state.authenticated = False
                st.session_state.auth_token = None
                st.rerun()

# modal 🥀🥀🥀🥀🥀
if st.session_state.show_auth_modal:
    show_auth_modal()

# protected actions
# def not secure 🥀
col1, col2, col3, col4 = st.columns([1, 1, 1.5, 4.5], gap="small")
with col1:
    if st.button('Refresh'):
        if not st.session_state.authenticated or not is_token_valid(st.session_state.auth_token):
            st.session_state.show_auth_modal = True
            st.rerun()
        else:
            with st.spinner('Scraping Canvas...'):
                result = subprocess.run(["python3", "fetch_grades.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.session_state.log_output = result.stdout
                    st.session_state.show_log = True
                    st.success("Refreshed")
                else:
                    st.session_state.log_output = result.stderr
                    st.session_state.show_log = True
                    st.error("Error refreshing")

with col2:
    if st.button('View Log'):
        st.session_state.show_log = True

# reauth button
with col3:
    if st.button('Reauthenticate'):
        if not st.session_state.authenticated or not is_token_valid(st.session_state.auth_token):
            st.session_state.show_auth_modal = True
            st.rerun()
        else:
            with st.spinner('Running setup_auth...'):
                result = subprocess.run(["python3", "setup_auth.py"], capture_output=True, text=True)
                if result.returncode == 0:
                    st.session_state.log_output = result.stdout
                    st.session_state.show_log = True
                    st.success("Reauthenticated!")
                else:
                    st.session_state.log_output = result.stderr
                    st.session_state.show_log = True
                    st.error("Error reauthenticating")

# ts NOT a modal popup 🥀🥀
if st.session_state.show_log:
    modal = st.container()
    with modal:
        col1, col2 = st.columns([9, 1])
        with col1:
            st.subheader("Refresh Log")
        with col2:
            if st.button("X", key="close_log"):
                st.session_state.show_log = False
                st.rerun()

        st.code(st.session_state.log_output, language="text")

# DB
conn = sqlite3.connect('grades.db')
df = pd.read_sql("SELECT * FROM grades", conn)
conn.close()

if not df.empty:
    df['date'] = pd.to_datetime(df['date'], format='mixed')

    # Old Graph
    # st.subheader("Grade Trends")
    #
    # chart = alt.Chart(df).mark_line(point=True).encode(
    #     x='date:T',
    #     y='score:Q',
    #     color=alt.Color('course:N', legend=alt.Legend(orient='right'))
    # ).properties(height=400)
    #
    # st.altair_chart(chart, width='stretch')

    # New graph
    selection = alt.selection_point(fields=['course'], bind='legend')

    max_score = math.ceil(df['score'].max() / 10) * 10

    chart = (
        alt.Chart(df)
        .mark_line(point=True, clip=True)
        .encode(
            x=alt.X('date:T', title='Refresh Time'),
            y=alt.Y('score:Q', title='Score (%)', scale=alt.Scale(domain=(50, max_score))),
            color=alt.Color('course:N', legend=alt.Legend(orient='left')),
            opacity=alt.condition(selection, alt.value(1), alt.value(0.15))
        )
        .add_params(selection)
        .properties(height=400)
        .interactive(bind_y=False)
    )

    st.altair_chart(chart, width='stretch')


    #Table
    st.subheader("Latest Grades")
    latest_date = df['date'].max()
    latest_df = df[df['date'] == latest_date]
    st.dataframe(latest_df[['course', 'score']].style.format({"score": "{:.2f}%"}))
else:
    st.warning("No data found yet. Click Refresh")
