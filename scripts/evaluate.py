"""Phase 1/2: run one or more models on a folder of shelf photos and compare them.

Example:
    python -m scripts.evaluate --images ../test_images --truth ../test_images/true_counts.csv
    python -m scripts.evaluate --images ../test_images --models retail-shelf-detection-peimi/1 planogram_sku110k/1=0 \
        --confidence 0.3 0.4 0.5

A model can be given as ID=CLASS to count a class other than PRODUCT_CLASS (for example "planogram_sku110k/1=0").

Writes annotated copies to outputs/eval/<model>_c<confidence>/ and a results.csv next to them.
"""

import argparse
import csv
import statistics
import time
from pathlib import Path

import cv2

from src import config
from src.annotator import Annotator
from src.detector import ShelfDetector


def load_truth(path: Path | None) -> dict[str, int]:
    if path is None or not path.exists():
        return {}
    with path.open(newline="") as f:
        return {
            row["filename"]: int(row["true_count"])
            for row in csv.DictReader(f)
            if row.get("true_count", "").strip()
        }


def write_truth_template(path: Path, images: list[Path]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "true_count", "conditions"])
        for img in images:
            writer.writerow([img.name, "", ""])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images", type=Path, required=True, help="folder of .jpg/.jpeg/.png photos")
    parser.add_argument(
        "--models", nargs="+", default=[config.MODEL_ID], help="Roboflow model IDs to compare, optionally ID=CLASS"
    )
    parser.add_argument("--confidence", nargs="+", type=float, default=[config.CONFIDENCE])
    parser.add_argument("--truth", type=Path, help="CSV with filename,true_count (template is created if missing)")
    parser.add_argument("--out", type=Path, default=config.OUTPUT_DIR / "eval")
    args = parser.parse_args()

    images = sorted(p for p in args.images.iterdir() if p.suffix.lower() in config.IMAGE_EXTENSIONS)
    if not images:
        raise SystemExit(f"No images found in {args.images}")

    if args.truth and not args.truth.exists():
        write_truth_template(args.truth, images)
        print(f"Created {args.truth}. Fill in true_count by eye, then run again.\n")
    truth = load_truth(args.truth)

    annotator = Annotator()
    rows = []
    model_ids = [spec.split("=")[0] for spec in args.models]
    for spec in args.models:
        model_id, _, product_class = spec.partition("=")
        load_start = time.perf_counter()
        detector = ShelfDetector(model_id, config.ROBOFLOW_API_KEY, product_class=product_class or config.PRODUCT_CLASS)
        print(f"{model_id}: loaded in {time.perf_counter() - load_start:.1f}s")
        detector.detect(cv2.imread(str(images[0])))  # warm-up, excluded from timings

        for conf in args.confidence:
            detector.confidence = conf
            run_dir = args.out / f"{model_id.replace('/', '_')}_c{conf}"
            run_dir.mkdir(parents=True, exist_ok=True)
            for img in images:
                frame = cv2.imread(str(img))
                start = time.perf_counter()
                detections = detector.detect(frame)
                seconds = time.perf_counter() - start
                cv2.imwrite(str(run_dir / f"{img.stem}_annotated.jpg"), annotator.annotate(frame, detections))
                true = truth.get(img.name)
                rows.append(
                    {
                        "model": model_id,
                        "confidence": conf,
                        "filename": img.name,
                        "width": frame.shape[1],
                        "height": frame.shape[0],
                        "true_count": "" if true is None else true,
                        "found": len(detections),
                        "difference": "" if true is None else len(detections) - true,
                        "seconds": round(seconds, 3),
                    }
                )

    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "results.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("\n| Model | Conf | Photo | Size | True | Found | Diff | Seconds |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        print(
            f"| {r['model']} | {r['confidence']} | {r['filename']} | {r['width']}x{r['height']} "
            f"| {r['true_count']} | {r['found']} | {r['difference']} | {r['seconds']:.3f} |"
        )

    print("\nSummary")
    for model_id in model_ids:
        for conf in args.confidence:
            run = [r for r in rows if r["model"] == model_id and r["confidence"] == conf]
            times = [r["seconds"] for r in run]
            line = (
                f"  {model_id} @ {conf}: found {sum(r['found'] for r in run)} products, "
                f"avg {statistics.mean(times):.3f}s, slowest {max(times):.3f}s"
            )
            scored = [r for r in run if r["true_count"] != ""]
            if scored:
                abs_err = sum(abs(r["difference"]) for r in scored)
                line += f", total |count error| {abs_err} over {len(scored)} photos"
            print(line)
    print(f"\nAnnotated images and results.csv in {args.out}")


if __name__ == "__main__":
    main()
