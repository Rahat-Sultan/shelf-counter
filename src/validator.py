from dataclasses import dataclass
from pathlib import Path

import cv2
from PIL import Image

from src import config
from src.image_io import can_read_header


@dataclass
class ValidationResult:
    ok: bool
    kind: str | None = None  # "image" or "video"
    message: str = ""


UNREADABLE_IMAGE = (
    "This file could not be read as an image. It may be damaged, or not really a .jpg, .png or .heic file."
)
UNREADABLE_VIDEO = "This video could not be read. It may be damaged or incomplete. Try another .mp4 or .mov file."
UNSUPPORTED = "Unsupported file type. Please upload a photo (.jpg, .png, .heic) or a video (.mp4, .mov)."


def image_megapixels(path: Path) -> float | None:
    """Width x height in megapixels, read from the file header without decoding the image.

    Returns None if the header cannot be read, and infinity if Pillow itself refuses the image as a
    decompression bomb (above about 179 MP), which is far over our limit anyway.
    """
    try:
        with Image.open(path) as img:
            width, height = img.size
    except Image.DecompressionBombError:
        return float("inf")
    except Exception:
        return None
    return width * height / 1_000_000


def video_duration_seconds(path: Path) -> float:
    """Duration from the file's metadata, or 0.0 if the video has no readable frame."""
    cap = cv2.VideoCapture(str(path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        # Truncated files can report a duration but contain no decodable frames.
        readable, _ = cap.read()
    finally:
        cap.release()
    return frames / fps if fps and readable else 0.0


def validate(path: str | Path) -> ValidationResult:
    path = Path(path)
    ext = path.suffix.lower()
    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if ext in config.IMAGE_EXTENSIONS | config.VIDEO_EXTENSIONS and size_bytes == 0:
        return ValidationResult(False, message="The file is empty. Please upload a shelf photo or video.")

    if ext in config.IMAGE_EXTENSIONS:
        if size_mb > config.MAX_IMAGE_MB:
            return ValidationResult(
                False, message=f"Image is {size_mb:.1f} MB. The limit is {config.MAX_IMAGE_MB} MB."
            )
        if not can_read_header(path):
            return ValidationResult(False, message=UNREADABLE_IMAGE)
        megapixels = image_megapixels(path)
        if megapixels is None:
            return ValidationResult(False, message=UNREADABLE_IMAGE)
        if megapixels > config.MAX_IMAGE_MEGAPIXELS:
            return ValidationResult(
                False,
                message=f"Image is {f'{megapixels:.0f}' if megapixels != float('inf') else 'over 179'} megapixels. "
                f"The limit is {config.MAX_IMAGE_MEGAPIXELS} megapixels.",
            )
        return ValidationResult(True, kind="image")

    if ext in config.VIDEO_EXTENSIONS:
        if size_mb > config.MAX_VIDEO_MB:
            return ValidationResult(
                False, message=f"Video is {size_mb:.1f} MB. The limit is {config.MAX_VIDEO_MB} MB."
            )
        duration = video_duration_seconds(path)
        if duration == 0:
            return ValidationResult(False, message=UNREADABLE_VIDEO)
        if duration > config.MAX_VIDEO_SECONDS:
            return ValidationResult(
                False,
                message=f"Video is {duration:.1f} seconds long. The limit is {config.MAX_VIDEO_SECONDS} seconds.",
            )
        return ValidationResult(True, kind="video")

    return ValidationResult(False, message=UNSUPPORTED)
