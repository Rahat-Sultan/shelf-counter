from __future__ import annotations

import logging
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import supervision as sv

from src import config
from src.annotator import Annotator
from src.errors import UserFacingError
from src.validator import UNREADABLE_IMAGE, UNREADABLE_VIDEO

if TYPE_CHECKING:
    # Type hints only: importing the detector imports inference, which is slow and is not needed
    # until the model is loaded.
    from src.detector import ShelfDetector

logger = logging.getLogger(__name__)


@dataclass
class Result:
    output_path: Path
    count: int
    per_frame_counts: list[int] = field(default_factory=list)
    seconds: float = 0.0
    fps: float = 0.0  # video only, used to plot counts against time
    note: str = ""  # something the user should know about an otherwise good result


class Processor(ABC):
    def __init__(
        self,
        detector: ShelfDetector,
        annotator: Annotator,
        confidence: float | None = None,
        output_dir: Path = config.OUTPUT_DIR,
    ):
        self.detector = detector
        self.annotator = annotator
        # Kept per processor so one cached detector can serve different slider values.
        self.confidence = confidence
        self.output_dir = output_dir

    @abstractmethod
    def process(self, path: Path) -> Result: ...


class ImageProcessor(Processor):
    def process(self, path: Path) -> Result:
        start = time.perf_counter()
        frame = cv2.imread(str(path))
        if frame is None:
            raise UserFacingError(UNREADABLE_IMAGE)
        detections = self.detector.detect(frame, self.confidence)
        annotated = self.annotator.annotate(frame, detections)
        out_path = self.output_dir / f"{path.stem}_annotated.jpg"
        cv2.imwrite(str(out_path), annotated)
        return Result(out_path, len(detections), [], time.perf_counter() - start)


def fit_width(width: int, height: int, max_width: int) -> tuple[int, int]:
    """Returns an even-sized (width, height) no wider than max_width, keeping the aspect ratio."""
    if width > max_width:
        height = height * max_width / width
        width = max_width
    # H.264 with yuv420p needs even dimensions.
    return int(width) // 2 * 2, int(round(height)) // 2 * 2


def encode_for_browser(src: Path, dst: Path) -> None:
    """Re-encodes src to H.264 at dst so browsers can play it.

    OpenCV can only write MPEG-4 Part 2 ("mp4v"), which most browsers will not play.
    Without ffmpeg the mp4v file is kept: it still downloads, but may not play in the page.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        logger.warning("ffmpeg not found; the annotated video may not play in the browser. See the README.")
        src.replace(dst)
        return
    try:
        subprocess.run(
            [
                ffmpeg, "-y", "-loglevel", "error", "-i", str(src),
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                "-movflags", "+faststart", "-an", str(dst),
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        # The mp4v file is still a valid result, so keep it rather than failing the whole upload.
        logger.warning("ffmpeg failed, keeping the mp4v video: %s", exc.stderr.decode(errors="replace").strip())
        src.replace(dst)
        return
    src.unlink()


class VideoProcessor(Processor):
    def __init__(
        self,
        *args,
        frame_step: int = config.FRAME_STEP,
        max_width: int = config.VIDEO_MAX_WIDTH,
        on_progress: Callable[[float], None] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.frame_step = frame_step
        self.max_width = max_width
        # Called with a fraction from 0 to 1 as frames are processed, for a progress bar.
        self.on_progress = on_progress

    def process(self, path: Path) -> Result:
        start = time.perf_counter()
        info = sv.VideoInfo.from_video_path(str(path))
        size = fit_width(info.width, info.height, self.max_width)
        raw_path = self.output_dir / f"{path.stem}_mp4v.mp4"
        out_path = self.output_dir / f"{path.stem}_annotated.mp4"
        counts: list[int] = []
        last = sv.Detections.empty()

        with sv.VideoSink(str(raw_path), sv.VideoInfo(width=size[0], height=size[1], fps=info.fps)) as sink:
            for i, frame in enumerate(sv.get_video_frames_generator(str(path))):
                if (frame.shape[1], frame.shape[0]) != size:
                    frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
                if i % self.frame_step == 0:
                    last = self.detector.detect(frame, self.confidence)
                counts.append(len(last))
                sink.write_frame(self.annotator.annotate(frame, last))
                if self.on_progress and info.total_frames:
                    self.on_progress(min(1.0, (i + 1) / info.total_frames))

        if not counts:
            raise UserFacingError(UNREADABLE_VIDEO)
        encode_for_browser(raw_path, out_path)
        note = ""
        if info.total_frames and len(counts) < 0.9 * info.total_frames:
            note = (
                f"Only {len(counts)} of {info.total_frames} frames could be read. "
                "The file may be incomplete, so the results cover only the readable part."
            )
        # Headline count for a video is the highest per-frame count (PRD assumption A5).
        return Result(out_path, max(counts), counts, time.perf_counter() - start, info.fps, note)
