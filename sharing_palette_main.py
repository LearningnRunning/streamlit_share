import streamlit as st
from os.path import join
import os
import glob
from PIL import Image
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def all_img_collecter(file_path):
    file_types = ['jpg', 'png', 'jpeg']
    files = sorted([file for file_type in file_types for file in glob.glob(join(file_path, f"*.{file_type}"))])
    return files       

# Function to load and display images in a grid
def display_images(selected_directory_path):
    # selected_directory_path = join(img_data, selected_directory)
    raw_imgs = all_img_collecter(img_data+"/raw_face")
    st.write("## Before 이미지")
    st.image(Image.open(raw_imgs[0]), width=300)
    images = all_img_collecter(selected_directory_path)
    # st.write(f"# {selected_directory}")
    images = sorted(images, key=natural_sort_key)
    if selected_directory == 'checco_ver_1_snap':
        st.write("\n\n")
        st.write("#### ※ 추가 결제시 받을 수 있는 팔레트입니다.")
    # Display images in a 2x2 grid
    for i in range(0, len(images), 2):
        row = images[i:i+2]
        col1, col2 = st.columns(2)  # Adjust this based on your layout needs

        with col1:
            if i < len(images):
                image_path = row[0]
                img_cap = int(image_path.split('/')[-1].split('.')[0]) 
                if selected_directory != 'checco_ver_1_snap':
                    st.write(f"### {img_cap} 번")
                st.image(Image.open(image_path), use_column_width=True)

        with col2:
            if i < len(images):
                image_path = row[1]
                img_cap = int(image_path.split('/')[-1].split('.')[0]) 
                if selected_directory != 'checco_ver_1_snap':
                    st.write(f"### {img_cap} 번")
                st.image(Image.open(image_path), use_column_width=True)

# Define the image directory
img_data = "./img_data"  # Replace with the actual path

# Streamlit app
st.title("Checco Palette Viewer")



# Radio button to choose image source
image_source = st.radio("원본을 고를지, 적용된 이미지(이효리)를 고를지 선택해주세요.", ["이효리", "model_8", "ai_model_D"])
img_data = join(img_data, image_source+"_result")
palette_lst = sorted(os.listdir(img_data))
# Selectbox to choose the image directory
selected_palette = st.selectbox("확인할 팔레트를 선택해주세요.", palette_lst)
selected_directory = join(img_data, selected_palette)

# dir_dict = {'MOONLIGHT': 'night_snap_retouched',
#             'graduation': 'graduation_snap',
#             'hanbok': 'hanbok_snap',
#             'japan_idol': 'japan_idol_snap',
#             'kimono': 'kimono_snap',
#             'graduation': 'graduation_snap',
#             'graduation': 'graduation_snap',
#             'TENNIS': 'tennis_snap_retouched',
#             'FOUR SEASONS': 'phase_1'}

# selected_directory = dir_dict.get(selected_palette)

# # Set image directory based on the selected source
# if image_source == "이효리":
#     img_data = join(img_data, 'model_8_result')
# elif image_source == "中条あやみ":
#     img_data = join(img_data, '中条あやみ_data')
# elif image_source == "checco Model 1":
#     img_data = join(img_data, 'checco_model_1_data')
# elif image_source == "checco Model 2":
#     img_data = join(img_data, 'ai_model_short_test_result')
# # elif image_source == "checco Model 3":
# #     img_data = join(img_data, 'ai_model_D_test_result')
# # Display images based on the selected directory



display_images(selected_directory)