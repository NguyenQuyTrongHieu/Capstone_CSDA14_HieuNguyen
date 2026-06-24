import pandas as pd
import re

def data_source(upload_file):

    if upload_file is None:
        return None

    df = pd.read_excel(upload_file)
    #list_columns = df.columns.tolist()
    kiem_tra_cot = [
        "CaseID",
        "Project Name",
        "Date Created",
        "Mapping Team",
        "Date Updated",
        "Description"
    ]
    # Kiểm tra cột
    missing_columns = [col for col in kiem_tra_cot if col not in df.columns]

    # Thiếu cột
    if missing_columns:
        return None, missing_columns

    return df, None

# EXTRACT OPEN/CLOSE TIME

def extract_case_time(df):

    # OPEN TIME
    df["Open Time"] = df["Description"].str.extract(r'opened at\s*(.*)',flags=re.IGNORECASE)

    # CLOSE TIME
    df["Close Time"] = df["Description"].str.extract(r'closed at\s*(.*)',flags=re.IGNORECASE)

    # CONVERT DATETIME
    df["Open Time"] = pd.to_datetime(df["Open Time"],errors="coerce")

    df["Close Time"] = pd.to_datetime(df["Close Time"],errors="coerce")

    return df

# CASE FINAL

def build_case_table(df):
    df = df.sort_values("Date Created")
    case_df = df.groupby("CaseID").agg({"Mapping Team": "first","Open Time": "max","Close Time": "max"}).reset_index()

    return case_df 

# COMPLETED CASE

def completed_case(case_df):

    completed_df = case_df[case_df["Open Time"].notna() & case_df["Close Time"].notna()].copy()

    # 24H/D
    real_hours = (completed_df["Close Time"] - completed_df["Open Time"]).dt.total_seconds() / 3600

    # 8H/D
    completed_df["Working Hours"] = (real_hours / 24) * 8

    completed_df["Working Hours"] = (completed_df["Working Hours"].round(2))

    completed_df["Filter Date"] = (completed_df["Open Time"])
    return completed_df

# OPEN CASE (CHƯA CLOSE)

def open_case(case_df):

    open_df = case_df[case_df["Open Time"].notna() & case_df["Close Time"].isna()].copy()

    # PENDING HOURS
    pending_hours = (pd.Timestamp.now() - open_df["Open Time"]).dt.total_seconds() / 3600

    # CONVERT 8H/DAY
    open_df["Pending Hours"] = (pending_hours / 24) * 8

    open_df["Pending Hours"] = (open_df["Pending Hours"].round(2))

    open_df["Filter Date"] = (open_df["Open Time"])
    return open_df

# INVALID CASE

def invalid_case(case_df):

    invalid_df = case_df[case_df["Open Time"].isna() & case_df["Close Time"].notna()].copy()
    invalid_df["Filter Date"] = (invalid_df["Close Time"])
    return invalid_df

# MAIN 

def process_data(df):

    # EXTRACT TIME
    df = extract_case_time(df)

    # CASE FINAL
    case_df = build_case_table(df)

    # SPLIT DATA
    completed_df = completed_case(case_df)

    open_df = open_case(case_df)

    invalid_df = invalid_case(case_df)

    return completed_df, open_df, invalid_df

KPI = {
    "Junior": [
        {
            "Name": "Productivity (Quantity of work) - standart: 100case (each quarter)",
            "Detail": """
- Level 1: Unable to reach target
- Level 2: Reach 50% of average target no. of closed cases
- Level 3: Reach 100% of average target no. of closed cases
- Level 4: Reach 120% of average target no. of closed cases
- Level 5: Reach 150% of average target no. of closed cases
"""
        },
        {
            "Name": "Quanlity of work Defect Map Tracking",
            "Detail": """
- Level 1: >= 50% mapping build have any issues level
- Level 2: < 50% mapping build have issue and <= 5 critical level issue
- Level 3: <= 25% mapping build have issue, no critical level
- Level 4: <= 10% mapping have only Low-level issues
- Level 5: There are not any issues on all maps
"""
        },
        {
            "Name": "TOEIC scores",
            "Detail": """
- Level 1: > 350
- Level 2: 350 < and <= 450
- Level 3: 450 < and <= 550
- Level 4: 550 < and <= 650
- Level 5: > 650
"""
        },
        {
            "Name": "Full report tasks and status on Netsuite Timecard Entry",
            "Detail": """
- Level 1: > 12
- Level 2: 9-12 times missing to submit the information
- Level 3: 6-8 times missing to submit the information
- Level 4: 1-5 times missing to submit the information
- Level 5: fully and promptly submitting information
"""
        }
    ],
    "Senior": [
        {
            "Name": "Productivity (Quantity of work) - standart: 130case (each quarter)",
            "Detail": """
- Level 1: Unable to reach target
- Level 2: Reach 50% of average target no. of closed cases
- Level 3: Reach 100% of average target no. of closed cases
- Level 4: Reach 120% of average target no. of closed cases
- Level 5: Reach 150% of average target no. of closed cases
"""
        },
        {
            "Name": "Quanlity of work Defect Map Tracking",
            "Detail": """
- Level 1: >= 50% mapping build have any issues level
- Level 2: < 50% mapping build have issue and <= 5 critical level issue
- Level 3: <= 25% mapping build have issue, no critical level
- Level 4: <= 10% mapping have only Low-level issues
- Level 5: There are not any issues on all maps
"""
        },
        {
            "Name": "TOEIC scores",
            "Detail": """
- Level 1: > 400
- Level 2: 400 < and <= 500
- Level 3: 500 < and <= 600
- Level 4: 600 < and <= 700
- Level 5: > 700
"""
        },
        {
            "Name": "Full report tasks and status on Netsuite Timecard Entry",
            "Detail": """
- Level 1: > 10
- Level 2: 7-10 times missing to submit the information
- Level 3: 4-7 times missing to submit the information
- Level 4: 1-4 times missing to submit the information
- Level 5: fully and promptly submitting information
"""
        }
    ],
    "Leader": [
        {
            "Name": "On-time delivery (deadline adherence)",
            "Detail": """
- Level 1: > 150 cases
- Level 2: > 120 cases
- Level 3: > 90 cases
- Level 4: > 50 cases
- Level 5: > 20 cases
"""
        },
        {
            "Name": "Quanlity of work Defect Map Tracking (all members)",
            "Detail": """
- Level 1: >= 50% mapping build have any issues level
- Level 2: < 50% mapping build have issue and <= 5 critical level issue
- Level 3: <= 25% mapping build have issue, no critical level
- Level 4: <= 10% mapping have only Low-level issues
- Level 5: There are not any issues on all maps
"""
        },
        {
            "Name": "Process and Improvement",
            "Detail": """
- Level 1: 50% of members achieved their individual KPIs
- Level 2: 60% of members achieved their individual KPIs
- Level 3: 70% of members achieved their individual KPIs
- Level 4: 80% of members achieved their individual KPIs
- Level 5: >= 90% of members achieved their individual KPIs
"""
        },
        {
            "Name": "survey based on members",
            "Detail": """
- Scores are awarded based on member and manager evaluations of team stability
"""
        }
    ]
}

def rank (score):
    if score == 5:
        return "Xuất sắc"
    elif score >= 4:
        return "Tốt"
    elif score >= 3:
        return "Khá"
    elif score >= 2:
        return "Trung bình"
    else:
        return "Cần xem xét"