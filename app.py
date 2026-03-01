import streamlit as st
import pandas as pd
from io import BytesIO

from analyzer import analyze_excel
from schedule_builder import build_schedule
from faculty_processor import extract_faculty_data
import doc_generator

from duty_allocator import generate_master_supervision

st.set_page_config(page_title="Supervision Chart Generator", layout="wide")
st.title("📋 Supervision Chart Generator")

# =========================================================
# MODE SELECTION
# =========================================================

mode = st.radio(
    "Choose Mode",
    ["Upload Master Supervision", "Auto Generate Master Supervision"]
)

template_file = st.file_uploader(
    "Upload Word Template (Optional)",
    type=["docx"]
)

# =========================================================
# MODE 1: UPLOAD MASTER SUPERVISION (OLD SYSTEM - UNCHANGED)
# =========================================================

if mode == "Upload Master Supervision":

    uploaded_file = st.file_uploader(
        "Upload Master Supervision Excel",
        type=["xlsx", "xls"]
    )

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
            st.write(f"Total Exam Sessions: {len(schedule)}")

            if st.button("Generate Supervision Charts"):

                individual_docs = []

                for faculty in faculty_list:
                    doc = doc_generator.generate_individual_doc(
                        faculty,
                        schedule,
                        analysis,
                        template_file
                    )
                    individual_docs.append((faculty["name"], doc))

                master_doc = doc_generator.combine_documents(individual_docs)

                buffer = BytesIO()
                master_doc.save(buffer)
                buffer.seek(0)

                st.download_button(
                    label="📥 Download Supervision Charts",
                    data=buffer,
                    file_name="Supervision_Charts.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# =========================================================
# MODE 2: AUTO GENERATE MASTER SUPERVISION
# =========================================================

elif mode == "Auto Generate Master Supervision":

    teacher_file = st.file_uploader(
        "Upload Faculty & Department Excel",
        type=["xlsx", "xls"]
    )

    if teacher_file:

        teacher_df = pd.read_excel(teacher_file)

        # ===============================
        # SMART COLUMN CLEANING (FIXED)
        # ===============================

        teacher_df.columns = teacher_df.columns.str.strip()
        teacher_df.columns = teacher_df.columns.str.replace('\n', '', regex=True)

        # Case-insensitive check
        columns_lower = [col.lower() for col in teacher_df.columns]

        if "name of faculty" not in columns_lower or "department" not in columns_lower:
            st.write("Detected Columns:", teacher_df.columns.tolist())
            st.error("Excel must contain columns: 'Name of faculty' and 'Department'")
        else:
            # Rename to exact expected format
            rename_map = {}
            for col in teacher_df.columns:
                if col.lower() == "name of faculty":
                    rename_map[col] = "Name of faculty"
                if col.lower() == "department":
                    rename_map[col] = "Department"

            teacher_df.rename(columns=rename_map, inplace=True)

            st.success("Faculty file loaded successfully ✅")

            # -----------------------------
            # Schedule Input
            # -----------------------------

            num_sessions = st.number_input(
                "Number of Exam Sessions",
                min_value=1,
                value=1
            )

            schedule_list = []

            for i in range(int(num_sessions)):
                st.markdown(f"### Session {i+1}")

                col1, col2 = st.columns(2)
                date = col1.text_input(f"Date {i+1}", key=f"date_{i}")
                day = col2.text_input(f"Day {i+1}", key=f"day_{i}")

                col3, col4 = st.columns(2)
                session_name = col3.text_input(f"Session {i+1}", key=f"session_{i}")
                time = col4.text_input(f"Time {i+1}", key=f"time_{i}")

                schedule_list.append({
                    "Date": date,
                    "Day": day,
                    "Session": session_name,
                    "Time": time
                })

            supervisors_required = st.number_input(
                "Supervisors Required Per Session",
                min_value=1,
                value=1
            )

            allow_two_duties = st.checkbox("Allow 2 Duties Per Day")

            avoid_list = st.multiselect(
                "Avoid Assigning These Teachers",
                teacher_df["Name of faculty"].tolist()
            )

            priority_list = st.multiselect(
                "Priority Teachers",
                teacher_df["Name of faculty"].tolist()
            )

            # -----------------------------
            # Generate Master
            # -----------------------------

            if st.button("Generate Master Supervision"):

                try:
                    master_df = generate_master_supervision(
                        teacher_df=teacher_df,
                        schedule_list=schedule_list,
                        supervisors_required=supervisors_required,
                        avoid_list=avoid_list,
                        priority_list=priority_list,
                        allow_two_duties=allow_two_duties,
                    )

                    st.session_state["generated_master"] = master_df
                    st.success("Master Supervision Generated ✅")

                except Exception as e:
                    st.error(str(e))

    # ------------------------------------------
    # PREVIEW + CONFIRM SECTION
    # ------------------------------------------

    if "generated_master" in st.session_state:

        st.markdown("## Preview & Edit Master Supervision")

        edited_master = st.data_editor(
            st.session_state["generated_master"],
            use_container_width=True
        )

        if st.button("Confirm & Generate Individual Charts"):

            analysis, error = analyze_excel(edited_master)

            if error:
                st.error("Edited Master Format Invalid")
            else:

                schedule = build_schedule(analysis)
                faculty_list = extract_faculty_data(edited_master, analysis)

                individual_docs = []

                for faculty in faculty_list:
                    doc = doc_generator.generate_individual_doc(
                        faculty,
                        schedule,
                        analysis,
                        template_file
                    )
                    individual_docs.append((faculty["name"], doc))

                master_doc = doc_generator.combine_documents(individual_docs)

                buffer = BytesIO()
                master_doc.save(buffer)
                buffer.seek(0)

                st.download_button(
                    label="📥 Download Supervision Charts",
                    data=buffer,
                    file_name="Supervision_Charts.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
