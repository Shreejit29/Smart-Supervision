import streamlit as st
import pandas as pd
from io import BytesIO

from analyzer import analyze_excel
from schedule_builder import build_schedule
from faculty_processor import extract_faculty_data
import doc_generator
from duty_allocator import generate_master_supervision


def run_auto_mode():

    template_file = st.file_uploader(
        "Upload Word Template (Optional)",
        type=["docx"]
    )

    teacher_file = st.file_uploader(
        "Upload Faculty & Department Excel",
        type=["xlsx", "xls"]
    )

    if not teacher_file:
        return

    teacher_df = pd.read_excel(teacher_file)

    teacher_df.columns = teacher_df.columns.str.strip()
    teacher_df.columns = teacher_df.columns.str.replace('\n', '', regex=True)

    teacher_df.rename(columns=lambda x: x.strip(), inplace=True)

    if "Name of faculty" not in teacher_df.columns or "Department" not in teacher_df.columns:
        st.error("Excel must contain columns: 'Name of faculty' and 'Department'")
        return

    st.success("Faculty file loaded successfully ✅")

    # ==================================================
    # STEP 1: DEFINE SESSION TYPES
    # ==================================================

    st.markdown("## Define Session Types")

    num_sessions = st.number_input(
        "Number of Session Types",
        min_value=1,
        value=1
    )

    session_dict = {}

    for i in range(int(num_sessions)):

        col1, col2 = st.columns(2)

        s_name = col1.text_input("Session Name", key=f"sname_{i}")
        s_time = col2.text_input("Session Time", key=f"stime_{i}")

        if s_name:
            session_dict[s_name] = s_time

    # ==================================================
    # STEP 2: DATE-WISE ALLOCATION BLOCKS
    # ==================================================

    st.markdown("## Date-wise Allocation")

    num_allocations = st.number_input(
        "Number of Allocation Entries",
        min_value=1,
        value=1
    )

    allocation_blocks = []

    for i in range(int(num_allocations)):

        st.markdown(f"### Allocation {i+1}")

        col1, col2, col3 = st.columns(3)

        date = col1.date_input("Date", key=f"date_{i}")

        session_choice = col2.selectbox(
            "Session",
            list(session_dict.keys()),
            key=f"session_{i}"
        )

        time_display = session_dict.get(session_choice, "")
        col3.markdown(f"**Time:** {time_display}")

        col4, col5 = st.columns(2)

        supervisors_required = col4.number_input(
            "Number of Supervisors",
            min_value=1,
            value=1,
            key=f"sup_{i}"
        )

        avoid_teachers = col5.multiselect(
            "Avoid Teachers (This Allocation)",
            teacher_df["Name of faculty"].tolist(),
            key=f"avoid_{i}"
        )

        allocation_blocks.append({
            "Date": date,
            "Session": session_choice,
            "Time": time_display,
            "Supervisors": supervisors_required,
            "Avoid": avoid_teachers
        })

    allow_two_duties = st.checkbox("Allow 2 Duties Per Day")

    priority_list = st.multiselect(
        "Priority Teachers",
        teacher_df["Name of faculty"].tolist()
    )

    # ==================================================
    # GENERATE MASTER
    # ==================================================

    if st.button("Generate Master Supervision"):

        full_master = pd.DataFrame()

        try:
            for block in allocation_blocks:

                formatted_date = pd.to_datetime(block["Date"])

                schedule_list = [{
                    "Date": formatted_date.strftime("%d-%m-%Y"),
                    "Day": formatted_date.day_name(),
                    "Session": block["Session"],
                    "Time": block["Time"]
                }]

                master_df = generate_master_supervision(
                    teacher_df=teacher_df,
                    schedule_list=schedule_list,
                    supervisors_required=block["Supervisors"],
                    avoid_list=block["Avoid"],
                    priority_list=priority_list,
                    allow_two_duties=allow_two_duties,
                )

                full_master = pd.concat([full_master, master_df])

            st.session_state["generated_master"] = full_master
            st.success("Master Supervision Generated ✅")

        except Exception as e:
            st.error(str(e))

    # ==================================================
    # PREVIEW + DUTY SUMMARY
    # ==================================================

    if "generated_master" in st.session_state:

        edited_master = st.data_editor(
            st.session_state["generated_master"],
            use_container_width=True
        )

        st.markdown("## Teacher-wise Duty Count")

        duty_summary = (
            edited_master["Name of faculty"]
            .value_counts()
            .reset_index()
        )

        duty_summary.columns = ["Name of faculty", "Total Duties"]

        st.dataframe(duty_summary)

        # Export Excel
        buffer = BytesIO()
        edited_master.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Download Master Supervision (Excel)",
            data=buffer,
            file_name="Master_Supervision.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        if st.button("Confirm & Generate Individual Charts"):

            analysis, error = analyze_excel(edited_master)

            if error:
                st.error("Edited Master Format Invalid")
                return

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
