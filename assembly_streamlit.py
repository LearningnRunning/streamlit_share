import streamlit as st
import pandas as pd
import json

# 페이지 설정 및 로고 표시
st.set_page_config(page_title="불참의힘", page_icon="./data/image/stop_icon.png")

st.logo("./data/image/stop_icon.png")

# @st.cache_data 적용: JSON 데이터 불러오기
@st.cache_data
def load_json_data():
    with open("./data/national_assembply_index.json", "r", encoding="utf-8") as json_file:
        return json.load(json_file)

# @st.cache_data 적용: Excel 데이터 불러오기
@st.cache_data
def load_excel_data():
    return pd.read_excel("./data/national_assembly_list.xlsx", sheet_name='excel')

# 데이터 로드
absent_data = load_json_data()
election_results_df = load_excel_data()

# 필터링: 번호로 데이터 추출
lifting_martial_law_absent_index = absent_data["lifting_martial_law_absent_index"]
impeachment_absent_index = absent_data["impeachment_absent_index"]

lifting_absentees = election_results_df[election_results_df['번호'].isin(lifting_martial_law_absent_index)]
impeachment_absentees = election_results_df[election_results_df['번호'].isin(impeachment_absent_index)]

# 불참 유형 추가
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

# 비례대표 처리: 비례대표만 남기기
combined_absentees['비례대표여부'] = combined_absentees['지역'].str.contains('비례대표')

# 지역 순서 지정
region_order = ["서울", "인천", "경기", "충북", "충남", "강원", "경북", "대구", "울산", "경남", "부산", "비례대표"]
combined_absentees['지역순서'] = combined_absentees['지역그룹'].apply(
    lambda x: region_order.index(x) if x in region_order else len(region_order)
)

# 시각화 순서 정렬
combined_absentees = combined_absentees.sort_values(by=['지역순서', '중복여부', '의원명'], ascending=[True, False, True])
combined_absentees.drop_duplicates(subset=['번호'], inplace=True)

# Streamlit 앱
st.title("불참의힘, 바로 잡아 내겠습니다.")

st.markdown(
    """
    - <span style="color:#E61D2B"> **비상계엄령 해제 요구안 + 탄핵소추안 불참**</span>
    - <span style="color:#EE564A"> **탄핵소추안 불참**</span>
    - <span style="color:#EDB19D"> **비상계엄령 해제 요구안 불참**</span>
    """,
    unsafe_allow_html=True,
)

# 검색 필터링
search_term = st.text_input("궁금한 의원명 또는 지역구명을 입력해 보세요").strip()

if search_term:
    combined_absentees = combined_absentees[
        combined_absentees['의원명'].str.contains(search_term, case=False, na=False) |
        combined_absentees['지역'].str.contains(search_term, case=False, na=False)
    ]

# 지역별 데이터를 3열로 표시
regions = combined_absentees['지역그룹'].unique()

for region in region_order:
    regional_data = combined_absentees[combined_absentees['지역그룹'] == region]

    if region == "비례대표":
        regional_data = regional_data[regional_data['비례대표여부']]  # 비례대표만 표시

    if not regional_data.empty:
        st.subheader(f"{region} 지역 의원")
        regional_data = regional_data.sort_values(by='의원명')  # 지역구 내 정렬

        # 데이터를 3열로 나누어 표시
        cols = st.columns(3)
        for idx, row in enumerate(regional_data.itertuples()):
            col = cols[idx % 3]  # 3열로 순환
            with col:
                additional_info = f"<em>{row.불참유형}</em>" if not row.중복여부 else ""
                st.markdown(
                    f"""
                    <div style="padding:10px; background-color:{row.색상}; border-radius:5px; margin-bottom:10px; color:white;">
                        <strong>{row.의원명}</strong><br>
                        {row.지역}<br>
                        {additional_info}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
