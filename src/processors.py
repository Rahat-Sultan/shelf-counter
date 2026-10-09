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
    def __init__(self, detector: ShelfDetector, annotator: Annotator):
        self.detector = detector
        self.annotator = annotator

    @abstractmethod
    def process(self, path: Path) -> Result: ...


class ImageProcessor(Processor):
    def process(self, path: Path) -> Result:
        start = time.perf_counter()
        frame = cv2.imread(str(path))
        detections = self.detector.detect(frame)
        annotated = self.annotator.annotate(frame, detections)
        out_path = config.OUTPUT_DIR / f"{path.stem}_annotated.jpg"
        cv2.imwrite(str(out_path), annotated)
        return Result(out_path, len(detections), [], time.perf_counter() - start)


class VideoProcessor(Processor):
    def __init__(self, detector, annotator, frame_step: int = config.FRAME_STEP):
        super().__init__(detector, annotator)
        self.frame_step = frame_step

    def process(self, path: Path) -> Result:
        start = time.perf_counter()
        info = sv.VideoInfo.from_video_path(str(path))
        out_path = config.OUTPUT_DIR / f"{path.stem}_annotated.mp4"
        counts: list[int] = []
        last = sv.Detections.empty()

        with sv.VideoSink(str(out_path), info) as sink:
            for i, frame in enumerate(sv.get_video_frames_generator(str(path))):
                if i % self.frame_step == 0:
                    last = self.detector.detect(frame)
                counts.append(len(last))
                sink.write_frame(self.annotator.annotate(frame, last))

        return Result(out_path, max(counts, default=0), counts, time.perf_counter() - start)
