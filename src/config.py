import os
from pathlib import Path

from dotenv import dotenv_values

# Read .env into our own settings instead of os.environ. The inference package parses some of the same
# names (for example CONFIDENCE) at import time, and a bad value there would crash it before our checks.
# Real environment variables still take precedence over .env, as with load_dotenv().
_settings = {**dotenv_values(), **os.environ}

# Problems found while reading settings; the page shows these as warnings instead of crashing.
WARNINGS: list[str] = []

API_KEY_PLACEHOLDER = "your_api_key_here"  # the value in .env.example
ROBOFLOW_API_KEY = (_settings.get("ROBOFLOW_API_KEY") or "").strip()
MODEL_ID = (_settings.get("MODEL_ID") or "").strip()

DEFAULT_CONFIDENCE = 0.3
MIN_CONFIDENCE, MAX_CONFIDENCE = 0.05, 0.95  # the slider's range


def _read_confidence() -> float:
    raw = (_settings.get("CONFIDENCE") or str(DEFAULT_CONFIDENCE)).strip()
    try:
        value = float(raw)
    except ValueError:
        WARNINGS.append(f"CONFIDENCE in .env is '{raw}', which is not a number. Using {DEFAULT_CONFIDENCE}.")
        return DEFAULT_CONFIDENCE
    clamped = min(max(value, MIN_CONFIDENCE), MAX_CONFIDENCE)
    if clamped != value:
        WARNINGS.append(
            f"CONFIDENCE in .env is {value}, outside {MIN_CONFIDENCE} to {MAX_CONFIDENCE}. Using {clamped}."
        )
    return clamped


CONFIDENCE = _read_confidence()

# The chosen model (planogram_sku110k/1, trained on SKU-110K) has a single class named "0".
# Only boxes of this class are drawn and counted.
PRODUCT_CLASS = (_settings.get("PRODUCT_CLASS") or "0").strip().lower()

# .heic/.heif are iPhone photos; .mov is the iPhone video format (H.264 or HEVC). Results are always .jpg or .mp4.
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
VIDEO_EXTENSIONS = {".mp4", ".mov"}

MAX_IMAGE_MB = 10
# A small file can still decode to a huge image (a "decompression bomb"): a 17 KB PNG can need 430 MB.
# The width x height is read from the file header before decoding. 100 MP covers 48 to 50 MP phone photos.
MAX_IMAGE_MEGAPIXELS = 100
MAX_VIDEO_MB = 100
MAX_VIDEO_SECONDS = 30

# Inference stops at 300 boxes by default, which undercounts packed shelves.
MAX_DETECTIONS = 1000

# Run detection on every Nth video frame; frames in between reuse the last result.
FRAME_STEP = 5

# Video frames wider than this are scaled down before detection and drawing. The model works at about
# 640 px anyway, and full 4K output is slow to process and too large to play smoothly in the page.
VIDEO_MAX_WIDTH = 1280

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
