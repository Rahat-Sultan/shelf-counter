import cv2
import numpy as np

from src.validator import validate


def test_rejects_unsupported_type(tmp_path):
    f = tmp_path / "notes.pdf"
    f.write_bytes(b"%PDF-1.4")
    result = validate(f)
    assert not result.ok
    assert "Unsupported" in result.message


def test_accepts_small_image(tmp_path):
    f = tmp_path / "shelf.jpg"
    cv2.imwrite(str(f), np.zeros((40, 60, 3), np.uint8))
    result = validate(f)
    assert result.ok
    assert result.kind == "image"


def test_rejects_oversized_image(tmp_path):
    f = tmp_path / "huge.png"
    f.write_bytes(b"0" * (11 * 1024 * 1024))
    result = validate(f)
    assert not result.ok
