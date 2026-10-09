import importlib
import os
import subprocess
import sys

import dotenv
import numpy as np
import pytest
import requests
from inference.core.exceptions import RoboflowAPIConnectionError, RoboflowAPINotNotFoundError
from inference_models.errors import ForbiddenModelAccessError

from src import config
from src.errors import UserFacingError, friendly_message
from src.processors import ImageProcessor
from src.validator import UNREADABLE_IMAGE, UNREADABLE_VIDEO, validate


def load_config(monkeypatch, env_file: dict):
    """Re-imports src.config as if .env contained env_file, with no real environment overrides."""
    monkeypatch.setattr(dotenv, "dotenv_values", lambda *a, **k: env_file)
    for name in ("ROBOFLOW_API_KEY", "MODEL_ID", "CONFIDENCE", "PRODUCT_CLASS"):
        monkeypatch.delenv(name, raising=False)
    return importlib.reload(config)


@pytest.fixture(autouse=True)
def restore_config():
    yield
    importlib.reload(config)


@pytest.mark.parametrize(
    "raw, expected, warns",
    [("0.5", 0.5, False), ("abc", 0.3, True), ("1.5", 0.95, True), ("0", 0.05, True), ("", 0.3, False)],
)
def test_confidence_from_env_file_never_crashes(monkeypatch, raw, expected, warns):
    cfg = load_config(monkeypatch, {"CONFIDENCE": raw})
    assert cfg.CONFIDENCE == expected
    assert bool(cfg.WARNINGS) == warns


def test_env_file_is_not_exported_to_the_environment(monkeypatch):
    load_config(monkeypatch, {"CONFIDENCE": "abc", "ROBOFLOW_API_KEY": "secret"})
    assert "CONFIDENCE" not in os.environ
    assert "ROBOFLOW_API_KEY" not in os.environ


def test_real_environment_overrides_env_file(monkeypatch):
    monkeypatch.setattr(dotenv, "dotenv_values", lambda *a, **k: {"MODEL_ID": "from-file/1"})
    monkeypatch.setenv("MODEL_ID", "from-env/2")
    assert importlib.reload(config).MODEL_ID == "from-env/2"


def test_inference_rejects_bad_confidence_in_environment():
    """Documents why .env must not be exported: inference itself parses CONFIDENCE on import."""
    result = subprocess.run(
        [sys.executable, "-c", "import inference.core.env"],
        env={**os.environ, "CONFIDENCE": "abc"},
        capture_output=True,
    )
    assert result.returncode != 0


@pytest.mark.parametrize(
    "exc, expected",
    [
        (UserFacingError("Shown as is."), "Shown as is."),
        (ForbiddenModelAccessError("403"), "rejected the API key"),
        (RoboflowAPINotNotFoundError("404"), "could not find the model"),
        (RoboflowAPIConnectionError("down"), "internet connection"),
        (requests.exceptions.ConnectionError("down"), "internet connection"),
        (RuntimeError("Traceback (most recent call last): secret details"), "Something went wrong"),
    ],
)
def test_friendly_message(exc, expected):
    message = friendly_message(exc)
    assert expected in message
    assert "Traceback" not in message


def test_rejects_empty_file(tmp_path):
    f = tmp_path / "empty.jpg"
    f.write_bytes(b"")
    assert "empty" in validate(f).message


def test_rejects_text_file_renamed_to_jpg(tmp_path):
    f = tmp_path / "notes.jpg"
    f.write_text("this is not an image")
    assert validate(f).message == UNREADABLE_IMAGE


def test_rejects_text_file_renamed_to_mp4(tmp_path):
    f = tmp_path / "notes.mp4"
    f.write_text("this is not a video")
    assert validate(f).message == UNREADABLE_VIDEO


def test_image_that_passes_signature_but_cannot_decode(tmp_path):
    f = tmp_path / "broken.jpg"
    f.write_bytes(b"\xff\xd8\xff" + b"\x00" * 100)
    with pytest.raises(UserFacingError, match="could not be read"):
        ImageProcessor(detector=None, annotator=None, output_dir=tmp_path).process(f)


def test_blank_image_gives_zero_without_crashing(tmp_path):
    import cv2
    import supervision as sv

    class NoProducts:
        def detect(self, frame, confidence=None):
            return sv.Detections.empty()

    from src.annotator import Annotator

    f = tmp_path / "blank.png"
    cv2.imwrite(str(f), np.full((100, 100, 3), 255, np.uint8))
    assert ImageProcessor(NoProducts(), Annotator(), output_dir=tmp_path).process(f).count == 0
