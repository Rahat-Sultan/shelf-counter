# Testing and Model Selection

## 1. Test data

Collect before Phase 1:

- 10 shelf photos, no people in frame.
- 3 or more short videos, 10 to 25 seconds, no people in frame.

Make the photos varied so the comparison is fair:

| Factor | Include |
| --- | --- |
| Density | Sparse shelf, medium shelf, packed shelf |
| Lighting | Bright, dim, mixed with glare |
| Angle | Straight on, slightly from the side |
| Product type | Boxes, bottles, cans, bags |
| Distance | Close up, full aisle |

Keep a small spreadsheet or table listing each photo, its conditions, and the true product count you counted by eye. Do not change the true counts after seeing model results.

## 2. Model selection method

1. Shortlist 2 or 3 public models on Roboflow Universe (search "retail shelf", "SKU-110K", "shelf products").
2. Only keep projects with a trained model attached. Many are datasets only.
3. Test each in the browser on 2 or 3 photos for a quick sanity check.
4. Run each remaining candidate on all 10 photos at the same confidence threshold.
5. Record the counts in the table below.
6. Choose the model with the lowest total missed products. Break ties with false boxes, then speed.
7. Write the winning model ID and the reasoning in the README.

### Comparison table template

True count is what you counted by eye. Missed = true count minus correct boxes. Extra = boxes that are not real products.

| Photo | Conditions | True count | Model A found | A missed | A extra | Model B found | B missed | B extra | Model C found | C missed | C extra |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | | | | | | | | | | | |
| 2 | | | | | | | | | | | |
| 3 | | | | | | | | | | | |
| 4 | | | | | | | | | | | |
| 5 | | | | | | | | | | | |
| 6 | | | | | | | | | | | |
| 7 | | | | | | | | | | | |
| 8 | | | | | | | | | | | |
| 9 | | | | | | | | | | | |
| 10 | | | | | | | | | | | |
| Total | | | | | | | | | | | |
| Avg seconds per image | | | | | | | | | | | |

Decision: Model ____ (ID: `project-name/version`) because ____.

### First run (2026-10-09), before true counts

Boxes found at confidence 0.4 on the 10 test photos (`python -m scripts.evaluate`). True counts are still to be added to `test_images/true_counts.csv`.

| Model | Total found | Avg seconds | Notes |
| --- | --- | --- | --- |
| A: `retail-shelf-detection-peimi/1` | 692 | 0.05 | Skips whole shelf sections; 14 boxes on the snack stand, 1 on the convenience-store photo |
| B: `planogram_sku110k/1` (class `0`) | 1,168 | 0.10 | Boxes items individually across full shelves; weak only on very small photos |
| C: `shelf-product/1` | not run | | Classes are specific coffee brands, not generic products |

Chosen: **B, `planogram_sku110k/1`**, because it found far more real products on every dense shelf, confirmed by checking the annotated images by eye.

### Fallback

If no candidate performs acceptably, use an open-vocabulary model that Roboflow Inference can run (for example YOLO-World). You type what to find ("bottle", "box") and it detects it with no training. Confirm what is currently available before relying on it.

## 3. Functional test matrix

| # | Test | Expected result |
| --- | --- | --- |
| T1 | Upload a normal `.jpg` shelf photo | Boxes drawn, count shown, download works |
| T2 | Upload a `.png` shelf photo | Same as T1 |
| T3 | Upload a 10-second `.mp4` | Annotated video plays, per-frame counts shown, download works |
| T4 | Upload a `.pdf` | Message: unsupported file type |
| T5 | Upload a renamed `.txt` file as `.jpg` | Clear message that the file could not be read |
| T6 | Upload an image over the size limit | Message: file too large, with the limit |
| T7 | Upload a video over 30 seconds | Message: video too long, with the limit |
| T8 | Upload a video over the size limit | Message: file too large, with the limit |
| T9 | Upload a blank or very dark photo | Count of 0, no crash |
| T10 | Start the app with no API key | Clear message about the missing key |
| T11 | Upload two files one after another | Each processed independently, no leftover results |
| T12 | Upload the same file twice | Same result both times |

Automated tests live in `tests/`. Run them with `pytest`. Currently covered: unsupported type, small image accepted, oversized image rejected. Add video-length tests once you have sample clips.

## 4. Performance checks

| Check | Target | How |
| --- | --- | --- |
| Image processing time | Under 5 seconds | Time 10 photos after the model is loaded; record average and slowest |
| First-run model load | Note it | Measure separately; it is a one-time warm-up cost |
| 10-second video | Completes with a count for every frame | Time the full run; note frames per second |
| Memory | No crash on the largest allowed video | Run with a 100 MB, 30-second clip |

Record results here:

| Date | Machine | Model ID | Avg image seconds | Slowest image | 10 s video seconds |
| --- | --- | --- | --- | --- | --- |
| 2026-10-09 | Intel i5-8350U laptop, CPU only | `planogram_sku110k/1` @ 0.3 | 0.11 | 0.13 | |

If images are slower than 5 seconds: resize large photos before detection, check that the model is cached, or try hosted inference.

## 5. Sample set (deliverable)

Save 5 input and output pairs in `samples/inputs/` and `samples/outputs/`. Pick a mix:

1. A clean, easy shelf (shows it working well).
2. A packed shelf (shows count accuracy under density).
3. A glare or low-light photo (shows a limit).
4. A short video clip (shows the video path).
5. One more typical case, or a failure you want to explain honestly.

Name pairs consistently, for example `01_clean_shelf.jpg` and `01_clean_shelf_annotated.jpg`.

## 6. Demo script (3 to 5 minutes)

1. State the goal in one sentence: upload a shelf photo or clip, get it back boxed and counted.
2. Upload a photo. Point out the boxes, the count and the processing time. Download the result.
3. Upload a video. Show the annotated playback and the per-frame count chart.
4. Show one error: upload a `.pdf` and show the message.
5. Say which model you chose and why, with one number from your comparison table.
6. Mention one honest limitation (for example dense shelves or glare).

## 7. Pre-demo checklist

- [ ] App starts from a clean clone following only the README.
- [ ] `.env` is not in Git.
- [ ] Model is cached so the first demo upload is not slow (run one upload beforehand).
- [ ] Demo photo and video are ready and contain no people.
- [ ] All acceptance criteria in `PRD.md` are ticked.
