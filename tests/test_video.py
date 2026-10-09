import shutil
import subprocess

import cv2
import numpy as np
import pytest
import supervision as sv

from src.annotator import Annotator
from src.processors import VideoProcessor, encode_for_browser, fit_width
from src.validator import validate


def write_video(path, seconds, fps=10, size=(64, 48)):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    for _ in range(int(seconds * fps)):
        writer.write(np.zeros((size[1], size[0], 3), np.uint8))
    writer.release()


class FakeDetector:
    """Returns one box per call and records how often it was called."""

    def __init__(self):
        self.calls = 0

    def detect(self, frame, confidence=None):
        self.calls += 1
        return sv.Detections(xyxy=np.array([[1, 1, 10, 10]], dtype=float), class_id=np.array([0]))


def test_fit_width_scales_down_and_keeps_even_size():
    assert fit_width(3840, 2160, 1280) == (1280, 720)
    assert fit_width(1001, 601, 1280) == (1000, 600)
    assert fit_width(1920, 1081, 1280) == (1280, 720)


def test_accepts_short_video(tmp_path):
    f = tmp_path / "short.mp4"
    write_video(f, seconds=2)
    assert validate(f).kind == "video"


def test_rejects_long_video(tmp_path):
    f = tmp_path / "long.mp4"
    write_video(f, seconds=31)
    result = validate(f)
    assert not result.ok
    assert "30 seconds" in result.message


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_video_has_a_count_for_every_frame_and_plays_in_browsers(tmp_path):
    f = tmp_path / "clip.mp4"
    write_video(f, seconds=2)
    detector = FakeDetector()

    result = VideoProcessor(detector, Annotator(), output_dir=tmp_path, frame_step=5).process(f)

    assert result.per_frame_counts == [1] * 20
    assert detector.calls == 4  # every 5th of 20 frames
    codec = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name",
         "-of", "csv=p=0", str(result.output_path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert codec == "h264"
    assert not (tmp_path / "clip_mp4v.mp4").exists()


def test_encode_without_ffmpeg_keeps_the_mp4v_file(tmp_path, monkeypatch):
    src, dst = tmp_path / "raw.mp4", tmp_path / "out.mp4"
    write_video(src, seconds=1)
    monkeypatch.setattr(shutil, "which", lambda _: None)
    encode_for_browser(src, dst)
    assert dst.exists() and not src.exists()
