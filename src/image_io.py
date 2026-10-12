"""Reading uploaded photos, including iPhone HEIC photos that OpenCV cannot open."""

from pathlib import Path

import cv2
import numpy as np
import pillow_heif
from PIL import Image, ImageOps

# Lets Pillow open .heic and .heif files (the default photo format on iPhones).
pillow_heif.register_heif_opener()

HEIF_EXTENSIONS = {".heic", ".heif"}


def is_heif(path: Path) -> bool:
    return path.suffix.lower() in HEIF_EXTENSIONS


def can_read_header(path: Path) -> bool:
    """True if the file looks like an image we can decode. Checks the signature only, without decoding.

    A text file renamed to .jpg fails here before any decoding is attempted.
    """
    if is_heif(path):
        return pillow_heif.is_supported(str(path))
    return cv2.haveImageReader(str(path))


def read_image(path: Path) -> np.ndarray | None:
    """Decodes a photo to a BGR array (OpenCV's layout), or None if it cannot be read.

    JPEG and PNG go through OpenCV, which also applies the EXIF rotation from phone cameras.
    HEIC goes through Pillow; exif_transpose applies the same rotation there.
    """
    if not is_heif(path):
        return cv2.imread(str(path))
    try:
        with Image.open(path) as img:
            rgb = ImageOps.exif_transpose(img).convert("RGB")
    except Exception:
        return None
    return cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
