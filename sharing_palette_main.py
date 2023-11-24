import streamlit as st
from os.path import join
import os
import glob
from PIL import Image

def all_img_collecter(file_path):
    file_types = ['jpg', 'png', 'jpeg']
    files = sorted([file for file_type in file_types for file in glob.glob(join(file_path, f"*.{file_type}"))])
    return files       

# Function to load and display images in a grid
def display_images(directory):
    images = all_img_collecter(directory)
    
    images = sorted(images)
    # Display images in a 2x2 grid
    for i in range(0, len(images), 2):
        row = images[i:i+2]
        col1, col2 = st.columns(2)  # Adjust this based on your layout needs

        with col1:
            if i < len(images):
                image_path = row[0]
                img_cap = image_path.split('/')[-1].split('.')[0]
                st.image(Image.open(image_path),caption=f"image_{img_cap}", use_column_width=True)

        with col2:
            if i + 1 < len(images):
                image_path = row[1]
                img_cap = image_path.split('/')[-1].split('.')[0]
                st.image(Image.open(image_path),caption=f"image_{img_cap}", use_column_width=True)

# Define the image directory
img_data = "./img_data"  # Replace with the actual path

# Streamlit app
st.title("Checco Palette Viewer")

# Selectbox to choose the image directory
selected_directory = st.selectbox("확인할 팔레트를 선택해주세요.", ["checco_ver_1_snap", "night_snap", "christmas_snap", "tennis_snap"])

# Radio button to choose image source
image_source = st.radio("원본을 고를지, 적용된 이미지(이효리)를 고를지 선택해주세요.", ["checco_model", "이효리", "中条あやみ"])

# Set image directory based on the selected source
if image_source == "이효리":
    img_data = join(img_data, 'hyori_data')
elif image_source == "中条あやみ":
    img_data = join(img_data, '中条あやみ_data')
elif image_source == "checco_model":
    img_data = join(img_data, 'checco_model_data')
    
# Display images based on the selected directory
selected_directory_path = join(img_data, selected_directory)
st.write(f"# {selected_directory}")
display_images(selected_directory_path)

