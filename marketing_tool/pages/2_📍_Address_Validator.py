import time
from typing import List

import pandas as pd
import requests
import streamlit as st


def clean_zipcode(zipcode: str) -> str:
    """우편번호에서 숫자만 추출."""
    return "".join(filter(str.isdigit, zipcode))


def parse_input_followers(input_text: str) -> List[str]:
    """텍스트 입력에서 주소 후보를 파싱하고 중복 제거(입력 순서 유지)."""
    tokens = [token.strip() for token in input_text.replace(",", "\n").split()]
    seen: set[str] = set()
    unique_tokens: List[str] = []
    for token in tokens:
        if token and token not in seen:
            seen.add(token)
            unique_tokens.append(token)
    return unique_tokens


def validate_address(zipcode: str, delay: float = 0.5) -> dict:
    """주소 유효성 검증 API 호출.

    Args:
        zipcode: 검증할 우편번호
        delay: API 호출 전 대기 시간 (초)

    Returns:
        {
            "valid": bool,
            "code": int,
            "data": {...} or None,
            "error": str or None
        }
    """
    time.sleep(delay)  # Rate limiting

    try:
        url = f"https://api.zipaddress.net/?zipcode={zipcode}"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return {
                "valid": False,
                "code": response.status_code,
                "data": None,
                "error": f"HTTP {response.status_code}",
            }

        json_data = response.json()
        code = json_data.get("code", 0)
        data = json_data.get("data")

        if code == 200 and data is not None:
            return {
                "valid": True,
                "code": code,
                "data": data,
                "error": None,
            }
        else:
            return {
                "valid": False,
                "code": code,
                "data": None,
                "error": "Invalid address" if code != 200 else "No data",
            }

    except requests.exceptions.Timeout:
        return {
            "valid": False,
            "code": 0,
            "data": None,
            "error": "Request timeout",
        }
    except requests.exceptions.RequestException as e:
        return {
            "valid": False,
            "code": 0,
            "data": None,
            "error": f"Network error: {str(e)}",
        }
    except Exception as e:  # noqa: BLE001
        return {
            "valid": False,
            "code": 0,
            "data": None,
            "error": f"Error: {str(e)}",
        }


def build_address_dataframe(results: List[dict]) -> pd.DataFrame:
    """주소 검증 결과 데이터프레임 생성."""
    rows = []
    for result in results:
        zipcode = result["zipcode"]
        valid = result["valid"]
        data = result.get("data")

        row = {
            "Postal Code": zipcode,
            "Valid": "TRUE" if valid else "FALSE",
            "pref": data.get("pref", "") if data else "",
            "address": data.get("address", "") if data else "",
            "city": data.get("city", "") if data else "",
            "town": data.get("town", "") if data else "",
            "fullAddress": data.get("fullAddress", "") if data else "",
        }
        rows.append(row)

    return pd.DataFrame(rows)


# ===== UI =====
st.set_page_config(page_title="Address Validator", layout="wide")
st.title("주소 유효성 검증")

# 입력 방식 선택
input_mode = st.radio(
    "입력 방식 선택",
    ["단일 주소", "여러 주소 (줄바꿈으로 구분)"],
    horizontal=True,
)

if input_mode == "단일 주소":
    zipcode_input = st.text_input(
        "우편번호를 입력하세요",
        placeholder="예: 4530809",
        help="검증할 우편번호를 입력하세요.",
    )

    if st.button("검증하기"):
        if not zipcode_input.strip():
            st.warning("우편번호를 입력해주세요.")
        else:
            cleaned_zipcode = clean_zipcode(zipcode_input.strip())
            if not cleaned_zipcode:
                st.warning("유효한 우편번호를 입력해주세요.")
            else:
                with st.spinner("주소를 검증하는 중..."):
                    result = validate_address(cleaned_zipcode, delay=0)

                if result["valid"]:
                    st.success("유효한 주소입니다!")
                    data = result["data"]
                    df = pd.DataFrame([{
                        "Postal Code": cleaned_zipcode,
                        "Valid": "TRUE",
                        "pref": data.get("pref", ""),
                        "address": data.get("address", ""),
                        "city": data.get("city", ""),
                        "town": data.get("town", ""),
                        "fullAddress": data.get("fullAddress", ""),
                    }])

                    st.dataframe(
                        df,
                        hide_index=True,
                        use_container_width=True,
                    )
                else:
                    st.error(f"유효하지 않은 주소입니다. {result.get('error', '')}")
                    df = pd.DataFrame([{
                        "Postal Code": cleaned_zipcode,
                        "Valid": "FALSE",
                        "pref": "",
                        "address": "",
                        "city": "",
                        "town": "",
                        "fullAddress": "",
                    }])
                    st.dataframe(
                        df,
                        hide_index=True,
                        use_container_width=True,
                    )

else:  # 여러 주소
    zipcodes_text = st.text_area(
        "우편번호 목록을 입력하세요 (여러 줄)",
        height=200,
        help="한 줄에 하나씩 또는 공백/쉼표로 구분하여 입력하세요. 하이픈(-) 등 숫자 외 문자는 자동으로 제거됩니다.",
    )

    if st.button("검증하기"):
        if not zipcodes_text.strip():
            st.warning("우편번호를 입력해주세요.")
        else:
            zipcodes = parse_input_followers(zipcodes_text)
            if not zipcodes:
                st.warning("유효한 우편번호를 찾지 못했습니다.")
            else:
                # 숫자만 추출하여 정리
                cleaned_zipcodes = []
                for zipcode in zipcodes:
                    cleaned = clean_zipcode(zipcode.strip())
                    if cleaned:
                        cleaned_zipcodes.append(cleaned)

                if not cleaned_zipcodes:
                    st.warning("유효한 우편번호를 찾지 못했습니다.")
                else:
                    st.write(f"### 검증할 주소 수: {len(cleaned_zipcodes)}")

                    # 진행 상황 표시
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    results = []
                    for i, zipcode in enumerate(cleaned_zipcodes):
                        status_text.text(f"검증 중: {i+1}/{len(cleaned_zipcodes)} - {zipcode}")
                        result = validate_address(zipcode)
                        result["zipcode"] = zipcode
                        results.append(result)
                        progress_bar.progress((i + 1) / len(cleaned_zipcodes))

                    status_text.text("검증 완료!")

                    # 결과 데이터프레임 생성 및 표시
                    df = build_address_dataframe(results)

                    st.dataframe(
                        df,
                        hide_index=True,
                        use_container_width=True,
                    )

                    # 요약 통계
                    total = len(results)
                    valid_count = sum(1 for r in results if r["valid"])
                    invalid_count = total - valid_count

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("전체 주소", total)
                    with col2:
                        st.metric("유효한 주소", valid_count)
                    with col3:
                        st.metric("유효하지 않은 주소", invalid_count)
