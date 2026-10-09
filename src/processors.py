import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import supervision as sv

from src import config
from src.annotator import Annotator
from src.detector import ShelfDetector


@dataclass
class Result:
    output_path: Path
    count: int
    per_frame_counts: list[int] = field(default_factory=list)
    seconds: float = 0.0


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
        detections = self.detector.detect(frame, self.confidence)
        annotated = self.annotator.annotate(frame, detections)
        out_path = self.output_dir / f"{path.stem}_annotated.jpg"
        cv2.imwrite(str(out_path), annotated)
        return Result(out_path, len(detections), [], time.perf_counter() - start)


class VideoProcessor(Processor):
    def __init__(self, *args, frame_step: int = config.FRAME_STEP, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_step = frame_step

    def process(self, path: Path) -> Result:
        start = time.perf_counter()
        info = sv.VideoInfo.from_video_path(str(path))
        out_path = self.output_dir / f"{path.stem}_annotated.mp4"
        counts: list[int] = []
        last = sv.Detections.empty()

        with sv.VideoSink(str(out_path), info) as sink:
            for i, frame in enumerate(sv.get_video_frames_generator(str(path))):
                if i % self.frame_step == 0:
                    last = self.detector.detect(frame, self.confidence)
                counts.append(len(last))
                sink.write_frame(self.annotator.annotate(frame, last))

        return Result(out_path, max(counts, default=0), counts, time.perf_counter() - start)
