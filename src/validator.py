from dataclasses import dataclass
from pathlib import Path

import cv2

from src import config


@dataclass
class ValidationResult:
    ok: bool
    kind: str | None = None  # "image" or "video"
    message: str = ""


def video_duration_seconds(path: Path) -> float:
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return frames / fps if fps else 0.0


def validate(path: str | Path) -> ValidationResult:
    path = Path(path)
    ext = path.suffix.lower()
    size_mb = path.stat().st_size / (1024 * 1024)

    if ext in config.IMAGE_EXTENSIONS:
        if size_mb > config.MAX_IMAGE_MB:
            return ValidationResult(
                False, message=f"Image is {size_mb:.1f} MB. The limit is {config.MAX_IMAGE_MB} MB."
            )
        return ValidationResult(True, kind="image")

    if ext in config.VIDEO_EXTENSIONS:
        if size_mb > config.MAX_VIDEO_MB:
            return ValidationResult(
                False, message=f"Video is {size_mb:.1f} MB. The limit is {config.MAX_VIDEO_MB} MB."
            )
        duration = video_duration_seconds(path)
        if duration == 0:
            return ValidationResult(False, message="This video could not be read. Try another .mp4 file.")
        if duration > config.MAX_VIDEO_SECONDS:
            return ValidationResult(
                False,
                message=f"Video is {duration:.0f} seconds long. The limit is {config.MAX_VIDEO_SECONDS} seconds.",
            )
        return ValidationResult(True, kind="video")

    return ValidationResult(False, message="Unsupported file type. Please upload a .jpg, .png or .mp4 file.")
