from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_individual_doc(faculty, schedule, analysis):

    doc = Document()
    doc.add_heading("Individual Supervision Chart", level=1)

    doc.add_paragraph(f"Name: {faculty['name']}")
    doc.add_paragraph(f"Department: {faculty['department']}")

    table = doc.add_table(rows=1, cols=4)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    headers = ["Sr.No", "Date", "Session", "Time"]
    for i, header in enumerate(headers):
        table.rows[0].cells[i].text = header

    sr = 1
    first_data_col = min(analysis["date_columns"].keys())

    for date, sessions in schedule.items():
        for session_name, session_time, col_idx in sessions:

            data_index = col_idx - first_data_col

            if data_index < len(faculty["data"]) and faculty["data"][data_index] == 1:

                row = table.add_row().cells
                row[0].text = str(sr)
                row[1].text = date
                row[2].text = session_name
                row[3].text = session_time
                sr += 1

    return doc


def combine_documents(individual_docs):

    master_doc = Document()

    for i, (_, doc) in enumerate(individual_docs):
        for element in doc.element.body:
            master_doc.element.body.append(element)

        if i < len(individual_docs) - 1:
            master_doc.add_page_break()

    return master_doc
