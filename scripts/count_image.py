"""Phase 2: box and count the products in one or more shelf photos.

Example:
    python -m scripts.count_image ../test_images/images8.jpeg
    python -m scripts.count_image ../test_images/*.jpeg --confidence 0.3

Annotated images are saved to outputs/<name>_annotated.jpg.
"""

import argparse
import time
from pathlib import Path

from src import config
from src.annotator import Annotator
from src.detector import ShelfDetector
from src.processors import ImageProcessor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--confidence", type=float, default=config.CONFIDENCE)
    args = parser.parse_args()

    start = time.perf_counter()
    detector = ShelfDetector(config.MODEL_ID, config.ROBOFLOW_API_KEY, args.confidence)
    print(f"Model {config.MODEL_ID} loaded in {time.perf_counter() - start:.1f}s (confidence {args.confidence})")

    processor = ImageProcessor(detector, Annotator())
    for path in args.images:
        result = processor.process(path)
        print(f"{path.name}: {result.count} products in {result.seconds:.2f}s -> {result.output_path}")


if __name__ == "__main__":
    main()
