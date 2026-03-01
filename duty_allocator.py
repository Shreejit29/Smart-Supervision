import pandas as pd
from collections import defaultdict


def allocate_single_block(
    teacher_df,
    block,
    total_duty_count,
    daily_duty_count,
    allow_two_duties,
    priority_list
):
    """
    Allocates teachers for ONE allocation block
    while maintaining global duty balance.
    """

    assigned = []

    date = block["Date"]
    session = block["Session"]
    time = block["Time"]
    supervisors_required = block["Supervisors"]
    avoid_list = block["Avoid"]

    dept_map = dict(zip(teacher_df["Name of faculty"], teacher_df["Department"]))

    all_teachers = teacher_df["Name of faculty"].tolist()

    # Remove avoid teachers
    eligible = [t for t in all_teachers if t not in avoid_list]

    # Daily limit filtering
    filtered = []
    for teacher in eligible:
        if allow_two_duties:
            if daily_duty_count[teacher][date] < 2:
                filtered.append(teacher)
        else:
            if daily_duty_count[teacher][date] < 1:
                filtered.append(teacher)

    # Sort by total duty count (ascending)
    filtered.sort(key=lambda x: total_duty_count[x])

    # Move priority teachers to front (but still sorted among themselves)
    priority = [t for t in filtered if t in priority_list]
    normal = [t for t in filtered if t not in priority_list]

    priority.sort(key=lambda x: total_duty_count[x])
    filtered = priority + normal

    dept_assigned = defaultdict(int)

    # Department counts
    dept_total = (
        teacher_df.groupby("Department")["Name of faculty"]
        .count()
        .to_dict()
    )

    # First pass: Keep one teacher free per department
    for teacher in filtered:

        if len(assigned) >= supervisors_required:
            break

        dept = dept_map[teacher]

        if dept_assigned[dept] < dept_total[dept] - 1:
            assigned.append(teacher)
            dept_assigned[dept] += 1
            total_duty_count[teacher] += 1
            daily_duty_count[teacher][date] += 1

    # Second pass: Relax department rule if needed
    if len(assigned) < supervisors_required:
        for teacher in filtered:

            if len(assigned) >= supervisors_required:
                break

            if teacher not in assigned:
                assigned.append(teacher)
                total_duty_count[teacher] += 1
                daily_duty_count[teacher][date] += 1

    if len(assigned) < supervisors_required:
        raise ValueError(
            f"Not enough supervisors available for {date} - {session}"
        )

    rows = []
    for teacher in assigned:
        rows.append({
            "Date": pd.to_datetime(date).strftime("%d-%m-%Y"),
            "Day": pd.to_datetime(date).day_name(),
            "Session": session,
            "Time": time,
            "Name of faculty": teacher,
            "Department": dept_map[teacher]
        })

    return rows


def generate_master_supervision_global(
    teacher_df,
    allocation_blocks,
    allow_two_duties=False,
    priority_list=None
):
    """
    allocation_blocks:
    [
        {
            "Date": date,
            "Session": session,
            "Time": time,
            "Supervisors": int,
            "Avoid": [...]
        },
        ...
    ]
    """

    if priority_list is None:
        priority_list = []

    total_duty_count = defaultdict(int)
    daily_duty_count = defaultdict(lambda: defaultdict(int))

    master_rows = []

    for block in allocation_blocks:

        block_rows = allocate_single_block(
            teacher_df,
            block,
            total_duty_count,
            daily_duty_count,
            allow_two_duties,
            priority_list
        )

        master_rows.extend(block_rows)

    master_df = pd.DataFrame(master_rows)

    return master_df
