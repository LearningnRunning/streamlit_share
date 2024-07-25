import streamlit as st
import pandas as pd
from glob import glob
import os
import re


        
NOW_PATH = os.getcwd()
STATIC_DATA_PATH = './data'

def find_rows(df, find_key):
    result_df = df[df['SeparatedSentences'].str.contains(find_key, case=False, na=False)]
    if not result_df.empty:
        return result_df
    else:
        return pd.DataFrame()

# 선택된 파일 불러오기
@st.cache_data
def load_data(file_list):
    # 파일 이름에서 국가명을 추출하는 함수
    def extract_country(filename):
        # 정규표현식을 사용하여 국가명 추출
        match = re.search(r'_(japan|korea|american|china)_', filename, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()
        return 'Unknown'  # 국가명을 찾지 못한 경우

    # 파일 이름과 경로를 매칭하는 딕셔너리 생성
    file_dict = {extract_country(os.path.basename(file)): pd.read_csv(file) for file in file_list}
    return file_dict

# Streamlit 앱 시작
st.title('CSV 파일 검색 앱')

file_list = glob(os.path.join(NOW_PATH, STATIC_DATA_PATH, '*.csv'))


df_dict = load_data(file_list)

# 파일 선택 위젯 (파일 이름만 표시)
selected_file_name = st.selectbox('CSV 파일을 선택하세요:', list(df_dict.keys()))
if selected_file_name:
    # 선택된 파일의 전체 경로 가져오기
    selected_df = df_dict[selected_file_name]


    # st.dataframe(df.head())

    # 검색어 입력
    search_term = st.text_input('검색어를 입력하세요:')

    # 검색 버튼
    if st.button('검색'):
        if search_term:
            result = find_rows(selected_df, search_term)
            if not result.empty:
                st.write('검색 결과:')
                st.data_editor(result, use_container_width=True)
            else:
                st.write('검색 결과가 없습니다.')
        else:
            st.write('검색어를 입력해주세요.')