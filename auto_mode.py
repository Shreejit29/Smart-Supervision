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

    if teacher_file:

        teacher_df = pd.read_excel(teacher_file)

        teacher_df.columns = teacher_df.columns.str.strip()
        teacher_df.columns = teacher_df.columns.str.replace('\n', '', regex=True)

        columns_lower = [col.lower() for col in teacher_df.columns]

        if "name of faculty" not in columns_lower or "department" not in columns_lower:
            st.write("Detected Columns:", teacher_df.columns.tolist())
            st.error("Excel must contain columns: 'Name of faculty' and 'Department'")
            return

        rename_map = {}
        for col in teacher_df.columns:
            if col.lower() == "name of faculty":
                rename_map[col] = "Name of faculty"
            if col.lower() == "department":
                rename_map[col] = "Department"

        teacher_df.rename(columns=rename_map, inplace=True)

        st.success("Faculty file loaded successfully ✅")

        # -------------------------
        # Define Sessions
        # -------------------------

        st.markdown("## Define Sessions")

        num_session_types = st.number_input(
            "Number of Session Types",
            min_value=1,
            value=1
        )

        session_definitions = []

        for i in range(int(num_session_types)):

            col1, col2, col3 = st.columns(3)

            session_name = col1.text_input("Session Name", key=f"sname_{i}")
            session_time = col2.text_input("Session Time", key=f"stime_{i}")
            supervisor_count = col3.number_input(
                "Supervisors Required",
                min_value=1,
                value=1,
                key=f"scount_{i}"
            )

            session_avoid = st.multiselect(
                f"Avoid Teachers For {session_name}",
                teacher_df["Name of faculty"].tolist(),
                key=f"savoid_{i}"
            )

            session_definitions.append({
                "Session": session_name,
                "Time": session_time,
                "Supervisors": supervisor_count,
                "SessionAvoid": session_avoid
            })

        # -------------------------
        # Dates
        # -------------------------

        st.markdown("## Select Exam Dates")

        selected_dates = st.date_input("Choose Dates", value=[])

        allow_two_duties = st.checkbox("Allow 2 Duties Per Day")

        global_avoid = st.multiselect(
            "Avoid Teachers (All Sessions)",
            teacher_df["Name of faculty"].tolist()
        )

        priority_list = st.multiselect(
            "Priority Teachers",
            teacher_df["Name of faculty"].tolist()
        )

        # -------------------------
        # Generate Master
        # -------------------------

        if st.button("Generate Master Supervision"):

            if not selected_dates:
                st.error("Please select at least one date")
                return

            full_master = pd.DataFrame()

            try:
                for session_def in session_definitions:

                    schedule_list = []

                    for date in selected_dates:
                        formatted_date = pd.to_datetime(date)

                        schedule_list.append({
                            "Date": formatted_date.strftime("%d-%m-%Y"),
                            "Day": formatted_date.day_name(),
                            "Session": session_def["Session"],
                            "Time": session_def["Time"]
                        })

                    combined_avoid = list(
                        set(global_avoid + session_def["SessionAvoid"])
                    )

                    master_df = generate_master_supervision(
                        teacher_df=teacher_df,
                        schedule_list=schedule_list,
                        supervisors_required=session_def["Supervisors"],
                        avoid_list=combined_avoid,
                        priority_list=priority_list,
                        allow_two_duties=allow_two_duties,
                    )

                    full_master = pd.concat([full_master, master_df])

                st.session_state["generated_master"] = full_master
                st.success("Master Supervision Generated ✅")

            except Exception as e:
                st.error(str(e))

    # -------------------------
    # Preview Section
    # -------------------------

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

        excel_buffer = BytesIO()
        edited_master.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Download Master Supervision (Excel)",
            data=excel_buffer,
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
                    None
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
