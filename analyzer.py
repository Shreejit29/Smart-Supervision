import pandas as pd
import re

def extract_session_info(text):

    text = str(text)
    text = text.replace("–", "-").replace("—", "-")
    text = re.sub(r"\s+", " ", text)

    if re.search(r'session\s*-\s*ii', text, re.IGNORECASE):
        session_name = "Session - II"
    elif re.search(r'session\s*-\s*i\b', text, re.IGNORECASE):
        session_name = "Session - I"
    else:
        return None, None

    time_match = re.search(r'(\d{1,2}[:.]\d{2}.*)', text)
    session_time = time_match.group(1) if time_match else ""

    return session_name, session_time.strip()


def analyze_excel(df):

    analysis = {
        "header_row": None,
        "faculty_col": None,
        "dept_col": None,
        "date_columns": {},
        "session_row": None,
        "session_mapping": {}
    }

    # Detect header row
    for i, row in df.iterrows():
        row_text = " ".join(str(x) for x in row if pd.notna(x)).lower()
        if "faculty" in row_text or "name" in row_text:
            analysis["header_row"] = i
            break

    if analysis["header_row"] is None:
        return None, "Faculty header not found"

    header = df.iloc[analysis["header_row"]]

    # Detect faculty & department column
    for idx, cell in enumerate(header):
        text = str(cell).lower()
        if "name" in text:
            analysis["faculty_col"] = idx
        if "department" in text:
            analysis["dept_col"] = idx

        date_match = re.search(r'\d{1,2}[/\-]\d{1,2}[/\-]\d{4}', str(cell))
        if date_match:
            analysis["date_columns"][idx] = date_match.group()

    # Session row
    session_row = analysis["header_row"] + 1
    analysis["session_row"] = session_row

    session_data = df.iloc[session_row]

    for idx, cell in enumerate(session_data):
        if pd.notna(cell) and re.search(r'session', str(cell), re.IGNORECASE):
            session_name, session_time = extract_session_info(cell)
            if session_name:
                analysis["session_mapping"][idx] = (session_name, session_time)

    return analysis, None
