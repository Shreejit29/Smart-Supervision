def extract_faculty_data(df, analysis):

    faculty_list = []

    start_row = analysis["session_row"] + 1
    first_data_col = min(analysis["date_columns"].keys())

    for i in range(start_row, len(df)):

        row = df.iloc[i]
        name = row[analysis["faculty_col"]]

        if str(name).lower() == "total" or str(name).strip() == "":
            break

        department = ""
        if analysis["dept_col"] is not None:
            department = row[analysis["dept_col"]]

        supervision_values = row[first_data_col:].values
        supervision_binary = [1 if x == 1 else 0 for x in supervision_values]

        faculty_list.append({
            "name": name,
            "department": department,
            "data": supervision_binary
        })

    return faculty_list
