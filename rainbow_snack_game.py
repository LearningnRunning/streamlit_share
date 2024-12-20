import streamlit as st
import numpy as np
from PIL import Image
import extcolors
from scipy.spatial import KDTree
import io
from rembg import remove


def get_closest_rainbow_color(rgb):
    # 무지개 색상 정의 (RGB)
    rainbow_colors = {
        "빨간색": (255, 0, 0),
        "주황색": (255, 165, 0),
        "노란색": (255, 255, 0),
        "초록색": (0, 255, 0),
        "파랑색": (0, 0, 255),
        "남색색": (75, 0, 130),
        "보라색": (128, 0, 128),
    }

    # KDTree를 사용하여 가장 가까운 무지개 색 찾기
    colors_array = np.array(list(rainbow_colors.values()))
    tree = KDTree(colors_array)
    distance, index = tree.query(rgb)

    return list(rainbow_colors.keys())[index]


def process_image(input_image):
    try:
        # 배경 제거
        output_image = remove(input_image)
        return output_image
    except Exception as e:
        st.error(f"이미지 처리 중 오류가 발생했습니다: {str(e)}")
        return None


def main():
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
                    st.image(input_image, use_column_width=True)

                with col2:
                    st.subheader("배경 제거")
                    st.image(processed_image, use_column_width=True)

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
                        st.write(f"이 과자의 대표 색은 {closest_rainbow}입니다!")

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
