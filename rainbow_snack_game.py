import streamlit as st
import numpy as np
from PIL import Image
import extcolors
from scipy.spatial import KDTree
import io
from rembg import remove


def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    else:
        h = (60 * ((r - g) / df) + 240) % 360
    s = 0 if mx == 0 else (df / mx) * 100
    v = mx * 100
    return h, s, v


def get_closest_rainbow_color(rgb):
    # 무지개 색상 정의
    rainbow_colors = {
        "빨간색": [
            (255, 0, 0),
            (180, 0, 0),
            (255, 192, 203),
            (249, 218, 223),
            (254, 138, 137),
            (255, 35, 0),
            (208, 6, 0),
            (114, 47, 56),
            (255, 10, 0),
            (218, 5, 44),
            (151, 2, 25),
            (126, 2, 1),
        ],
        "주황색": [
            (255, 165, 0),
            (255, 140, 0),
            (228, 61, 5),
            (229, 84, 7),
            (240, 111, 11),
            (240, 111, 11),
        ],
        "노란색": [
            (255, 255, 0),
            (142, 122, 35),
            (247, 228, 0),
            (247, 247, 153),
            (246, 247, 1),
            (246, 247, 1),
        ],
        "초록색": [
            (0, 255, 0),
            (0, 180, 0),
            (143, 192, 3),
            (42, 140, 68),
            (42, 140, 68),
            (42, 140, 68),
            (42, 140, 68),
        ],
        "파란색": [
            (0, 0, 255),
            (0, 0, 180),
            (167, 198, 247),
            (141, 180, 247),
            (118, 165, 248),
            (97, 154, 247),
            (63, 132, 246),
            (14, 2, 238),
            (1, 168, 232),
            (57, 61, 237),
        ],
        "남색": [
            (75, 0, 130),
            (60, 0, 110),
            (19, 32, 88),
            (20, 33, 87),
            (36, 64, 127),
            (54, 95, 161),
            (115, 145, 186),
            (12, 49, 81),
        ],
        "보라색": [
            (128, 0, 128),
            (100, 0, 100),
            (41, 15, 87),
            (158, 145, 197),
            (143, 72, 173),
            (187, 125, 192),
            (103, 7, 142),
            (123, 115, 161),
        ],
    }

    input_h, input_s, input_v = rgb_to_hsv(*rgb)
    min_diff = float("inf")
    closest_color = None

    for color_name, color_list in rainbow_colors.items():
        for color in color_list:
            h, s, v = rgb_to_hsv(*color)
            # HSV 공간에서의 거리 계산 (색상에 가중치 부여)
            h_diff = min(abs(h - input_h), 360 - abs(h - input_h))
            s_diff = abs(s - input_s)
            v_diff = abs(v - input_v)

            # 색상(H)에 더 큰 가중치 부여
            total_diff = (h_diff * 2) + (s_diff * 0.5) + (v_diff * 0.3)

            if total_diff < min_diff:
                min_diff = total_diff
                closest_color = color_name

    return closest_color


def resize_image(image, target_size=512):
    # PIL Image로 변환
    if isinstance(image, bytes):
        img = Image.open(io.BytesIO(image))
    else:
        img = Image.fromarray(image)

    # 현재 크기
    width, height = img.size

    # 리사이징 비율 계산
    ratio = min(target_size / width, target_size / height)
    new_size = (int(width * ratio), int(height * ratio))

    # 리사이징
    resized_img = img.resize(new_size, Image.Resampling.LANCZOS)

    return resized_img


def process_image(input_image):
    try:
        # 이미지 리사이징
        resized_image = resize_image(input_image)

        # 리사이즈된 이미지를 bytes로 변환
        img_byte_arr = io.BytesIO()
        resized_image.save(
            img_byte_arr, format=resized_image.format if resized_image.format else "PNG"
        )
        img_byte_arr = img_byte_arr.getvalue()

        # 배경 제거
        output_image = remove(img_byte_arr)
        return output_image
    except Exception as e:
        st.error(f"이미지 처리 중 오류가 발생했습니다: {str(e)}")
        return None


st.set_page_config(
    page_title="무지개판결기🌈", page_icon="./data/rainbow_icon_125.png", layout="wide"
)


def main():
    st.image(Image.open("./data/rainbow_icon.png"))
    st.title("무지개 과자 게임🌈🍪🧀🍫🍭")

    # 파일 업로더 추가
    uploaded_file = st.file_uploader("과자 사진을 업로드해주세요", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            # 이미지 데이터 가져오기
            image_bytes = uploaded_file.getvalue()

            # 원본 이미지 표시를 위한 PIL Image 객체 생성
            input_image = Image.open(io.BytesIO(image_bytes))

            # 진행 상태 표시
            with st.spinner("과자 분석 중..."):
                # 배경 제거 처리
                processed_image = process_image(image_bytes)

            if processed_image is not None:
                # 원본 이미지와 처리된 이미지를 나란히 표시
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("원본 이미지")
                    st.image(input_image, use_container_with=True)

                with col2:
                    st.subheader("배경 제거")
                    st.image(processed_image, use_container_with=True)

                # 색상 추출
                try:
                    # PIL Image로 변환
                    if isinstance(processed_image, bytes):
                        processed_pil = Image.open(io.BytesIO(processed_image))
                    else:
                        processed_pil = Image.fromarray(processed_image)

                    colors = extcolors.extract_from_image(processed_pil)

                    if colors[0]:  # 색상이 추출되었다면
                        # Top 5 색상 표시
                        st.subheader("검출된 Top 5 색상")

                        # 색상을 가로로 배열하기 위한 컬럼 생성
                        cols = st.columns(5)

                        # 상위 5개 색상 처리
                        for idx, (color, count) in enumerate(colors[0][:5]):
                            percentage = count / sum(c[1] for c in colors[0]) * 100
                            with cols[idx]:
                                # 색상 박스 표시
                                st.markdown(
                                    f"""
                                    <div style="width: 50px; height: 50px; 
                                    background-color: rgb{color}; 
                                    border: 1px solid black;
                                    margin: 0 auto;"></div>
                                    <div style="text-align: center; font-size: 12px; 
                                    margin-top: 5px;">{percentage:.1f}%</div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                        # 가장 많은 비율을 차지하는 색상 찾기
                        dominant_color = colors[0][0][0]
                        closest_rainbow = get_closest_rainbow_color(dominant_color)

                        # 결과 표시
                        st.markdown("---")
                        st.subheader("최종 분석 결과 ✨")
                        st.write(f"이 과자의 대표 색은 **{closest_rainbow}**에 가깝습니다!")

                        # 대표 색상 미리보기
                        st.markdown(
                            f"""
                            <div style="width: 100px; height: 50px; 
                            background-color: rgb{dominant_color}; 
                            border: 1px solid black; 
                            margin-top: 10px;"></div>
                            """,
                            unsafe_allow_html=True,
                        )

                except Exception as e:
                    st.error(f"색상 분석 중 오류가 발생했습니다: {str(e)}")

        except Exception as e:
            st.error(f"이미지 로딩 중 오류가 발생했습니다: {str(e)}")


if __name__ == "__main__":
    main()
