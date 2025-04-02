import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# 데이터베이스 연결 설정
username = "a1_poke"
password = "a1_poke"
host = "postgres"  # docker-compose 서비스 이름
port = 5432
dbname = "postgres"
DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"

# 제목 설정
st.title("네이버 데이터랩 분석 대시보드")


# 데이터베이스 연결
@st.cache_resource
def get_db_connection():
    return create_engine(DATABASE_URL)


engine = get_db_connection()


# 카테고리 목록 가져오기
@st.cache_data
def get_categories():
    with engine.connect() as conn:
        query = "SELECT DISTINCT category FROM naver_lab ORDER BY category"
        result = conn.execute(text(query))
        categories = [row[0] for row in result]
    return categories


# 연령/성별 목록 가져오기
@st.cache_data
def get_age_genders():
    with engine.connect() as conn:
        query = "SELECT DISTINCT age_gender FROM naver_lab ORDER BY age_gender"
        result = conn.execute(text(query))
        age_genders = [row[0] for row in result]
    return age_genders


# 필터 설정
st.sidebar.header("필터")
categories = get_categories()
selected_category = st.sidebar.selectbox("카테고리 선택", ["전체"] + categories)

age_genders = get_age_genders()
selected_age_gender = st.sidebar.selectbox("연령/성별 선택", ["전체"] + age_genders)

# 날짜 범위 설정
try:
    with engine.connect() as conn:
        query = "SELECT MIN(date), MAX(date) FROM naver_lab"
        result = conn.execute(text(query))
        min_date, max_date = result.fetchone()

    date_range = st.sidebar.date_input(
        "날짜 범위",
        value=(pd.to_datetime(min_date), pd.to_datetime(max_date)),
        min_value=pd.to_datetime(min_date),
        max_value=pd.to_datetime(max_date),
    )
except Exception as e:
    st.error(f"날짜 정보를 가져오는 중 오류가 발생했습니다: {e}")
    date_range = (None, None)


# 데이터 쿼리 함수
@st.cache_data
def get_data(category, age_gender, start_date, end_date):
    query = "SELECT * FROM naver_lab WHERE 1=1"

    params = {}
    if category != "전체":
        query += " AND category = :category"
        params["category"] = category

    if age_gender != "전체":
        query += " AND age_gender = :age_gender"
        params["age_gender"] = age_gender

    if start_date and end_date:
        query += " AND date BETWEEN :start_date AND :end_date"
        params["start_date"] = start_date
        params["end_date"] = end_date

    query += " ORDER BY date, rank"

    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn, params=params)
    return df


# 데이터 로드 및 표시
if date_range[0] and date_range[1]:
    try:
        data = get_data(
            selected_category,
            selected_age_gender,
            date_range[0].strftime("%Y-%m-%d"),
            date_range[1].strftime("%Y-%m-%d"),
        )

        st.write(f"## 검색 결과: {len(data)}개의 데이터")
        st.dataframe(data)

        # 상위 키워드 표시
        if not data.empty:
            st.write("## 인기 키워드 (순위별)")
            top_keywords = data.groupby("keyword")["rank"].mean().sort_values().head(10)
            st.bar_chart(top_keywords)

            # 일별 변화 추이
            st.write("## 일별 키워드 변화 추이")
            pivot_df = pd.pivot_table(
                data, index="date", columns="keyword", values="rank", aggfunc="mean"
            ).fillna(0)
            st.line_chart(pivot_df)
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
else:
    st.info("날짜 범위를 선택해주세요.")
