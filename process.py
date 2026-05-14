import pandas as pd
import re

def data_source(upload_file):

    if upload_file is None:
        return None

    df = pd.read_excel(upload_file)

    list_columns = df.columns.tolist()
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
        return None

    return df

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