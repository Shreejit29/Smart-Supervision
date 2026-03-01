import pandas as pd
from collections import defaultdict
import random


def generate_master_supervision(
    teacher_df,
    schedule_list,
    supervisors_required,
    avoid_list=None,
    priority_list=None,
    allow_two_duties=False,
):
    """
    teacher_df: DataFrame with columns:
        - 'Name of faculty'
        - 'Department'

    schedule_list: List of dictionaries:
        [
            {
                "Date": "01-04-2026",
                "Day": "Monday",
                "Session": "FN",
                "Time": "10:00 AM - 1:00 PM"
            },
            ...
        ]

    supervisors_required: int
    avoid_list: list of teacher names to avoid
    priority_list: list of teacher names to prioritize
    allow_two_duties: bool
    """

    if avoid_list is None:
        avoid_list = []

    if priority_list is None:
        priority_list = []

    # Clean teacher list
    teacher_df = teacher_df.copy()
    teacher_df = teacher_df[~teacher_df["Name of faculty"].isin(avoid_list)]

    teachers = teacher_df["Name of faculty"].tolist()

    # Department mapping
    dept_map = dict(zip(teacher_df["Name of faculty"], teacher_df["Department"]))

    # Track total duty count
    total_duty_count = defaultdict(int)

    # Track daily duty count
    daily_duty_count = defaultdict(lambda: defaultdict(int))

    master_rows = []

    for session in schedule_list:

        date = session["Date"]
        day = session["Day"]
        session_name = session["Session"]
        time = session["Time"]

        # Eligible teachers based on daily rule
        eligible_teachers = []

        for teacher in teachers:

            if allow_two_duties:
                if daily_duty_count[teacher][date] < 2:
                    eligible_teachers.append(teacher)
            else:
                if daily_duty_count[teacher][date] < 1:
                    eligible_teachers.append(teacher)

        # Sort by total duties (approx equal distribution)
        eligible_teachers.sort(key=lambda x: total_duty_count[x])

        # Move priority teachers to front
        priority_teachers = [t for t in eligible_teachers if t in priority_list]
        normal_teachers = [t for t in eligible_teachers if t not in priority_list]

        eligible_teachers = priority_teachers + normal_teachers

        assigned = []
        dept_assigned = defaultdict(int)

        # First Pass: Try keeping 1 per dept free
        for teacher in eligible_teachers:

            if len(assigned) >= supervisors_required:
                break

            dept = dept_map[teacher]

            # Count teachers in this dept
            total_in_dept = teacher_df[teacher_df["Department"] == dept].shape[0]

            # Ensure 1 teacher remains free
            if dept_assigned[dept] < total_in_dept - 1:
                assigned.append(teacher)
                dept_assigned[dept] += 1
                total_duty_count[teacher] += 1
                daily_duty_count[teacher][date] += 1

        # Second Pass: Relax department rule if needed (Option A)
        if len(assigned) < supervisors_required:

            for teacher in eligible_teachers:

                if len(assigned) >= supervisors_required:
                    break

                if teacher not in assigned:
                    assigned.append(teacher)
                    total_duty_count[teacher] += 1
                    daily_duty_count[teacher][date] += 1

        # Final safety check
        if len(assigned) < supervisors_required:
            raise ValueError(
                f"Not enough supervisors available for {date} {session_name}"
            )

        # Add to master rows
        for teacher in assigned:
            master_rows.append(
                {
                    "Date": date,
                    "Day": day,
                    "Session": session_name,
                    "Time": time,
                    "Name of faculty": teacher,
                    "Department": dept_map[teacher],
                }
            )

    master_df = pd.DataFrame(master_rows)

    return master_df
