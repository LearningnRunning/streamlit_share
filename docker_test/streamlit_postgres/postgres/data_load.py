import pandas as pd
from sqlalchemy import create_engine, text

# 데이터베이스 연결 설정
username = "a1_poke"
password = "a1_poke"
host = "localhost"  # 로컬에서 실행 시
port = 5432
dbname = "postgres"
DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{dbname}"


def load_data():
    # CSV 파일 로드
    try:
        df = pd.read_csv("data/naver_datalab_202503271540.csv")
        print("CSV 파일을 성공적으로 로드했습니다.")
    except Exception as e:
        print(f"CSV 파일 로드 중 오류가 발생했습니다: {e}")
        return

    # 컬럼명 변경
    df.rename(
        columns={
            "날짜": "date",
            "기간": "period",
            "1분류": "category",
            "연령/성별": "age_gender",
            "전일대비": "prev_day_change_rate",
            "전주대비": "prev_week_change_rate",
        },
        inplace=True,
    )

    # 전일대비 및 전주대비 기호 변환
    def convert_change_symbol(value):
        if value == "▲":
            return "+"
        elif value == "▼":
            return "-"
        else:
            return "0"

    # 전일대비, 전주대비 기호 변환
    if "전일대비" in df.columns:
        df["prev_day_change_rate"] = df["전일대비"].apply(convert_change_symbol)

    if "전주대비" in df.columns:
        df["prev_week_change_rate"] = df["전주대비"].apply(convert_change_symbol)

    # 필요한 컬럼만 선택
    required_columns = [
        "date",
        "category",
        "period",
        "age_gender",
        "rank",
        "keyword",
        "prev_day_change_rate",
        "prev_week_change_rate",
    ]

    # 컬럼이 존재하는지 확인
    for col in required_columns:
        if col not in df.columns:
            print(f"필요한 컬럼 {col}이(가) 데이터프레임에 없습니다.")

    # 존재하는 컬럼만 선택
    existing_columns = [col for col in required_columns if col in df.columns]
    df_filtered = df[existing_columns]

    # 데이터베이스에 저장
    try:
        engine = create_engine(DATABASE_URL)

        # 테이블 초기화 (선택 사항)
        with engine.connect() as conn:
            conn.execute(text("TRUNCATE TABLE naver_lab RESTART IDENTITY"))
            conn.commit()

        # 데이터 삽입
        df_filtered.to_sql("naver_lab", engine, if_exists="append", index=False)
        print(
            f"총 {len(df_filtered)}개의 레코드가 naver_lab 테이블에 성공적으로 삽입되었습니다."
        )
    except Exception as e:
        print(f"데이터베이스 저장 중 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    load_data()
