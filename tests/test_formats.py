"""iPhone formats: .heic photos and .mov videos (H.264 and HEVC)."""

import shutil
import subprocess

import numpy as np
import pytest
import supervision as sv
from PIL import Image

from src.annotator import Annotator
from src.image_io import read_image
from src.processors import ImageProcessor, VideoProcessor
from src.validator import UNREADABLE_IMAGE, validate


class OneBox:
    def detect(self, frame, confidence=None):
        return sv.Detections(xyxy=np.array([[1, 1, 10, 10]], dtype=float), class_id=np.array([0]))


def save_heic(path, size=(80, 40), orientation=None):
    img = Image.new("RGB", size, (200, 30, 30))
    exif = Image.Exif()
    if orientation:
        exif[0x0112] = orientation  # EXIF Orientation, as phone cameras write it
    img.save(path, exif=exif.tobytes())


def test_accepts_and_reads_heic(tmp_path):
    f = tmp_path / "IMG_0001.HEIC"
    save_heic(f)
    assert validate(f).kind == "image"
    frame = read_image(f)
    assert frame.shape == (40, 80, 3)
    assert frame[0, 0].tolist() == [30, 30, 200]  # BGR, like OpenCV


def test_heic_rotation_from_camera_is_applied(tmp_path):
    f = tmp_path / "portrait.heic"
    save_heic(f, size=(80, 40), orientation=6)  # 6 = rotate 90 degrees, a phone held upright
    assert read_image(f).shape[:2] == (80, 40)


def test_heic_counts_and_gives_a_jpeg(tmp_path):
    f = tmp_path / "shelf.heic"
    save_heic(f)
    result = ImageProcessor(OneBox(), Annotator(), output_dir=tmp_path).process(f)
    assert result.count == 1
    assert result.output_path.name == "shelf_annotated.jpg"


def test_rejects_text_renamed_to_heic(tmp_path):
    f = tmp_path / "notes.heic"
    f.write_text("not a photo")
    assert validate(f).message == UNREADABLE_IMAGE


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
@pytest.mark.parametrize("codec", ["libx264", "libx265"])
def test_mov_from_iphone_codecs_gives_h264_mp4(tmp_path, codec):
    encoders = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if codec not in encoders:
        pytest.skip(f"ffmpeg has no {codec}")
    f = tmp_path / "IMG_0002.MOV"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=10", "-t", "2",
         "-c:v", codec, "-pix_fmt", "yuv420p", str(f)],
        check=True,
    )
    assert validate(f).kind == "video"
    result = VideoProcessor(OneBox(), Annotator(), output_dir=tmp_path).process(f)
    assert len(result.per_frame_counts) == 20
    assert result.output_path.suffix == ".mp4"
