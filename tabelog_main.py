import pandas as pd
import plotly.express as px
import streamlit as st


# 데이터 로드
@st.cache_data
def load_data():
    df = pd.read_csv(
        "./tabelog_demo/ranked_diner_okinawa_df.csv"
    )  # 경로는 실제 데이터 위치에 맞게 조정해주세요
    return df


def main():
    st.title("🍽️ 일본 맛집 탐색기")

    # 데이터 로드
    df = load_data()

    # 사이드바 생성
    st.sidebar.header("필터 옵션")

    # 도시 다중 선택
    cities = sorted(df["city_name"].unique().tolist())
    selected_cities = st.sidebar.multiselect(
        "도시 선택",
        options=cities,
        default=cities,  # 기본값으로 처음 3개 도시 선택
    )

    # 가격대 선택 (일반 가격)
    price_min = int(df["price_min"].min())
    price_max = int(df["price_max"].max())

    price_range = st.sidebar.slider(
        "가격 범위 (¥)",
        min_value=price_min,
        max_value=price_max,
        value=(price_min, price_max),
    )

    # 리뷰 기반 가격대 선택
    review_price_min = int(df["review_price_min"].min())
    review_price_max = int(df["review_price_max"].max())

    review_price_range = st.sidebar.slider(
        "리뷰 기반 가격 범위 (¥)",
        min_value=review_price_min,
        max_value=review_price_max,
        value=(review_price_min, review_price_max),
    )

    # 데이터 필터링
    filtered_df = df[
        (df["city_name"].isin(selected_cities))
        & (df["price_min"] >= price_range[0])
        & (df["price_max"] <= price_range[1])
        & (df["review_price_min"] >= review_price_range[0])
        & (df["review_price_max"] <= review_price_range[1])
    ]

    # 결과 표시
    st.subheader(f"선택된 레스토랑 수: {len(filtered_df)}")

    # 도시별 레스토랑 분포 시각화
    fig_city = px.bar(
        filtered_df["city_name"].value_counts().reset_index(),
        x="city_name",
        y="count",
        title="도시별 레스토랑 분포",
    )
    st.plotly_chart(fig_city)

    # 카테고리별 레스토랑 분포
    fig_category = px.pie(
        filtered_df["category"].value_counts().reset_index(),
        values="count",
        names="category",
        title="카테고리별 레스토랑 분포",
    )
    st.plotly_chart(fig_category)
    # 모든 카테고리를 하나의 리스트로 펼치고 중복 제거
    unique_categories = (
        filtered_df["category"]
        .dropna()  # NaN 제거
        .str.split("、")  # '、' 기준으로 분리
        .explode()  # 리스트 풀기
        .str.strip()  # 공백 제거
        .unique()  # 중복 제거
        .tolist()  # 리스트로 변환
    )

    selected_categories = st.sidebar.multiselect(
        "카테고리 선택",
        options=unique_categories,
        default=unique_categories,  # 기본값으로 처음 3개 도시 선택
    )
    mask = filtered_df["category"].str.contains("|".join(selected_categories), na=False)
    filtered_df = filtered_df[mask]

    # 레스토랑 목록 표시
    st.subheader("레스토랑 목록")
    st.dataframe(
        filtered_df[
            [
                "rank",
                "name",
                "tabelog_url",
                "category",
                "hours",
                "price_range",
                "review_based_price_range",
                "phone",
                "parking",
                "seating_capacity",
                "max_guests",
                "private_rooms",
                "charter",
                "smoking_policy",
                "facilities",
                "course_menu",
                "drinks",
                "facebook_url",
                "instagram_url",
                "twitter_url",
            ]
        ],
        hide_index=True,
        column_config={
            "rank": st.column_config.NumberColumn(format="%.0f"),
            "name": st.column_config.TextColumn(),
            "category": st.column_config.TextColumn(),
            "phone": st.column_config.TextColumn(),
            "tabelog_url": st.column_config.LinkColumn(),
            "facebook_url": st.column_config.LinkColumn(),
            "instagram_url": st.column_config.LinkColumn(),
            "twitter_url": st.column_config.LinkColumn(),
        },
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
