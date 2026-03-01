import streamlit as st
import pandas as pd
from io import BytesIO

from analyzer import analyze_excel
from schedule_builder import build_schedule
from faculty_processor import extract_faculty_data
import doc_generator
from duty_allocator import generate_master_supervision_global
from pixel_master_export import export_pixel_perfect


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

    if "Name of faculty" not in teacher_df.columns or "Department" not in teacher_df.columns:
        st.error("Excel must contain columns: 'Name of faculty' and 'Department'")
        return

    st.success("Faculty file loaded successfully ✅")

    # ==============================
    # SESSION TYPES
    # ==============================

    st.markdown("## Define Session Types")

    if "sessions" not in st.session_state:
        st.session_state.sessions = []

    if st.button("➕ Add Session"):
        st.session_state.sessions.append({"name": "", "time": ""})
        st.rerun()

    for i, session in enumerate(st.session_state.sessions):

        col1, col2, col3 = st.columns([3, 3, 1])

        session["name"] = col1.text_input(
            "Session Name",
            value=session["name"],
            key=f"sname_{i}"
        )

        session["time"] = col2.text_input(
            "Session Time",
            value=session["time"],
            key=f"stime_{i}"
        )

        if col3.button("❌", key=f"del_session_{i}"):
            st.session_state.sessions.pop(i)
            st.rerun()

    session_dict = {
        s["name"]: s["time"]
        for s in st.session_state.sessions
        if s["name"]
    }

    # ==============================
    # ALLOCATION BLOCKS
    # ==============================

    st.markdown("## Date-wise Allocation")

    if "allocations" not in st.session_state:
        st.session_state.allocations = []

    if st.button("➕ Add Allocation"):
        st.session_state.allocations.append({
            "date": None,
            "session": "",
            "supervisors": 1,
            "avoid": []
        })
        st.rerun()

    for i, block in enumerate(st.session_state.allocations):

        st.markdown(f"### Allocation {i+1}")

        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

        block["date"] = col1.date_input(
            "Date",
            value=block["date"],
            key=f"date_{i}"
        )

        block["session"] = col2.selectbox(
            "Session",
            list(session_dict.keys()) if session_dict else [""],
            index=list(session_dict.keys()).index(block["session"])
            if block["session"] in session_dict else 0,
            key=f"session_{i}"
        )

        if col3.button("❌", key=f"del_alloc_{i}"):
            st.session_state.allocations.pop(i)
            st.rerun()

        if col4.button("📄", key=f"dup_alloc_{i}"):
            new_block = {
                "date": block["date"],
                "session": block["session"],
                "supervisors": block["supervisors"],
                "avoid": block["avoid"].copy()
            }
            st.session_state.allocations.append(new_block)
            st.rerun()

        if block["session"] in session_dict:
            st.markdown(f"**Time:** {session_dict[block['session']]}")

        block["supervisors"] = st.number_input(
            "Number of Supervisors",
            min_value=1,
            value=block["supervisors"],
            key=f"sup_{i}"
        )

        block["avoid"] = st.multiselect(
            "Avoid Teachers (This Allocation)",
            teacher_df["Name of faculty"].tolist(),
            default=block["avoid"],
            key=f"avoid_{i}"
        )

    allow_two_duties = st.checkbox("Allow 2 Duties Per Day")

    priority_list = st.multiselect(
        "Priority Teachers",
        teacher_df["Name of faculty"].tolist()
    )

    # ==============================
    # GENERATE MASTER
    # ==============================

    if st.button("Generate Master Supervision"):

        if not st.session_state.allocations:
            st.error("Please add at least one allocation.")
            return

        allocation_blocks = []

        for block in st.session_state.allocations:

            if not block["date"] or not block["session"]:
                st.error("Please complete all allocation fields.")
                return

            allocation_blocks.append({
                "Date": block["date"],
                "Session": block["session"],
                "Time": session_dict.get(block["session"], ""),
                "Supervisors": block["supervisors"],
                "Avoid": block["avoid"]
            })

        try:
            full_master = generate_master_supervision_global(
                teacher_df=teacher_df,
                allocation_blocks=allocation_blocks,
                allow_two_duties=allow_two_duties,
                priority_list=priority_list
            )

            st.session_state.generated_master = full_master
            st.success("Master Supervision Generated ✅")

        except Exception as e:
            st.error(str(e))

    # ==============================
    # PREVIEW + EXPORT
    # ==============================

    if "generated_master" in st.session_state:

        edited_master = st.data_editor(
            st.session_state.generated_master,
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

        # Pixel Perfect Export
        pixel_buffer = export_pixel_perfect(edited_master)

        st.download_button(
            label="📥 Download Master Supervision (Institution Format)",
            data=pixel_buffer,
            file_name="Master_Supervision_Pixel_Perfect.xlsx",
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
