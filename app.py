import tempfile
from pathlib import Path

import streamlit as st

from src import config
from src.annotator import Annotator
from src.detector import ShelfDetector
from src.processors import ImageProcessor, VideoProcessor
from src.validator import validate

st.set_page_config(page_title="Shelf Product Counter", layout="centered")
st.title("Shelf Product Counter")
st.caption("Upload a shelf photo (.jpg, .png) or a short video (.mp4, under 30 seconds).")


@st.cache_resource
def load_detector() -> ShelfDetector:
    return ShelfDetector(config.MODEL_ID, config.ROBOFLOW_API_KEY, config.CONFIDENCE)


uploaded = st.file_uploader("Choose a file", type=None)

if uploaded is not None:
    suffix = Path(uploaded.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = Path(tmp.name)

    check = validate(tmp_path)
    if not check.ok:
        st.error(check.message)
    else:
        try:
            detector = load_detector()
            processor_cls = ImageProcessor if check.kind == "image" else VideoProcessor
            with st.spinner("Counting products..."):
                result = processor_cls(detector, Annotator()).process(tmp_path)
        except Exception as exc:
            st.error(f"Something went wrong while processing the file: {exc}")
        else:
            st.metric("Products found", result.count)
            st.caption(f"Processed in {result.seconds:.1f} seconds")
            data = result.output_path.read_bytes()
            if check.kind == "image":
                st.image(data)
                st.download_button("Download result", data, result.output_path.name, "image/jpeg")
            else:
                st.video(data)
                st.line_chart(result.per_frame_counts)
                st.download_button("Download result", data, result.output_path.name, "video/mp4")
