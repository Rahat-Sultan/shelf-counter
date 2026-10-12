import logging
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

# On Streamlit Community Cloud the settings are pasted into the Secrets box. Streamlit copies top-level secrets
# into environment variables only when secrets are first loaded, so load them now, before src.config reads the
# environment. Without a secrets file this does nothing. Streamlit treats a secrets file with a typo (invalid TOML)
# as missing, so that case shows up below as "not set".
st.secrets.load_if_toml_exists()

from src import config  # noqa: E402  (must come after the secrets are loaded)
from src.annotator import Annotator  # noqa: E402
from src.errors import friendly_message  # noqa: E402
from src.image_io import read_image  # noqa: E402
from src.processors import ImageProcessor, VideoProcessor  # noqa: E402
from src.validator import validate  # noqa: E402

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Shelf Product Counter", layout="centered")
st.title("Shelf Product Counter")
st.caption(
    "Count the products on a shelf from a photo (.jpg, .png, .heic) or a short video (.mp4, .mov, up to 30 "
    "seconds). Keep people out of the frame."
)

missing = [
    name
    for name, value in [("ROBOFLOW_API_KEY", config.ROBOFLOW_API_KEY), ("MODEL_ID", config.MODEL_ID)]
    if not value or value == config.API_KEY_PLACEHOLDER
]
if missing:
    st.error(
        f"{' and '.join(missing)} {'is' if len(missing) == 1 else 'are'} not set. On your laptop, copy "
        ".env.example to .env and fill in your values. On Streamlit Community Cloud, add them in App settings, "
        'Secrets, one per line, like ROBOFLOW_API_KEY = "your key" (a typo there, such as a missing quote, makes '
        "all secrets unreadable). On other hosts, add them as environment variables. "
        "Then restart the app. See STARTUP.md or DEPLOY.md."
    )
    st.stop()

for warning in config.WARNINGS:
    st.warning(warning)


@st.cache_resource(show_spinner="Loading the model. The first start after a reboot can take up to 30 seconds...")
def load_detector():
    """Loads the model once per server. Imported here because importing inference takes 10 to 20 seconds,
    and doing it at the top of this file would leave the page blank for that long."""
    from src.detector import ShelfDetector

    return ShelfDetector(config.MODEL_ID, config.ROBOFLOW_API_KEY, config.CONFIDENCE)


SOURCES = {"upload": ":material/upload: Upload a file", "camera": ":material/photo_camera: Take a photo"}

# Input choice and settings sit in the page, not the sidebar: on phones the sidebar is collapsed and easy to miss.
with st.container(horizontal=True, vertical_alignment="center"):
    source = st.segmented_control(
        "Input",
        options=list(SOURCES),
        format_func=SOURCES.get,
        default="upload",
        required=True,
        label_visibility="collapsed",
        key="source",
    )
    with st.popover("Detection settings", icon=":material/tune:"):
        confidence = st.slider(
            "Confidence threshold",
            min_value=config.MIN_CONFIDENCE,
            max_value=config.MAX_CONFIDENCE,
            value=config.CONFIDENCE,
            step=0.05,
            help="Lower finds more products but may add false boxes. Higher keeps only confident boxes.",
        )
        st.caption(f"Model: `{config.MODEL_ID}`")

if source == "camera":
    # 1080p is the highest preset; small images miss products. Phones on HTTPS can use this too.
    uploaded = st.camera_input("Take a photo of the shelf", resolution="1080p", help="Keep people out of the frame.")
    upload_name = Path("camera_photo.jpg")
else:
    uploaded = st.file_uploader("Choose a photo or video")
    upload_name = Path(uploaded.name) if uploaded is not None else None

if uploaded is None:
    # Warm the model while the user picks a file, so the first upload is fast and a bad key or
    # model ID is reported straight away rather than after the first upload.
    try:
        load_detector()
    except Exception as exc:
        logger.exception("Loading the model failed")
        st.error(friendly_message(exc))
        st.stop()

if uploaded is not None:
    name = upload_name
    with tempfile.TemporaryDirectory() as work_dir:
        work_dir = Path(work_dir)
        # Keep the original name so the download is called <name>_annotated.<ext>.
        input_path = work_dir / f"{name.stem}{name.suffix.lower()}"
        input_path.write_bytes(uploaded.getbuffer())

        check = validate(input_path)
        if not check.ok:
            st.error(check.message)
            st.stop()

        bar = None
        try:
            detector = load_detector()
            if check.kind == "image":
                processor = ImageProcessor(detector, Annotator(), confidence=confidence, output_dir=work_dir)
                with st.spinner("Counting products..."):
                    result = processor.process(input_path)
                # Decoded here because browsers cannot show HEIC photos as uploaded.
                original = read_image(input_path)
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
        except Exception as exc:
            logger.exception("Processing failed for %s", name)
            if bar is not None:
                bar.empty()
            st.error(friendly_message(exc))
            st.stop()

    if result.note:
        st.warning(result.note)

    if check.kind == "image":
        # A horizontal container keeps both metrics on one row on phones, so the photo stays near the top.
        with st.container(horizontal=True):
            st.metric("Products found", result.count, border=True, width="content")
            st.metric("Processing time", f"{result.seconds:.2f} s", border=True, width="content")
        result_tab, original_tab = st.tabs(["Result", "Original"])
        result_tab.image(data, width="stretch", alt=f"Shelf photo with {result.count} products boxed")
        original_tab.image(original, channels="BGR", width="stretch", alt="The photo as uploaded")
        st.download_button(
            "Download result",
            data,
            result.output_path.name,
            "image/jpeg",
            on_click="ignore",
            type="primary",
            icon=":material/download:",
        )
    else:
        counts = pd.DataFrame(
            {
                "Seconds": [i / result.fps for i in range(len(result.per_frame_counts))],
                "Products": result.per_frame_counts,
            }
        )
        with st.container(horizontal=True):
            st.metric("Most in a frame", result.count, border=True, width="content")
            st.metric("Average per frame", f"{counts['Products'].mean():.0f}", border=True, width="content")
            st.metric("Processing time", f"{result.seconds:.1f} s", border=True, width="content")
        st.video(data, alt="Shelf video with the products boxed in every frame")
        st.caption(f"Products per frame ({len(counts)} frames, detection on every {config.FRAME_STEP}th frame)")
        st.line_chart(counts, x="Seconds", y="Products", alt="Number of products found in each frame over time")
        with st.container(horizontal=True):
            st.download_button(
                "Download result",
                data,
                result.output_path.name,
                "video/mp4",
                on_click="ignore",
                type="primary",
                icon=":material/download:",
            )
            st.download_button(
                "Download per-frame counts (CSV)",
                counts.rename_axis("Frame").to_csv(),
                f"{name.stem}_counts.csv",
                "text/csv",
                on_click="ignore",
                icon=":material/table:",
            )
