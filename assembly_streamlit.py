import streamlit as st
import pandas as pd
import json

# 데이터 파일 경로
json_file_path = "./data/national_assembply_index.json"
excel_file_path = "./data/national_assembly_list.xlsx"

# JSON 데이터 불러오기
with open(json_file_path, "r", encoding="utf-8") as json_file:
    absent_data = json.load(json_file)

lifting_martial_law_absent_index = absent_data["lifting_martial_law_absent_index"]
impeachment_absent_index = absent_data["impeachment_absent_index"]

# Excel 데이터 불러오기
election_results_df = pd.read_excel(excel_file_path, sheet_name='excel')

# 필터링: 번호로 데이터 추출
lifting_absentees = election_results_df[election_results_df['번호'].isin(lifting_martial_law_absent_index)]
impeachment_absentees = election_results_df[election_results_df['번호'].isin(impeachment_absent_index)]

# 탄핵소추안 및 비상계엄령 해제 요구안 데이터를 통합
lifting_absentees['불참유형'] = '비상계엄령 해제 요구안'
impeachment_absentees['불참유형'] = '탄핵소추안'

combined_absentees = pd.concat([lifting_absentees, impeachment_absentees])

# 중복 여부 구분 (두 안건 모두 불참한 경우)
combined_absentees['중복여부'] = combined_absentees.duplicated(subset=['의원명'], keep=False)

# 색상 구분
def assign_color(row):
    if row['중복여부']:
        return "#E61D2B"  # 두 안건 모두 불참: 진한 빨강
    elif row['불참유형'] == '탄핵소추안':
        return "#EE564A"  # 탄핵소추안만 불참: 연한 빨강
    elif row['불참유형'] == '비상계엄령 해제 요구안':
        return "#EDB19D"  # 비상계엄령 해제 요구안만 불참: 연한 살구색

combined_absentees['색상'] = combined_absentees.apply(assign_color, axis=1)

# 지역별로 첫 단어 추출
combined_absentees['지역그룹'] = combined_absentees['지역'].str.split(' ').str[0]

# 시각화 순서 정렬: 두 안건 모두 불참한 의원이 먼저 오도록
combined_absentees = combined_absentees.sort_values(by='중복여부', ascending=False)

# Streamlit 앱
st.title("국회의원 불참석 현황")
st.markdown(
    """
    ### 색상 설명
    - <span style="color:#E61D2B"> **비상계엄령 해제 요구안 + 탄핵소추안 불참**</span>: **#E61D2B (PANTONE 1795 C)**  
    - <span style="color:#EE564A"> **탄핵소추안 불참**</span>: **#EE564A (연한 빨강)**  
    - <span style="color:#EDB19D"> **비상계엄령 해제 요구안 불참**</span>: **#EDB19D (연한 살구색)**  
    """,
    unsafe_allow_html=True,
)

# 지역별로 데이터 그룹화
regions = combined_absentees['지역그룹'].unique()

# 지역별 데이터를 그리드로 표시
for region in regions:
    st.subheader(f"{region} 지역 의원")
    regional_data = combined_absentees[combined_absentees['지역그룹'] == region]

    def display_grid(data):
        cols = st.columns(3)  # 3열 그리드
        for i, row in data.iterrows():
            # 불참유형 표시 여부 결정
            additional_info = f"<em>{row['불참유형']}</em>" if not row['중복여부'] else ""
            st.markdown(
                f"""
                <div style="padding:10px; background-color:{row['색상']}; border-radius:5px; margin-bottom:10px; color:white;">
                    <strong>{row['의원명']}</strong><br>
                    {row['지역']}<br>
                    {additional_info}
                </div>
                """,
                unsafe_allow_html=True,
            )

    # 해당 지역의 데이터를 그리드 형식으로 표시
    display_grid(regional_data)
