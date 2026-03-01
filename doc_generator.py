from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT


def generate_individual_doc(faculty, schedule, analysis, template_file=None):

    # If template uploaded → use it
    if template_file:
        doc = Document(template_file)
    else:
        doc = Document()

    # -------------------------
    # Replace placeholders
    # -------------------------

    for paragraph in doc.paragraphs:
        if "{{NAME}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{NAME}}", faculty["name"])

        if "{{DEPARTMENT}}" in paragraph.text:
            paragraph.text = paragraph.text.replace("{{DEPARTMENT}}", str(faculty["department"]))

    # -------------------------
    # Add Supervision Table
    # -------------------------

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
