import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "")
MODEL_ID = os.getenv("MODEL_ID", "")
CONFIDENCE = float(os.getenv("CONFIDENCE", "0.4"))

# The chosen model has two classes: "product" and "empty" (empty shelf space).
# Only boxes of this class are drawn and counted.
PRODUCT_CLASS = os.getenv("PRODUCT_CLASS", "product").lower()

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
VIDEO_EXTENSIONS = {".mp4"}

MAX_IMAGE_MB = 10
MAX_VIDEO_MB = 100
MAX_VIDEO_SECONDS = 30

# Run detection on every Nth video frame; frames in between reuse the last result.
FRAME_STEP = 5

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
