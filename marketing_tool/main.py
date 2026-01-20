import sys

import streamlit as st

# Streamlit 서버 설정
if __name__ == "__main__":
    sys.argv = ["streamlit", "run", sys.argv[0], "--server.port=8001"]

# Main entry point - Streamlit will automatically detect pages in the pages/ directory
st.set_page_config(page_title="Multi-Tool App", layout="wide")

# ===== 메인 페이지 =====
st.title("🛠️ Multi-Tool App")
st.markdown("---")

st.markdown("""
### 👋 환영합니다!

이 애플리케이션은 여러 유용한 도구들을 제공하는 멀티 페이지 Streamlit 앱입니다.
왼쪽 사이드바에서 원하는 도구를 선택하거나 아래 페이지 목록을 확인하세요.
""")

st.markdown("---")

# 페이지 안내
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 📋 Instagram Follower Checker
    
    **기능:**
    - Instagram JSON 파일에서 팔로워 목록 추출
    - 입력한 팔로워 목록과 비교하여 팔로우 여부 확인
    
    **사용 방법:**
    1. Instagram에서 다운로드한 JSON 파일을 업로드합니다
    2. 확인하고 싶은 팔로워 목록을 입력합니다
       - 한 줄에 한 명씩 입력하거나
       - 공백이나 쉼표로 구분하여 입력할 수 있습니다
    3. "확인하기" 버튼을 클릭합니다
    4. 결과를 확인하고 필요한 경우 복사할 수 있습니다
    
    **결과:**
    - 각 팔로워의 팔로우 여부 (TRUE/FALSE)
    - 전체 팔로워 수, 팔로우 중인 수, 팔로우하지 않는 수 통계
    """)

with col2:
    st.markdown("""
    ### 📍 Address Validator
    
    **기능:**
    - 일본 우편번호의 유효성 검증
    - 유효한 주소의 상세 정보 조회 (도도부현, 시구, 정촌 등)
    
    **사용 방법:**
    1. 입력 방식을 선택합니다:
       - **단일 주소**: 하나의 우편번호만 검증
       - **여러 주소**: 여러 우편번호를 한 번에 검증
    2. 우편번호를 입력합니다
       - 하이픈(-) 등 숫자 외 문자는 자동으로 제거됩니다
       - 여러 주소의 경우 한 줄에 하나씩 또는 공백/쉼표로 구분
    3. "검증하기" 버튼을 클릭합니다
    4. 결과를 확인합니다
    
    **결과:**
    - 각 우편번호의 유효성 (TRUE/FALSE)
    - 유효한 경우: pref(도도부현), address, city, town, fullAddress 정보
    - 전체 주소 수, 유효한 주소 수, 유효하지 않은 주소 수 통계
    
    **참고:**
    - API 호출 시 자동으로 rate limiting이 적용됩니다
    - 여러 주소 검증 시 진행 상황이 표시됩니다
    """)

st.markdown("---")

st.info("💡 **팁**: 왼쪽 사이드바의 페이지 메뉴를 사용하여 각 도구로 이동할 수 있습니다.")
