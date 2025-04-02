-- naver_lab 테이블 생성
CREATE TABLE IF NOT EXISTS naver_lab (
    id SERIAL PRIMARY KEY,
    date DATE,
    category VARCHAR(100),
    period VARCHAR(100),
    age_gender VARCHAR(50),
    rank INTEGER,
    keyword VARCHAR(200),
    prev_day_change_rate VARCHAR(50),
    prev_week_change_rate VARCHAR(50)
);