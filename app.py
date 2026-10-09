import logging
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src import config
from src.annotator import Annotator
from src.detector import ShelfDetector
from src.processors import ImageProcessor, VideoProcessor
from src.validator import validate

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Shelf Product Counter", layout="centered")
st.title("Shelf Product Counter")
st.caption("Upload a shelf photo (.jpg, .png) or a short video (.mp4, under 30 seconds).")

if not config.ROBOFLOW_API_KEY or not config.MODEL_ID:
    st.error("ROBOFLOW_API_KEY and MODEL_ID must be set in the .env file. See the README for setup.")
    st.stop()


@st.cache_resource(show_spinner="Loading the model (first run only)...")
def load_detector() -> ShelfDetector:
    return ShelfDetector(config.MODEL_ID, config.ROBOFLOW_API_KEY, config.CONFIDENCE)


confidence = st.sidebar.slider(
    "Confidence threshold",
    min_value=0.05,
    max_value=0.95,
    value=config.CONFIDENCE,
    step=0.05,
    help="Lower finds more products but may add false boxes. Higher keeps only confident boxes.",
)
st.sidebar.caption(f"Model: `{config.MODEL_ID}`")

uploaded = st.file_uploader("Choose a file", type=None)

if uploaded is not None:
    name = Path(uploaded.name)
    with tempfile.TemporaryDirectory() as work_dir:
        work_dir = Path(work_dir)
        # Keep the original name so the download is called <name>_annotated.<ext>.
        input_path = work_dir / f"{name.stem}{name.suffix.lower()}"
        input_path.write_bytes(uploaded.getbuffer())

        check = validate(input_path)
        if not check.ok:
            st.error(check.message)
            st.stop()

        try:
            detector = load_detector()
            if check.kind == "image":
                processor = ImageProcessor(detector, Annotator(), confidence=confidence, output_dir=work_dir)
                with st.spinner("Counting products..."):
                    result = processor.process(input_path)
            else:
                bar = st.progress(0.0, text="Counting products in each frame...")
                processor = VideoProcessor(
                    detector,
                    Annotator(),
                    confidence=confidence,
                    output_dir=work_dir,
                    on_progress=lambda done: bar.progress(done, text=f"Counting products in each frame... {done:.0%}"),
                )
                result = processor.process(input_path)
                bar.empty()
            data = result.output_path.read_bytes()
        except Exception:
            logger.exception("Processing failed for %s", uploaded.name)
            st.error("Something went wrong while processing the file. Check the terminal for details and try again.")
            st.stop()

    if check.kind == "image":
        count_col, time_col = st.columns(2)
        count_col.metric("Products found", result.count)
        time_col.metric("Processing time", f"{result.seconds:.2f} s")
        result_tab, original_tab = st.tabs(["Result", "Original"])
        result_tab.image(data, width="stretch")
        original_tab.image(uploaded.getvalue(), width="stretch")
        st.download_button(
            "Download result", data, result.output_path.name, "image/jpeg", on_click="ignore", type="primary"
        )
    else:
        counts = pd.DataFrame(
            {
                "Seconds": [i / result.fps for i in range(len(result.per_frame_counts))],
                "Products": result.per_frame_counts,
            }
        )
        max_col, avg_col, time_col = st.columns(3)
        max_col.metric("Most products in a frame", result.count)
        avg_col.metric("Average per frame", f"{counts['Products'].mean():.0f}")
        time_col.metric("Processing time", f"{result.seconds:.1f} s")
        st.video(data)
        st.caption(f"Products per frame ({len(counts)} frames, detection on every {config.FRAME_STEP}th frame)")
        st.line_chart(counts, x="Seconds", y="Products")
        video_col, csv_col = st.columns(2)
        video_col.download_button(
            "Download result", data, result.output_path.name, "video/mp4", on_click="ignore", type="primary"
        )
        csv_col.download_button(
            "Download per-frame counts (CSV)",
            counts.rename_axis("Frame").to_csv(),
            f"{name.stem}_counts.csv",
            "text/csv",
            on_click="ignore",
        )
