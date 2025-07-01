import streamlit_authenticator as stauth

# --- Authentication setup ---------------------------------------------
credentials = {
    "usernames": {
        "nick":   {"name": "Nick",   "password": "$2b$12$lGal21pEt57loTjkokAENOjVd2z2UsooIwZesDFPK4qSRFmTX4ujS"},
        "mai":    {"name": "Mai",    "password": "$2b$12$lGal21pEt57loTjkokAENOjVd2z2UsooIwZesDFPK4qSRFmTX4ujS"},
        "jordan": {"name": "Jordan", "password": "$2b$12$lGal21pEt57loTjkokAENOjVd2z2UsooIwZesDFPK4qSRFmTX4ujS"},
        "drew":   {"name": "Drew",   "password": "$2b$12$lGal21pEt57loTjkokAENOjVd2z2UsooIwZesDFPK4qSRFmTX4ujS"},
        "anne":   {"name": "Anne",   "password": "$2b$12$lGal21pEt57loTjkokAENOjVd2z2UsooIwZesDFPK4qSRFmTX4ujS"},
    }
}

authenticator = stauth.Authenticate(
    credentials,
    cookie_name="voc_auth_cookie",
    key="voc_secret_key",
    cookie_expiry_days=1,
)

name, authentication_status, username = authenticator.login("Login", "sidebar")

if not authentication_status:
    st.error("❌ Username/password incorrect")
    st.stop()
else:
    st.sidebar.success(f"Welcome, {name}")
    authenticator.logout("Logout", "sidebar")

import streamlit as st
import pandas as pd
import sqlite3
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

DB = "voc_pipeline.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

conn = sqlite3.connect(DB, check_same_thread=False)

st.title("VoC Pipeline Explorer")

# Sidebar: Upload & Process
st.sidebar.header("Upload Interviews")
files = st.sidebar.file_uploader(
    "Select .txt or .docx", type=["txt", "docx"], accept_multiple_files=True
)
paths = []
if files:
    for f in files:
        dest = os.path.join(UPLOAD_DIR, f.name)
        with open(dest, "wb") as out:
            out.write(f.getbuffer())
        paths.append(dest)
    st.sidebar.success(f"Saved {len(paths)} file(s).")

    if st.sidebar.button("Process"):
        # Run your pipeline steps
        subprocess.run(["python", "run_pipeline.py", "--step", "ingest", "--inputs"] + paths, check=True)
        subprocess.run(["python", "batch_code.py"], check=True)
        subprocess.run(["python", "batch_validate.py"], check=True)
        # Refresh SQLite table
        conn.execute("DROP TABLE IF EXISTS validated_quotes;")
        conn.execute(".mode csv")
        conn.execute(".import validated_quotes.csv validated_quotes")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_criteria ON validated_quotes(criteria);")
        st.sidebar.success("Processing complete!")

# Main: Data Explorer
st.header("Validated Quotes")
criteria = pd.read_sql("SELECT DISTINCT criteria FROM validated_quotes", conn)["criteria"].tolist()
sel = st.multiselect("Filter criteria", criteria, default=criteria)
placeholders = ",".join("?" for _ in sel)
query = f"""
SELECT * FROM validated_quotes
WHERE criteria IN ({placeholders})
LIMIT 200
"""
df = pd.read_sql(query, conn, params=sel)
st.write(f"Showing {len(df)} rows")
st.dataframe(df)
