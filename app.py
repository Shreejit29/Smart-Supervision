import streamlit as st
import pandas as pd
from io import BytesIO
from docx import Document

from analyzer import analyze_excel
from schedule_builder import build_schedule
from faculty_processor import extract_faculty_data
from doc_generator import generate_individual_doc, combine_documents

st.set_page_config(page_title="Supervision Chart Generator", layout="wide")

st.title("📋 Supervision Chart Generator")

uploaded_file = st.file_uploader("Upload Master Supervision Excel", type=["xlsx", "xls"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    analysis, error = analyze_excel(df)

    if error:
        st.error(error)
    else:
        st.success("Excel structure detected successfully ✅")

        schedule = build_schedule(analysis)
        faculty_list = extract_faculty_data(df, analysis)

        st.write(f"Faculty Detected: {len(faculty_list)}")
        st.write(f"Total Exam Dates: {len(schedule)}")

        if st.button("Generate Supervision Charts"):

            individual_docs = []

            for faculty in faculty_list:
                doc = generate_individual_doc(faculty, schedule, analysis)
                individual_docs.append((faculty["name"], doc))

            master_doc = combine_documents(individual_docs)

            buffer = BytesIO()
            master_doc.save(buffer)
            buffer.seek(0)

            st.download_button(
                label="📥 Download Charts",
                data=buffer,
                file_name="Supervision_Charts.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
