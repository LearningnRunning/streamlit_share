from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from kr_holidays import is_holiday, is_working_day
    KR_HOLIDAYS_AVAILABLE = True
except ImportError:
    KR_HOLIDAYS_AVAILABLE = False
    print("kr_holidays 라이브러리를 사용할 수 없습니다. 기본 날짜 계산을 사용합니다.")

# -------------------------------
# 1️⃣ 데이터 로드
# -------------------------------
# 사용자가 제공한 월별 대진표 (팀 조합 다양성 최적화 - 중복 조합 0회)
schedule = {
    '2026-01': {
        'A구장': [10, 2, 7],
        'B구장': [3, 6, 8],
        'C구장': [4, 5, 9],
        '휴식': 1
    },
    '2026-02': {
        'A구장': [4, 10, 1],
        'B구장': [9, 7, 5],
        'C구장': [3, 8, 2],
        '휴식': 6
    },
    '2026-03': {
        'A구장': [7, 8, 1],
        'B구장': [4, 2, 6],
        'C구장': [3, 10, 5],
        '휴식': 9
    },
    '2026-04': {
        'A구장': [7, 3, 4],
        'B구장': [6, 2, 10],
        'C구장': [5, 9, 1],
        '휴식': 8
    },
    '2026-05': {
        'A구장': [2, 6, 1],
        'B구장': [5, 8, 10],
        'C구장': [9, 4, 7],
        '휴식': 3
    },
    '2026-06': {
        'A구장': [6, 5, 9],
        'B구장': [1, 10, 7],
        'C구장': [4, 3, 8],
        '휴식': 2
    },
    '2026-07': {
        'A구장': [3, 7, 5],
        'B구장': [2, 9, 1],
        'C구장': [8, 6, 4],
        '휴식': 10
    },
    '2026-08': {
        'A구장': [6, 2, 8],
        'B구장': [4, 10, 9],
        'C구장': [1, 5, 7],
        '휴식': 3
    },
    '2026-09': {
        'A구장': [5, 2, 4],
        'B구장': [3, 1, 7],
        'C구장': [10, 6, 8],
        '휴식': 9
    },
    '2026-10': {
        'A구장': [4, 8, 9],
        'B구장': [10, 7, 6],
        'C구장': [3, 1, 2],
        '휴식': 5
    },
    '2026-11': {
        'A구장': [10, 9, 3],
        'B구장': [5, 8, 1],
        'C구장': [6, 2, 7],
        '휴식': 4
    },
    '2026-12': {
        'A구장': [8, 1, 10],
        'B구장': [5, 4, 3],
        'C구장': [6, 2, 9],
        '휴식': 7
    }
}



# 구장 매핑 (A구장=1구장, B구장=2구장, C구장=3구장)
def field_map(field_char):
    return {'A구장': 1, 'B구장': 2, 'C구장': 3}[field_char]

# 팀 이름 매핑
TEAM_NAMES = {
    1: '포항OB',
    2: '동부',
    3: '장량',
    4: '오천',
    5: '포유',
    6: '유강',
    7: '백호',
    8: '육사(64)',
    9: '흑룡',
    10: '청호'
}

# 팀 이름으로 번호 찾기 (역매핑)
TEAM_NUMBERS = {name: num for num, name in TEAM_NAMES.items()}

def get_team_name(team_num):
    """팀 번호를 팀 이름으로 변환"""
    return TEAM_NAMES.get(team_num, f'팀 {team_num}')

# 월 키 변환 함수 (2026-01 -> 1월)
def month_key_to_display(month_key):
    month_num = int(month_key.split('-')[1])
    return f"{month_num}월"

# 쉬는 팀 정보 추출
rest_teams = {}
for month_key, month_data in schedule.items():
    display_month = month_key_to_display(month_key)
    rest_teams[display_month] = month_data.get('휴식')

# schedule을 data 리스트로 변환
# 각 구장의 팀 리스트에서 3개씩 조합하여 경기 생성
data = []
for month_key, month_data in sorted(schedule.items()):
    month_str = month_key_to_display(month_key)
    
    for field_key in ['A구장', 'B구장', 'C구장']:
        field_num = field_map(field_key)
        teams = month_data.get(field_key, [])
        
        # 각 구장의 3개 팀을 3개 경기로 조합
        # 예: [1, 2, 3] -> (1, 2), (2, 3), (3, 1)
        for i in range(len(teams)):
            team1 = teams[i]
            team2 = teams[(i + 1) % len(teams)]
            data.append((month_str, field_num, team1, team2))

# 실제 날짜 계산 (매월 2번째 주 토요일)
def get_match_date(year, month_str):
    """매월 2번째 주 토요일 찾기"""
    month_map = {"1월": 1, "2월": 2, "3월": 3, "4월": 4, "5월": 5, "6월": 6,
                 "7월": 7, "8월": 8, "9월": 9, "10월": 10, "11월": 11, "12월": 12}
    month = month_map.get(month_str, 1)
    
    # 해당 월의 첫날
    first_day = datetime(year, month, 1)
    
    # 첫날이 토요일인지 확인
    if first_day.weekday() == 5:  # 토요일
        first_saturday = first_day
    else:
        # 다음 토요일까지의 일수 계산
        days_to_saturday = (5 - first_day.weekday()) % 7
        if days_to_saturday == 0:
            days_to_saturday = 7  # 이번 주 토요일이면 다음 주로
        first_saturday = first_day + timedelta(days=days_to_saturday)
    
    # 2번째 주 토요일 (첫번째 토요일에서 +7일)
    second_saturday = first_saturday + timedelta(days=7)
    
    return second_saturday.strftime("%Y-%m-%d")

def get_weekday(date_str):
    """요일 반환"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    return weekdays[date_obj.weekday()]

# 경기 순서 번호만 추가 (시간은 표시하지 않음)
data_with_date = []
month_match_counts = {"1월": 0, "2월": 0, "3월": 0, "4월": 0, "5월": 0, "6월": 0,
                      "7월": 0, "8월": 0, "9월": 0, "10월": 0, "11월": 0, "12월": 0}

for month, field, team1, team2 in data:
    match_idx = month_match_counts[month]
    
    # 실제 날짜 계산 (매월 2번째 주 토요일)
    match_date = get_match_date(2026, month)
    match_weekday = get_weekday(match_date)
    
    # 경기 순서 (1부터 시작)
    match_order = match_idx + 1
    
    data_with_date.append((month, field, team1, team2, match_date, match_weekday, match_order))
    month_match_counts[month] += 1

df = pd.DataFrame(data_with_date, columns=["월", "구장", "팀1", "팀2", "날짜", "요일", "순서"])

# -------------------------------
# 2️⃣ 페이지 구성 및 스타일
# -------------------------------
st.set_page_config(
    page_title="⚽ 포항 축구 대진표",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# 포항 축구 구장 대진표\n### 2026 시즌 전체 일정 관리 시스템\n모든 팀이 공정하게 경기를 치를 수 있도록 구성되었습니다."
    }
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2e7d32 0%, #4caf50 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .match-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
        border-left: 4px solid #1976d2;
    }
    .stat-box {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
    }
    .team-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.2rem;
    }
    .rest-banner {
        background: #ff6b6b;
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 1.3rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .field-card {
        background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
    }
    .field-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e7d32;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .team-group {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 1rem 0;
        flex-wrap: wrap;
    }
    .team-circle {
        background: rgba(255,255,255,0.95);
        color: #2e7d32;
        min-width: 60px;
        padding: 0.5rem 0.8rem;
        height: auto;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 0.9rem;
        border: 2px solid rgba(255,255,255,0.8);
        white-space: nowrap;
    }
    .metric-card {
        background: linear-gradient(135deg, #4caf50 0%, #66bb6a 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div class="main-header">
    <h1>⚽ 포항 축구 구장 대진표</h1>
    <p style="font-size: 1.1rem; margin: 0.5rem 0 0 0;">2026 시즌 전체 일정 관리 시스템</p>
    <p style="font-size: 0.9rem; opacity: 0.9; margin: 0.5rem 0 0 0;">🏆 모두를 위한 공정한 대진표</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------
# 2.5️⃣ 통계 데이터 계산
# -------------------------------
# 팀별 구장 사용 통계 계산
team_field_stats = {}
for team in range(1, 11):
    team_field_stats[team] = {'A구장': 0, 'B구장': 0, 'C구장': 0, '휴식': 0, '총경기수': 0}
    
for month_key, month_data in schedule.items():
    # 쉬는 팀 체크
    rest_team = month_data.get('휴식')
    if rest_team:
        team_field_stats[rest_team]['휴식'] += 1
    
    # 각 구장의 팀들 체크
    for field_key in ['A구장', 'B구장', 'C구장']:
        teams = month_data.get(field_key, [])
        for team in teams:
            team_field_stats[team][field_key] += 1
            team_field_stats[team]['총경기수'] += 1

# 통계 데이터프레임 생성
stats_data = []
for team in range(1, 11):
    stats_data.append({
        '팀': get_team_name(team),
        'A구장': team_field_stats[team]['A구장'],
        'B구장': team_field_stats[team]['B구장'],
        'C구장': team_field_stats[team]['C구장'],
        '휴식': team_field_stats[team]['휴식'],
        '총경기수': team_field_stats[team]['총경기수']
    })
stats_df = pd.DataFrame(stats_data)

# -------------------------------
# 3️⃣ 필터 영역 (탭)
# -------------------------------
tab1, tab2, tab3 = st.tabs(["🏟️ 이번 주 구장 현황", "📊 팀별 경기 현황", "📈 구장 이용 통계"])

# -------------------------------
# 4️⃣ 탭 1: 이번 주 구장 현황
# -------------------------------
with tab1:
    # 월 선택
    month_options = sorted(df["월"].unique(), key=lambda x: int(x.replace("월", "")))
    selected_month = st.selectbox("📅 월 선택", options=month_options, index=0)
    st.markdown("---")
    
    # 선택한 월의 데이터만 사용
    month_df = df[df["월"] == selected_month].copy() if selected_month else df.copy()
    
    # 쉬는 팀 배너
    if selected_month in rest_teams and rest_teams[selected_month]:
        rest_team = rest_teams[selected_month]
        rest_team_name = get_team_name(rest_team)
        st.markdown(f"""
        <div class="rest-banner">
            ⏸️ 이번 주 쉬는 팀: <strong>{rest_team_name}</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # 날짜 정보
    if len(month_df) > 0:
        match_date = month_df.iloc[0]["날짜"]
        match_weekday = month_df.iloc[0]["요일"]
        st.markdown(f"### 📅 {selected_month} {match_date} ({match_weekday})")
    
    # 구장별 팀 그룹 구성 표시
    # A, B, C 구장을 각각 카드로 표시
    cols = st.columns(3)
    
    # 구장명 매핑
    field_names = {1: 'A', 2: 'B', 3: 'C'}
    
    for field_num in [1, 2, 3]:
        field_df = month_df[month_df["구장"] == field_num]
        field_name = field_names[field_num]
        col_idx = field_num - 1
        
        with cols[col_idx]:
            # 해당 구장의 팀 목록 추출 (중복 제거)
            teams_in_field = set()
            for _, row in field_df.iterrows():
                teams_in_field.add(int(row["팀1"]))
                teams_in_field.add(int(row["팀2"]))
            teams_sorted = sorted(teams_in_field)
            
            # 구장명을 카드 바깥 상단에 헤더로 표시
            st.markdown(f"""
            <div class="field-header">
                🏟️ {field_name}구장
            </div>
            """, unsafe_allow_html=True)
            
            # 구장 카드 표시 (팀 정보만)
            team_html = ''.join([f'<div class="team-circle" title="{get_team_name(t)}">{get_team_name(t)}</div>' for t in teams_sorted])
            st.markdown(f"""
            <div class="field-card">
                <div class="team-group">
                    {team_html}
                </div>
            </div>
            """, unsafe_allow_html=True)
            


# -------------------------------
# 5️⃣ 탭 2: 팀별 현황 (테이블 형태)
# -------------------------------
with tab2:
    st.subheader("👥 팀별 경기 현황")
    
    # 팀 선택 (팀 이름으로 표시)
    team_numbers = sorted(set(df["팀1"]).union(df["팀2"]))
    team_options = [get_team_name(team) for team in team_numbers]
    selected_team_name = st.selectbox("👤 팀 선택", options=team_options)
    selected_team = TEAM_NUMBERS.get(selected_team_name)
    
    if selected_team:
        # 팀별 일정 생성
        team_schedule = []
        for month_key in sorted(schedule.keys()):
            month_display = month_key_to_display(month_key)
            month_data = schedule[month_key]
            
            # 쉬는 팀 체크
            if month_data.get('휴식') == selected_team:
                team_schedule.append({
                    '월': month_display,
                    '날짜': get_match_date(2026, month_display),
                    '요일': get_weekday(get_match_date(2026, month_display)),
                    '구장': '-',
                    '함께하는 팀들': '-',
                    '상태': '휴식'
                })
            else:
                # 어느 구장에 속하는지 찾기
                for field_key in ['A구장', 'B구장', 'C구장']:
                    teams = month_data.get(field_key, [])
                    if selected_team in teams:
                        field_num = field_map(field_key)
                        field_name = {1: 'A', 2: 'B', 3: 'C'}[field_num]
                        # 함께하는 팀들 (자기 자신 제외)
                        other_teams = [t for t in teams if t != selected_team]
                        team_schedule.append({
                            '월': month_display,
                            '날짜': get_match_date(2026, month_display),
                            '요일': get_weekday(get_match_date(2026, month_display)),
                            '구장': f'{field_name}구장 ({field_num}구장)',
                            '함께하는 팀들': ', '.join([get_team_name(t) for t in other_teams]),
                            '상태': '경기'
                        })
                        break  # 한 달에는 하나의 구장에만 속함
        
        if team_schedule:
            # 테이블로 표시
            schedule_df = pd.DataFrame(team_schedule)
            
            # 휴식인 행은 별도 스타일 적용
            st.markdown(f"### 📅 {selected_team_name} 전체 일정 (2026 시즌)")
            st.markdown(f"총 {len(team_schedule)}개월 중 경기 {len([s for s in team_schedule if s['상태'] == '경기'])}개월, 휴식 {len([s for s in team_schedule if s['상태'] == '휴식'])}개월")
            
            # 날짜와 요일을 함께 표시
            schedule_df['날짜정보'] = schedule_df['날짜'] + ' (' + schedule_df['요일'] + ')'
            
            # 표시할 컬럼만 선택
            display_df = schedule_df[['월', '날짜정보', '구장', '함께하는 팀들', '상태']].copy()
            display_df.columns = ['월', '날짜', '구장', '함께하는 팀들', '상태']
            
            # 휴식인 행 강조를 위한 스타일 적용
            def highlight_rest(row):
                if row['상태'] == '휴식':
                    return ['background-color: #ffebee'] * len(row)
                return [''] * len(row)
            
            styled_df = display_df.style.apply(highlight_rest, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"❌ {selected_team_name}의 경기 데이터가 없습니다.")

# -------------------------------
# 6️⃣ 탭 3: 공정성 통계
# -------------------------------
with tab3:
    st.header("📈 구장 이용 통계 분석")
    
    # 요약 통계 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_matches = stats_df['총경기수'].mean()
        st.metric(
            label="평균 경기 수",
            value=f"{avg_matches:.1f}경기"
        )
    
    with col2:
        min_matches = stats_df['총경기수'].min()
        max_matches = stats_df['총경기수'].max()
        st.metric(
            label="경기 수 범위",
            value=f"{min_matches}-{max_matches}경기",
            delta=f"{max_matches - min_matches}차이"
        )
    
    with col3:
        balanced_teams = 0
        for idx, row in stats_df.iterrows():
            counts = [row['A구장'], row['B구장'], row['C구장']]
            if max(counts) - min(counts) <= 1:
                balanced_teams += 1
        st.metric(
            label="구장 균형 팀",
            value=f"{balanced_teams}/10"
        )
    
    with col4:
        avg_rest = stats_df['휴식'].mean()
        st.metric(
            label="평균 휴식 횟수",
            value=f"{avg_rest:.1f}회"
        )
    
    st.markdown("---")
    
    # 경기 수 공정성 분석
    st.subheader("✅ 경기 수 공정성")
    st.write("각 팀이 균등하게 경기를 치루는지 확인합니다.")
    
    # 경기 횟수가 적은 팀 찾기 (평균보다 현저히 낮은 팀)
    below_avg_teams = stats_df[stats_df['총경기수'] < avg_matches - 1]
    if len(below_avg_teams) > 0:
        st.warning("""
        ⚠️ **주의**: 다음 팀들의 경기 횟수가 평균보다 낮습니다: {}
        """.format(', '.join(below_avg_teams['팀'].tolist())))
    
    # 각 팀의 색상을 다르게 설정
    colors = ['#f44336' if row['총경기수'] < avg_matches - 0.5 else '#4caf50' for _, row in stats_df.iterrows()]
    
    fig_matches = px.bar(
        stats_df, 
        x='팀', 
        y='총경기수',
        title='팀별 총 경기 횟수',
        color=stats_df['총경기수'],
        color_continuous_scale='Greens'
    )
    fig_matches.update_traces(marker_line_width=0, marker_color=colors)
    
    # 평균선 추가
    fig_matches.add_hline(
        y=avg_matches, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"평균: {avg_matches:.1f}경기"
    )
    
    # 가장 낮은 팀 강조
    min_teams = stats_df[stats_df['총경기수'] == stats_df['총경기수'].min()]['팀'].tolist()
    for team in min_teams:
        team_idx = stats_df[stats_df['팀'] == team].index[0]
        fig_matches.add_shape(
            type="rect",
            xref="x",
            yref="paper",
            x0=team_idx-0.4,
            x1=team_idx+0.4,
            y0=0,
            y1=1,
            fillcolor="rgba(244, 67, 54, 0.2)",
            line=dict(color="red", width=2, dash="dot")
        )
    
    fig_matches.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_matches, use_container_width=True)
    
    # 경기 횟수가 적은 팀 상세 정보
    if len(below_avg_teams) > 0:
        st.markdown("### 📉 경기 횟수가 적은 팀 상세")
        detail_col1, detail_col2 = st.columns([2, 1])
        with detail_col1:
            for _, row in below_avg_teams.iterrows():
                diff = avg_matches - row['총경기수']
                st.markdown(f"""
                **{row['팀']}**: {row['총경기수']}경기 (평균보다 {diff:.1f}경기 적음)
                - A구장: {row['A구장']}회, B구장: {row['B구장']}회, C구장: {row['C구장']}회
                - 휴식: {row['휴식']}회
                """)
        
        with detail_col2:
            st.markdown("""
            💡 **개선 방안**:
            - 해당 팀들이 다른 팀들보다 경기를 더 많이 치르도록 대진표 조정 필요
            """)
    
    st.info("""
    💡 **공정성 분석**: 전체 팀의 평균 경기 수는 {:.1f}경기이며, 
    경기 횟수 차이는 최대 {}경기입니다.
    """.format(avg_matches, max_matches - min_matches))
    
    st.markdown("---")
    
    # 구장 사용 공정성 분석
    st.subheader("✅ 구장별 사용 공정성")
    st.write("각 팀이 A구장, B구장, C구장을 균등하게 사용하는지 확인합니다.")
    
    # 팀별 구장 사용 상세 테이블
    def highlight_balanced(row):
        """구장별 사용이 균형잡힌 팀 강조"""
        field_counts = [row['A구장'], row['B구장'], row['C구장']]
        if max(field_counts) - min(field_counts) <= 1:
            return ['background-color: #e8f5e9', 'background-color: #e8f5e9', 
                   'background-color: #e8f5e9', 'background-color: #e8f5e9', 'background-color: #e8f5e9', 'background-color: #c8e6c9']
        return [''] * 6
    
    styled_stats_df = stats_df.style.apply(highlight_balanced, axis=1)
    st.dataframe(styled_stats_df, use_container_width=True, hide_index=True)
    
    
# -------------------------------
# 7️⃣ 푸터
# -------------------------------
st.markdown("""
---
<div style="text-align: center; color: #666; padding: 2rem;">
    <p style="font-size: 1rem; margin-bottom: 0.5rem;">⚽ 2026 포항 축구 구장 대진표</p>
    <p style="font-size: 0.8rem; opacity: 0.7;">데이터 기반 일정 관리 시스템 | 모든 팀을 위한 공정한 대진표</p>
    <p style="font-size: 0.7rem; opacity: 0.5; margin-top: 1rem;">🏆 Fair Play, Fair Game</p>
</div>
""", unsafe_allow_html=True)
