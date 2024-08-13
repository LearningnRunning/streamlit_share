import streamlit as st
from gensim.models import Word2Vec
import pandas as pd
from glob import glob
import os
import re

NOW_PATH = os.getcwd()
STATIC_DATA_PATH = './data'
STATIC_PATH = './data/modulab_phase_2'

def find_rows(df, find_key):
    result_df = df[df['SeparatedSentences'].str.contains(find_key, case=False, na=False)]
    if not result_df.empty:
        return result_df
    else:
        return pd.DataFrame()

@st.cache_data
def load_csv(file_list):
    def extract_country(filename):
        match = re.search(r'_(japan|korea|american|china)_', filename, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()
        return 'Unknown'
    
    file_dict = {extract_country(os.path.basename(file)): pd.read_csv(file) for file in file_list}
    return file_dict

@st.cache_data
def load_word2vec(model_file_path):
    model = Word2Vec.load(model_file_path)
    return model

st.sidebar.title('메뉴 선택')
app_mode = st.sidebar.radio('모드를 선택하세요:', ['Keyword가 포함된 문장 찾기', 'Keyword 연관 단어 찾기'])

if app_mode == 'Keyword가 포함된 문장 찾기':
    st.title('Keyword가 포함된 문장 찾기')

    file_list = glob(os.path.join(NOW_PATH, STATIC_DATA_PATH, '*.csv'))
    df_dict = load_csv(file_list)

    selected_file_name = st.selectbox('CSV 파일을 선택하세요:', list(df_dict.keys()))
    if selected_file_name:
        selected_df = df_dict[selected_file_name]

        search_term = st.text_input('검색어를 입력하세요:')

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

elif app_mode == 'Keyword 연관 단어 찾기':
    st.title('Keyword 연관 단어 찾기')

    china_word2vec_model_file_path = os.path.join(STATIC_DATA_PATH, 'china', 'intern_china_word2vec_model')
    vec_model = load_word2vec(china_word2vec_model_file_path)

    key_word = st.text_input('키워드를 입력하세요:')
    top_num = st.slider(label='연관 단어 수', min_value=1, max_value=100, value=5)

    if st.button('연관 단어 찾기'):
        if key_word:
            try:
                relevant_keywords = vec_model.wv.most_similar(key_word, topn=top_num)
                st.write('연관 단어:')
                for word, similarity in relevant_keywords:
                    st.write(f"{word}: {similarity:.4f}")
            except KeyError:
                st.write('입력한 키워드가 모델에 없습니다. 다른 키워드를 시도해보세요.')
        else:
            st.write('키워드를 입력해주세요.')