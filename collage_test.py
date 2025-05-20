# app.py  ─ Streamlit 광고 소재 툴 v0.1
# 실행:  streamlit run app.py
import datetime
import io
import subprocess
import tempfile
import time
import uuid
import zipfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

VIDEO_AVAILABLE = True


# ────────────────────────────────────────────────
# 1️⃣ 플랫폼·템플릿 메타데이터 ---------------------
#    (가장 많이 쓰이는 사이즈·비율 기준)
TEMPLATES = {
    "Meta (Instagram·Facebook)": {
        "Feed Square (1080×1080)": {
            "w": 1080,
            "h": 1080,
            "type": "image/video",
        },  # :contentReference[oaicite:0]{index=0}
        "Reels/Stories Vertical (1080×1920)": {
            "w": 1080,
            "h": 1920,
            "type": "image/video",
        },  # :contentReference[oaicite:1]{index=1}
    },
    "TikTok": {
        "Vertical Video (720×1280)": {
            "w": 720,
            "h": 1280,
            "type": "image/video",
        },  # :contentReference[oaicite:2]{index=2}
    },
    "LINE Ads": {
        "Square Image/Video (1080×1080)": {
            "w": 1080,
            "h": 1080,
            "type": "image/video",
        },  # :contentReference[oaicite:3]{index=3}
        "PC Headline Banner (1280×338)": {
            "w": 1280,
            "h": 338,
            "type": "image/video",
        },  # :contentReference[oaicite:4]{index=4}
    },
    "Criteo": {
        "Square (1200×1200)": {
            "w": 1200,
            "h": 1200,
            "type": "image/video",
        },  # :contentReference[oaicite:5]{index=5}
        "Horizontal (1200×628)": {
            "w": 1200,
            "h": 628,
            "type": "image/video",
        },  # :contentReference[oaicite:6]{index=6}
        "Vertical (800×1200)": {
            "w": 800,
            "h": 1200,
            "type": "image/video",
        },  # :contentReference[oaicite:7]{index=7}
    },
}


COLLAGE_LAYOUTS = {
    "Side-by-Side 50/50": {"ratio": (1, 1), "axis": "horizontal"},
    "Left 70 · Right 30": {"ratio": (7, 3), "axis": "horizontal"},
    "Top 60 · Bottom 40": {"ratio": (6, 4), "axis": "vertical"},
}

# ────────────────────────────────────────────────
# 2️⃣ 사이드바 – 플랫폼 & 템플릿 -------------------
st.sidebar.header("🖼️ 매체 / 레이아웃 선택")
platform = st.sidebar.selectbox("플랫폼", list(TEMPLATES.keys()))
layout = st.sidebar.selectbox("템플릿", list(TEMPLATES[platform].keys()))
spec = TEMPLATES[platform][layout]

st.title("📐 Creative collage Demo")
st.subheader(f"{platform} – {layout}")
st.markdown(f"""
- **권장 사이즈**: {spec["w"]} × {spec["h"]} px  
- **타입**: {spec["type"]}  
""")


# ────────────────────────────────────────────────
# 4️⃣ 미리보기 & 리사이즈 -------------------------
@st.cache_data(show_spinner=False)
def draw_layout_preview(name, size=180):
    spec = COLLAGE_LAYOUTS[name]
    w = h = size
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    if spec["axis"] == "horizontal":
        w1 = int(w * spec["ratio"][0] / sum(spec["ratio"]))
        draw.rectangle([0, 0, w1, h], fill="#d0d0d0")
        draw.rectangle([w1, 0, w, h], fill="#a0a0a0")
    else:  # vertical
        h1 = int(h * spec["ratio"][0] / sum(spec["ratio"]))
        draw.rectangle([0, 0, w, h1], fill="#d0d0d0")
        draw.rectangle([0, h1, w, h], fill="#a0a0a0")
    return img


def resize_with_padding(image, target_width, target_height, mode="contain"):
    """비율을 유지하면서 리사이즈
    mode: 'contain' (화면 맞추기) 또는 'cover' (화면 채우기)
    """
    if isinstance(image, np.ndarray):
        # OpenCV 이미지
        ih, iw = image.shape[:2]
        if mode == "contain":
            scale = min(target_width / iw, target_height / ih)
        else:  # cover
            scale = max(target_width / iw, target_height / ih)

        new_w = int(iw * scale)
        new_h = int(ih * scale)
        resized = cv2.resize(image, (new_w, new_h))

        if mode == "contain":
            # 패딩 추가
            delta_w = target_width - new_w
            delta_h = target_height - new_h
            top = delta_h // 2
            bottom = delta_h - top
            left = delta_w // 2
            right = delta_w - left
            return cv2.copyMakeBorder(
                resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0]
            )
        else:  # cover
            # 중앙 크롭
            start_x = (new_w - target_width) // 2 if new_w > target_width else 0
            start_y = (new_h - target_height) // 2 if new_h > target_height else 0
            return resized[
                start_y : start_y + target_height, start_x : start_x + target_width
            ]
    else:
        # PIL 이미지
        iw, ih = image.size
        if mode == "contain":
            scale = min(target_width / iw, target_height / ih)
        else:  # cover
            scale = max(target_width / iw, target_height / ih)

        new_w = int(iw * scale)
        new_h = int(ih * scale)
        resized = image.resize((new_w, new_h), Image.LANCZOS)

        if mode == "contain":
            # 패딩 추가
            result = Image.new("RGB", (target_width, target_height), (0, 0, 0))
            paste_x = (target_width - new_w) // 2
            paste_y = (target_height - new_h) // 2
            result.paste(resized, (paste_x, paste_y))
            return result
        else:  # cover
            # 중앙 크롭
            left = (new_w - target_width) // 2 if new_w > target_width else 0
            top = (new_h - target_height) // 2 if new_h > target_height else 0
            right = left + target_width
            bottom = top + target_height
            return resized.crop((left, top, right, bottom))


def resize_video(tmp_path, w, h):
    if not VIDEO_AVAILABLE:
        st.warning("OpenCV 미설치 → 동영상 리사이즈는 생략됩니다.")
        return tmp_path

    cap = cv2.VideoCapture(str(tmp_path))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    out_path = tmp_path.with_suffix(".resized.mp4")
    out = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        resized_frame = cv2.resize(frame, (w, h))
        out.write(resized_frame)

    cap.release()
    out.release()
    return out_path


# ────────────────────────────────────────────────
# 5️⃣ 결과 ZIP 패키징 -----------------------------
# ─────────────────────────────────────────
# (B) 사이드바 – "콜라주 모드" 전환 및 레이아웃 선택
# st.sidebar.markdown("---")
collage_mode = True

# 리사이징 모드 선택
st.sidebar.markdown("---")
resize_mode = st.sidebar.radio(
    "📐 리사이징 모드",
    options=["화면 맞추기 (Contain)", "화면 채우기 (Cover)"],
    help="""
    - 화면 맞추기: 비율을 유지하면서 영역 안에 모두 표시 (검은색 여백 발생)
    - 화면 채우기: 비율을 유지하면서 영역을 꽉 채워 표시 (이미지 일부 잘림)
    """,
)
resize_mode = "cover" if "채우기" in resize_mode else "contain"

if collage_mode:
    col1, col2, col3 = st.sidebar.columns(3)
    layout_names = list(COLLAGE_LAYOUTS.keys())
    thumbs = [draw_layout_preview(n) for n in layout_names]
    # 3개의 썸네일을 가로로 배치하고 radio로 선택
    idx = st.sidebar.radio(
        label="",
        options=range(len(layout_names)),
        format_func=lambda i: layout_names[i],
        horizontal=True,
    )
    collage_layout = layout_names[idx]
    st.sidebar.image(thumbs[idx], caption=collage_layout, use_container_width=True)

# ─────────────────────────────────────────
# (C) 업로드 영역 수정 – "최대 2개"
upload_help = """이미지 2개 / 이미지+동영상 1개씩 (최대 2개)
- 파일 크기 제한: 200MB 이하
- 지원 형식: JPG, PNG, MP4, MOV"""

uploaded = st.file_uploader(
    "🔽 콜라주할 소재를 업로드 해주세요.",
    type=["jpg", "jpeg", "png", "mp4", "mov"],
    accept_multiple_files=True,
    help=upload_help,
)

if uploaded:
    # 파일 크기 체크 (200MB = 200 * 1024 * 1024 bytes)
    MAX_SIZE = 200 * 1024 * 1024
    oversized_files = [f.name for f in uploaded if f.size > MAX_SIZE]

    if oversized_files:
        st.error(f"""
        다음 파일이 크기 제한(200MB)을 초과했습니다:
        - {chr(10).join(oversized_files)}
        
        파일 크기를 줄여서 다시 시도해주세요.
        """)
        st.stop()

    if len(uploaded) > 2:
        st.warning("2개까지만 업로드 가능합니다.")
        uploaded = uploaded[:2]


# ─────────────────────────────────────────
# (D) 콜라주 생성 함수
def get_video_thumb(file, w, h, mode="contain"):
    """OpenCV로 첫 프레임 추출 → PIL 이미지 반환 (비율 유지)"""
    if not VIDEO_AVAILABLE:
        return Image.new("RGB", (w, h), "black")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(file.read())
        tmp.flush()
        cap = cv2.VideoCapture(tmp.name)
        ret, frame = cap.read()
        cap.release()

        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = resize_with_padding(frame, w, h, mode)
            return Image.fromarray(frame)
        return Image.new("RGB", (w, h), "black")


def sanitize_filename(original_filename):
    """안전한 파일명 생성
    - UUID와 타임스탬프 조합으로 고유한 파일명 생성
    - 원본 확장자 유지
    """
    # 확장자 추출
    ext = Path(original_filename).suffix
    # 안전한 파일명 생성 (UUID + 타임스탬프)
    safe_name = f"{uuid.uuid4().hex}_{int(datetime.datetime.now().timestamp())}{ext}"
    return safe_name


def make_collage(
    files, layout_key, canvas_w=1080, canvas_h=1080, resize_mode="contain"
):
    spec = COLLAGE_LAYOUTS[layout_key]
    axis = spec["axis"]
    r1, r2 = spec["ratio"]
    total = r1 + r2
    if axis == "horizontal":
        w1 = int(canvas_w * r1 / total)
        w2 = canvas_w - w1
        h1 = h2 = canvas_h
    else:  # vertical
        h1 = int(canvas_h * r1 / total)
        h2 = canvas_h - h1
        w1 = w2 = canvas_w

    # 두 칸에 들어갈 PIL 이미지 준비
    imgs = []
    for f, (w, h) in zip(files, [(w1, h1), (w2, h2)]):
        if f.type.startswith("image"):
            img = Image.open(f).convert("RGB")
            img = resize_with_padding(img, w, h, resize_mode)
        else:  # video
            img = get_video_thumb(f, w, h, resize_mode)
        imgs.append(img)

    # 캔버스 합치기
    canvas = Image.new("RGB", (canvas_w, canvas_h), "black")
    if axis == "horizontal":
        canvas.paste(imgs[0], (0, 0))
        canvas.paste(imgs[1], (w1, 0))
    else:
        canvas.paste(imgs[0], (0, 0))
        canvas.paste(imgs[1], (0, h1))
    return canvas


def make_collage_video(
    files, layout_key, canvas_w=1080, canvas_h=1080, fps=30, resize_mode="contain"
):
    try:
        spec = COLLAGE_LAYOUTS[layout_key]
        axis = spec["axis"]
        r1, r2 = spec["ratio"]
        total = r1 + r2

        if axis == "horizontal":
            w1 = int(canvas_w * r1 / total)
            w2 = canvas_w - w1
            h1 = h2 = canvas_h
            pos = [(0, 0), (w1, 0)]
        else:  # vertical
            h1 = int(canvas_h * r1 / total)
            h2 = canvas_h - h1
            w1 = w2 = canvas_w
            pos = [(0, 0), (0, h1)]

        # 안전한 임시 파일 생성
        temp_dir = tempfile.mkdtemp()
        output_path = Path(temp_dir) / "output.mp4"

        # 'mp4v' 코덱을 우선 사용
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (canvas_w, canvas_h))

        if not out.isOpened():
            # 'mp4v'가 실패하면 'avc1' 시도
            out.release()
            fourcc = cv2.VideoWriter_fourcc(*"avc1")
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (canvas_w, canvas_h))

            if not out.isOpened():
                st.error("비디오 작성기를 초기화할 수 없습니다.")
                return None

        # 비디오 프레임 또는 이미지 준비
        video_captures = []
        static_images = []
        sizes = [(w1, h1), (w2, h2)]

        max_frames = 0
        for file, (w, h) in zip(files, sizes):
            try:
                if file.type.startswith("video"):
                    # 비디오 파일 임시 저장
                    temp_video = Path(temp_dir) / f"video_{uuid.uuid4()}.mp4"
                    temp_video.write_bytes(file.read())

                    cap = cv2.VideoCapture(str(temp_video))
                    if not cap.isOpened():
                        st.error(f"비디오 파일을 열 수 없습니다: {file.name}")
                        continue

                    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    max_frames = max(max_frames, frames)
                    video_captures.append({
                        "capture": cap,
                        "size": (w, h),
                        "position": pos[len(static_images) + len(video_captures)],
                        "temp_file": temp_video,
                    })
                else:
                    # 이미지 파일 처리
                    img = Image.open(file).convert("RGB")
                    img = resize_with_padding(img, w, h, resize_mode)
                    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    static_images.append({
                        "image": img,
                        "position": pos[len(static_images)],
                    })
            except Exception as e:
                st.error(f"파일 처리 중 오류 발생: {file.name}\n{str(e)}")
                continue

        if not video_captures and not static_images:
            st.error("처리 가능한 파일이 없습니다.")
            return None

        # 최소 프레임 수 설정
        if max_frames == 0:
            max_frames = fps * 5  # 정적 이미지만 있는 경우 5초

        # 프레임 생성 및 저장
        for frame_idx in range(max_frames):
            try:
                # 흰색 캔버스 생성
                canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

                # 정적 이미지 추가
                for img_data in static_images:
                    x, y = img_data["position"]
                    h, w = img_data["image"].shape[:2]
                    canvas[y : y + h, x : x + w] = img_data["image"]

                # 비디오 프레임 추가
                for vid_data in video_captures:
                    ret, frame = vid_data["capture"].read()
                    if not ret:  # 비디오 끝에 도달하면 처음으로 되감기
                        vid_data["capture"].set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = vid_data["capture"].read()

                    if ret:
                        frame = resize_with_padding(
                            frame, vid_data["size"][0], vid_data["size"][1], resize_mode
                        )
                        x, y = vid_data["position"]
                        h, w = frame.shape[:2]
                        canvas[y : y + h, x : x + w] = frame

                out.write(canvas)
            except Exception as e:
                st.error(f"프레임 {frame_idx} 처리 중 오류 발생: {str(e)}")
                continue

        # 리소스 정리
        out.release()
        for vid_data in video_captures:
            vid_data["capture"].release()
            vid_data["temp_file"].unlink()  # 임시 파일 삭제

        # FFmpeg로 웹 호환 포맷으로 변환
        web_compatible_output = str(Path(temp_dir) / "output_web.mp4")

        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    str(output_path),
                    "-c:v",
                    "libx264",
                    "-preset",
                    "fast",
                    "-pix_fmt",
                    "yuv420p",
                    "-y",
                    web_compatible_output,
                ],
                check=True,
                capture_output=True,
            )
            return web_compatible_output
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            st.warning(
                f"""FFmpeg 처리 중 오류가 발생했습니다: {str(e)}
                다운로드는 가능하지만 미리보기는 작동하지 않을 수 있습니다."""
            )
            return str(output_path)
    except Exception as e:
        st.error(f"콜라주 생성 중 오류가 발생했습니다: {str(e)}")
        return None


def is_any_video(files):
    return any(f.type.startswith("video") for f in files)


if collage_mode and uploaded and 1 < len(uploaded) <= 2:
    st.subheader("🎬 콜라주 미리보기")

    # 선택된 템플릿의 규격 사용
    canvas_w = spec["w"]
    canvas_h = spec["h"]

    if is_any_video(uploaded):
        start_time = time.time()
        collage_video = make_collage_video(
            uploaded, collage_layout, canvas_w, canvas_h, resize_mode=resize_mode
        )
        end_time = time.time()
        st.video(collage_video)

        st.write(f"콜라주 생성 시간: {end_time - start_time:.2f}초")

        with open(collage_video, "rb") as f:
            st.download_button(
                "⬇️ 콜라주 영상 다운로드",
                data=f,
                file_name=f"collage_{canvas_w}x{canvas_h}.mp4",
                mime="video/mp4",
            )
    else:
        collage_img = make_collage(uploaded, collage_layout, canvas_w, canvas_h)
        st.image(collage_img, use_container_width=True)

        buf = io.BytesIO()
        collage_img.save(buf, format="PNG")
        buf.seek(0)
        st.download_button(
            "⬇️ 콜라주 PNG 다운로드",
            data=buf,
            file_name=f"collage_{canvas_w}x{canvas_h}.png",
            mime="image/png",
        )


def create_zip(files_dict, spec):
    buff = io.BytesIO()
    with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as zf:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"{platform.replace(' ', '')}_{layout.replace(' ', '_')}_{timestamp}"
        # 이미지
        if files_dict.get("image"):
            img = Image.open(files_dict["image"])
            img = resize_with_padding(img, spec["w"], spec["h"])
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="PNG")
            zf.writestr(f"{base}.png", img_bytes.getvalue())
        # 동영상
        if files_dict.get("video"):
            video_path = Path(files_dict["video"].name)
            if spec["type"] == "video":
                # (옵션) 리사이즈
                tmp = Path("/tmp") / video_path.name
                tmp.write_bytes(files_dict["video"].read())
                final_path = (
                    resize_video(tmp, spec["w"], spec["h"]) if VIDEO_AVAILABLE else tmp
                )
                zf.write(final_path, f"{base}{final_path.suffix}")
            else:
                zf.writestr(video_path.name, files_dict["video"].read())
    buff.seek(0)
    return buff


# if uploaded_files.get("image") or uploaded_files.get("video"):
#     if st.button("📦 ZIP 다운로드"):
#         zip_buff = create_zip(uploaded_files, spec)
#         st.download_button(
#             label="⬇️ 결과 ZIP 저장",
#             data=zip_buff,
#             file_name="creative_assets.zip",
#             mime="application/zip",
#         )
