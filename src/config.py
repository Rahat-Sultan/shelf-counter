import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "")
CONFIDENCE = float(os.getenv("CONFIDENCE", "0.3"))

# The chosen model (planogram_sku110k/1, trained on SKU-110K) has a single class named "0".
# Only boxes of this class are drawn and counted.
PRODUCT_CLASS = os.getenv("PRODUCT_CLASS", "0").lower()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4"}

MAX_IMAGE_MB = 10
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
