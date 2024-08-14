import streamlit as st
from gensim.models import Word2Vec
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

def extract_country(filename):
    match = re.search(r'_(japan|korea|american|china)_', filename, re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    return 'Unknown'
    
@st.cache_data
def load_csv(file_list):
  
    file_dict = {extract_country(os.path.basename(file)): pd.read_csv(file) for file in file_list}
    return file_dict

@st.cache_data
def load_word2vec(model_file_path_list):
    file_dict = {extract_country(os.path.basename(file)): Word2Vec.load(file) for file in model_file_path_list}
    return file_dict

@st.cache_data
def load_excel(file_path):
    return pd.read_excel(file_path, sheet_name=None)

excel_path = os.path.join(STATIC_DATA_PATH, 'country_keyword_frequency.xlsx')
sheets = load_excel(excel_path)

csv_file_list = glob(os.path.join(NOW_PATH, STATIC_DATA_PATH, 'only_sentences', '*.csv'))
df_dict = load_csv(csv_file_list)


model_files = glob(os.path.join(STATIC_DATA_PATH, 'word2vec', '*word2vec_model'))
vec_model_dict = load_word2vec(model_files)
    
st.sidebar.title('메뉴 선택')
app_mode = st.sidebar.radio('모드를 선택하세요:', ['국가별 Keyword 빈도수', 'Keyword가 포함된 문장 찾기', 'Keyword 연관 단어 찾기'])

if app_mode == '국가별 Keyword 빈도수':
    st.title('국가별 Keyword 빈도수')
    sheet_names = ['북미', '일본', '중국', '한국']
    selected_sheet = st.selectbox('국가를 선택하세요:', sheet_names)
    word_cloud_image_path = os.path.join(STATIC_DATA_PATH, 'wordclouds', f'{selected_sheet}.png')
    if selected_sheet in sheets:
        st.image(word_cloud_image_path)
        df = sheets[selected_sheet]
        st.write(f'{selected_sheet} 키워드 빈도수:')
        st.dataframe(df)
    else:
        st.write(f'{selected_sheet} 시트를 찾을 수 없습니다.')
        
elif app_mode == 'Keyword가 포함된 문장 찾기':
    st.title('Keyword가 포함된 문장 찾기')

    selected_file_name = st.selectbox('국가를 선택하세요:', list(df_dict.keys()))
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

    selected_file_name = st.selectbox('국가를 선택하세요:', list(vec_model_dict.keys()))
    if selected_file_name:
        vec_model = vec_model_dict[selected_file_name]


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

