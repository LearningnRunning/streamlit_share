import json
from typing import List, Tuple

import pandas as pd
import streamlit as st


# ===== Helper functions =====
def extract_follower_usernames_from_json(json_data: list) -> List[str]:
    """인스타 JSON에서 팔로워 사용자명 리스트 추출."""
    usernames: List[str] = []
    for item in json_data:
        if not isinstance(item, dict):
            continue
        string_list_data = item.get("string_list_data")
        if isinstance(string_list_data, list) and len(string_list_data) > 0:
            first = string_list_data[0]
            if isinstance(first, dict):
                username = first.get("value")
                if isinstance(username, str) and username.strip():
                    usernames.append(username.strip())
    return usernames


def load_followers_from_json_file(uploaded_file) -> Tuple[List[str], str | None]:
    """업로드된 파일에서 팔로워 리스트를 로드하고 검증.

    Returns: (followers, error_message)
    """
    try:
        json_data = json.load(uploaded_file)
    except Exception as exc:  # noqa: BLE001
        return [], f"JSON 파싱 오류: {exc}"

    if not isinstance(json_data, list):
        return [], "알 수 없는 JSON 형식입니다. 리스트 형태여야 합니다."

    followers = extract_follower_usernames_from_json(json_data)
    if not followers:
        return [], "유효한 팔로워 데이터를 찾지 못했습니다. 파일 형식을 확인해주세요."

    return followers, None


def parse_input_followers(input_text: str) -> List[str]:
    """텍스트 입력에서 팔로워 후보를 파싱하고 중복 제거(입력 순서 유지)."""
    tokens = [token.strip() for token in input_text.replace(",", "\n").split()]
    seen: set[str] = set()
    unique_tokens: List[str] = []
    for token in tokens:
        if token and token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    return unique_tokens


def build_result_dataframe(
    input_followers: List[str], follower_list: List[str]
) -> pd.DataFrame:
    """입력 팔로워 대비 실제 팔로우 여부 데이터프레임 생성."""
    status_values = [
        "TRUE" if follower in set(follower_list) else "FALSE"
        for follower in input_followers
    ]
    return pd.DataFrame(
        {
            "Follower": input_followers,
            "Qoo10 インスタを followしている（更新日：）": status_values,
        }
    )


# ===== UI =====
st.set_page_config(page_title="Instagram Follower Checker", layout="wide")
st.title("Instagram Follower Checker")

# JSON 파일 업로더
uploaded_file = st.file_uploader("JSON 파일을 업로드하세요", type=["json"])

if uploaded_file is None:
    st.warning("JSON 파일을 먼저 업로드해주세요.")
else:
    follower_list, error_message = load_followers_from_json_file(uploaded_file)
    if error_message:
        st.error(error_message)
    else:
        st.write(f"### 입력해주신 파일에서 팔로우수: {len(follower_list)}")

        # 텍스트 입력 영역
        input_text = st.text_area(
            "팔로워 목록을 입력하세요 (여러 줄)",
            height=200,
            help="한 줄에 한 명씩 또는 공백/쉼표로 구분하여 입력하세요.",
        )

        if st.button("확인하기"):
            if not input_text.strip():
                st.warning("팔로워 이름을 입력해주세요.")
            else:
                input_followers = parse_input_followers(input_text)
                if not input_followers:
                    st.warning("유효한 팔로워 이름을 찾지 못했습니다.")
                else:
                    # 결과 생성 및 표시
                    df = build_result_dataframe(input_followers, follower_list)

                    st.dataframe(
                        df,
                        column_config={
                            "Follower": "팔로워",
                            "Qoo10 インスタを followしている（更新日：）": "팔로우 상태",
                        },
                        hide_index=True,
                        use_container_width=True,
                    )

                    total = len(input_followers)
                    following = int(
                        (
                            df["Qoo10 インスタを followしている（更新日：）"] == "TRUE"
                        ).sum()
                    )
                    not_following = total - following

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("전체 팔로워", total)
                    with col2:
                        st.metric("팔로우 중", following)
                    with col3:
                        st.metric("팔로우 안함", not_following)

                    # 복사를 위한 결과 표시
                    st.text_area(
                        "결과 (복사하려면 전체 선택 후 Ctrl+C 또는 Cmd+C를 누르세요)",
                        value="\n".join(
                            df["Qoo10 インスタを followしている（更新日：）"].tolist()
                        ),
                        height=200,
                    )

                    # 성공적으로 비교가 완료되고, 적어도 한 명 이상 팔로우 중일 때 축하 애니메이션
                    if following > 0:
                        st.balloons()
