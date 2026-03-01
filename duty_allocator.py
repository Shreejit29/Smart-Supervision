import pandas as pd
import random
from collections import defaultdict


def generate_master_supervision_global(
    teacher_df,
    allocation_blocks,
    allow_two_duties=False,
    priority_list=None
):

    if priority_list is None:
        priority_list = []

    teachers = teacher_df["Name of faculty"].tolist()
    dept_map = dict(zip(teacher_df["Name of faculty"], teacher_df["Department"]))

    # Track total duties
    duty_count = defaultdict(int)

    # Track daily duties
    daily_count = defaultdict(lambda: defaultdict(int))

    master_rows = []

    for block in allocation_blocks:

        date = block["Date"]
        session = block["Session"]
        time = block["Time"]
        supervisors_required = block["Supervisors"]
        avoid_list = block["Avoid"]

        # Filter available teachers
        available_teachers = [
            t for t in teachers
            if t not in avoid_list
        ]

        # Remove teachers exceeding daily rule
        filtered_teachers = []

        for t in available_teachers:

            if allow_two_duties:
                if daily_count[t][date] < 2:
                    filtered_teachers.append(t)
            else:
                if daily_count[t][date] < 1:
                    filtered_teachers.append(t)

        if len(filtered_teachers) < supervisors_required:
            raise Exception(
                f"Not enough available teachers for {date} - {session}"
            )

        # Sort by least duties
        filtered_teachers.sort(key=lambda x: duty_count[x])

        # Add randomness inside equal duty group
        min_duty = duty_count[filtered_teachers[0]]

        same_group = [
            t for t in filtered_teachers
            if duty_count[t] == min_duty
        ]

        random.shuffle(same_group)

        remaining = [
            t for t in filtered_teachers
            if duty_count[t] != min_duty
        ]

        final_pool = same_group + remaining

        selected = final_pool[:supervisors_required]

        for teacher in selected:

            master_rows.append({
                "Date": pd.to_datetime(date).strftime("%d-%m-%Y"),
                "Day": pd.to_datetime(date).day_name(),
                "Session": session,
                "Time": time,
                "Name of faculty": teacher,
                "Department": dept_map[teacher]
            })

            duty_count[teacher] += 1
            daily_count[teacher][date] += 1

    master_df = pd.DataFrame(master_rows)

    return master_df
