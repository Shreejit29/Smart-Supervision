def build_schedule(analysis):

    schedule = {}

    for col_idx, (session_name, session_time) in analysis["session_mapping"].items():

        nearest_date = None

        for date_col in analysis["date_columns"]:
            if abs(col_idx - date_col) <= 1:
                nearest_date = analysis["date_columns"][date_col]
                break

        if nearest_date:
            if nearest_date not in schedule:
                schedule[nearest_date] = []

            schedule[nearest_date].append(
                (session_name, session_time, col_idx)
            )

    return schedule
