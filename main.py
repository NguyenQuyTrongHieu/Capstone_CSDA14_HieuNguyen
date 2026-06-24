import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime,date
from process import *

st.set_page_config(page_title = 'Case Information', layout= 'wide')

st.title('Task Performance Dashboard', text_alignment='center')

# file_name = 'Case Update Information.xlsx'

with st.sidebar:

    upload_file = st.file_uploader("Upload Excel File",type=["xlsx"])

    if upload_file:
        df, missing_columns = data_source(upload_file)
        if missing_columns:
            st.error(f'thiếu cột: {missing_columns}')
            st.stop()
        else:
            st.success("File upload successfully")


if upload_file is None:
    st.sidebar.warning("Please upload file")
    st.stop()
if df is None:
    st.info("File chưa được upload")
    st.stop()

Trang_chu = st.sidebar.radio('', ['Trang chủ','Active Member'])

if Trang_chu == 'Trang chủ':
    start_date = st.date_input("From Date",min_value=date(2025,1,1),max_value=datetime.today())
    end_date = st.date_input("To Date",min_value=date(2025,1,1),max_value=datetime.today())
    df_date = df[(df["Date Created"].dt.date >= start_date) & (df["Date Created"].dt.date <= end_date)]

    df_date = df_date.drop_duplicates(subset=["CaseID",'Mapping Team'])
    st.metric("Tổng case", len(df_date),border = True)  
    
    cols = st.columns(5)
    member_case = (df_date.groupby("Mapping Team")["CaseID"].count())
    for i, (member, total_case) in enumerate(member_case.items()):
        cols[i % 5].metric(member,total_case,border=True)

    st.subheader("Team Case Compare")

    # GROUP DATA
    team_chart = (df_date.groupby("Mapping Team")["CaseID"].nunique().sort_values(ascending=False))

    fig, ax = plt.subplots(figsize=(10,5))

    # BAR CHART
    ax.bar(team_chart.index,team_chart.values)

    ax.set_title("Cases By Member")

    ax.set_xlabel("Member")

    ax.set_ylabel("Total Cases")

    plt.xticks(rotation=15)

    st.pyplot(fig)
    
elif Trang_chu == 'Active Member':
    df_Data_Member = pd.read_excel(upload_file,sheet_name= 'Member Data')
    member_list = df['Mapping Team'].unique().tolist()

    selected_member = st.sidebar.selectbox("Select Member",options=member_list,
        index=None,placeholder="Type member name...")   

    if selected_member:
        info = df_Data_Member[df_Data_Member["Tên"] == selected_member].iloc[0]
        
        st.sidebar.write(f'Title: {info['Title']}')
        st.sidebar.write(f'Shift: {info['Shift']}')
        st.sidebar.write(f'Level: {info['Level']}')

        member_df = df[df["Mapping Team"] == selected_member]
        start_date = st.date_input("From Date",min_value=date(2025,1,1),max_value=datetime.today())
        end_date = st.date_input("To Date",min_value=date(2025,1,1),max_value=datetime.today())
        # df_date_member = member_df[(member_df["Date Created"].dt.date >= start_date) & (member_df["Date Created"].dt.date <= end_date)]

        completed_df, open_df, invalid_df = process_data(member_df)
        completed_df = completed_df[(completed_df["Filter Date"].dt.date >= start_date) & ( completed_df["Filter Date"].dt.date <= end_date)]
        open_df = open_df[(open_df["Filter Date"].dt.date >= start_date) &(open_df["Filter Date"].dt.date <= end_date)]
        invalid_df = invalid_df[(invalid_df["Filter Date"].dt.date >= start_date) & (invalid_df["Filter Date"].dt.date <= end_date)]
        Full_Case = member_df[(member_df["Date Created"].dt.date >= start_date) & (member_df["Date Created"].dt.date <= end_date)]
        st.title(selected_member)

        member_final = pd.concat([completed_df,open_df,invalid_df])
        tab1, tab2, tab3 = st.tabs(["Overview","KPI","Raw Data"])
        
        with tab1:
            # KPI
            col1, col2, col3 = st.columns(3)

            col1.metric("Completed Cases",len(completed_df))

            col2.metric("Opening Cases",len(open_df))

            col3.metric("Invalid Cases",len(invalid_df))

            # AVG HOURS

            avg_hours = round(completed_df["Working Hours"].mean(),2)

            st.metric("Average Working Hours",avg_hours)

            # LONGEST CASES

            st.subheader("Top Longest Cases")

            top_cases = completed_df.sort_values("Working Hours",ascending=False).head(10)

            st.dataframe(top_cases)

            # OPEN CASES
    
            st.subheader("Opening Cases")

            st.dataframe(open_df.sort_values("Pending Hours",ascending=False))

            # DAILY CASE TREND
            st.subheader("Daily Case Trend")

            daily_case = (member_final.groupby(member_final["Filter Date"].dt.date)["CaseID"].count())

            st.line_chart(daily_case)

        with tab2:
            col1, col2, col3 = st.columns(3)

            col1.metric("Completed Cases",len(completed_df))

            col2.metric("Opening Cases",len(open_df))

            col3.metric("Invalid Cases",len(invalid_df))
            # FROM KPI
            level = info['Level']
            kpi_level = KPI.get(level,[])
            with st.form("KPI_Form"):
                score = {}
                for idx, kpi in enumerate(kpi_level, start = 1):
                    st.subheader(f"KPI {idx}: {kpi["Name"]}")
                    with st.popover("Xem chi tiết"):
                        st.write(kpi["Detail"])
                    score[kpi["Name"]] = st.number_input("Level", min_value=0, max_value=5,step=1,key=f"kpi_{idx}")
                submit = st.form_submit_button("Submit")
            
            if submit:
                df_kpis = pd.DataFrame({"KPI": list(score.keys()),"Điểm": list(score.values()) })
                total_score = df_kpis["Điểm"].sum()
                avg_score = total_score / len(df_kpis)

                xep_loai = rank(avg_score)

                st.success("Đánh giá hoàn tất")

                st.dataframe(df_kpis, use_container_width= True)

                col4, col5, col6 = st.columns(3)
                col4.metric("Tổng điểm", round(total_score, 2))
                col5.metric("Điểm Trung Bình", round(avg_score, 2))
                col6.metric("Xếp loại", xep_loai)

                chart_df = df_kpis.set_index("KPI")

                st.bar_chart(chart_df["Điểm"])

        with tab3:
            # RAW DATA

            st.subheader("Full Cases")

            st.dataframe(Full_Case)

            st.subheader("Opening Cases")

            st.dataframe(open_df)

            st.subheader("Invalid Cases")

            st.dataframe(invalid_df)
