import os
import subprocess
import sqlite3

import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# -------------------- Authentication setup --------------------
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

# Login widget in the sidebar
name, authentication_status, username = authenticator.login("Login", "sidebar")
if not authentication_status:
    st.error("❌ Username/password incorrect")
    st.stop()
else:
    st.sidebar.success(f"Welcome, {name}")
    authenticator.logout("Logout", "sidebar")

# -------------------- App Configuration --------------------
DB_PATH = "voc_pipeline.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create / open SQLite connection
conn = sqlite3.connect(DB_PATH, check_same_thread=False)

# -------------------- UI --------------------
st.title("VoC Pipeline Explorer")

st.sidebar.header("Upload & Process Interviews")
uploaded_files = st.sidebar.file_uploader(
    "Select .txt or .docx files", type=["txt", "docx"], accept_multiple_files=True
)

if uploaded_files:
    # Save uploaded files locally
    local_paths = []
    for f in uploaded_files:
        dest = os.path.join(UPLOAD_DIR, f.name)
        with open(dest, "wb") as out_file:
            out_file.write(f.getbuffer())
        local_paths.append(dest)
    st.sidebar.success(f"Saved {len(local_paths)} file(s).")

    # Trigger processing pipeline
    if st.sidebar.button("Process"):
        try:
            # Ingest → Stage 1 → Stage 2
            subprocess.run(
                ["python", "run_pipeline.py", "--step", "ingest", "--inputs"] + local_paths,
                check=True,
            )
            subprocess.run(["python", "batch_code.py"], check=True)
            subprocess.run(
                ["python", "batch_validate.py", "--input", "stage1_output.csv", "--output", "validated_quotes.csv"],
                check=True,
            )

            # Load validated CSV back into SQLite
            df = pd.read_csv("validated_quotes.csv")
            df.to_sql("validated_quotes", conn, if_exists="replace", index=False)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_criteria ON validated_quotes(criteria);")

            st.sidebar.success("✅ Processing complete and database updated!")
        except subprocess.CalledProcessError as e:
            st.sidebar.error(f"Pipeline error: {e}")
        except Exception as e:
            st.sidebar.error(f"Unexpected error: {e}")

# -------------------- Data Explorer --------------------
st.header("Validated Quotes")

# Ensure the table exists
try:
    all_criteria = pd.read_sql("SELECT DISTINCT criteria FROM validated_quotes", conn)["criteria"].tolist()
except Exception:
    all_criteria = []

# Allow filtering by criteria
selected = st.multiselect("Filter by criteria", all_criteria, default=all_criteria)

if selected:
    placeholders = ",".join("?" for _ in selected)
    query = f"SELECT * FROM validated_quotes WHERE criteria IN ({placeholders}) LIMIT 200"
    df_display = pd.read_sql(query, conn, params=selected)
else:
    df_display = pd.DataFrame(columns=[])

st.write(f"Showing {len(df_display)} rows")
st.dataframe(df_display)
