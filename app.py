import streamlit as st
from upload_mode import run_upload_mode
from auto_mode import run_auto_mode

st.set_page_config(page_title="Supervision Chart Generator", layout="wide")
st.title("📋 Supervision Chart Generator")

mode = st.radio(
    "Choose Mode",
    ["Upload Master Supervision", "Auto Generate Master Supervision"]
)

if mode == "Upload Master Supervision":
    run_upload_mode()

elif mode == "Auto Generate Master Supervision":
    run_auto_mode()
