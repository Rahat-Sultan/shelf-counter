# Product Requirements: Shelf Product Counter

Status: Draft v1 · Owner: intern project · Source: "Intern Project: Shelf Product Counter with Roboflow" (Oct 9, 2026)

## 1. Summary

A small web app. The user uploads a shelf photo or a short video. The app returns the same file with every product boxed, shows how many products were found, and lets the user download the result.

The app uses a pretrained model from Roboflow Universe. There is no data labeling and no model training in this project.

## 2. Goals and non-goals

### Goals

- Detect and count products on a retail shelf from a photo or a short video.
- Show the annotated result and the count on one page.
- Run locally on a laptop and be easy for a teammate to set up.

### Non-goals (out of scope)

- Labeling data or training a model.
- Live camera feeds.
- Identifying brands or specific products. The app counts items, it does not name them.
- Photos with people in them. Test and demo shots must be framed so no one is visible.
- Processing more than one file at a time.
- User accounts, saved history, or any server-side storage of results (see the database decision in `ARCHITECTURE.md`).

## 3. Users

| User | Need |
| --- | --- |
| Team member / reviewer | Upload a shelf photo or clip and quickly see a boxed, counted result |
| Teammate setting up the project | Follow the README and have the app running in under 10 minutes |

## 4. Functional requirements

Priority: **Must** = needed for "done", **Should** = clear value and cheap, **Could** = only if time allows.

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-1 | The user can upload one image in `.jpg` or `.png` format | Must |
| FR-2 | The user can upload one video in `.mp4` format, under 30 seconds | Must |
| FR-3 | Only one file is processed at a time | Must |
| FR-4 | The app runs the file through a pretrained Roboflow shelf model using Roboflow Inference | Must |
| FR-5 | The app draws a box on every detected product using Supervision | Must |
| FR-6 | The page shows the annotated image or video | Must |
| FR-7 | The page shows the total number of products found | Must |
| FR-8 | The user can download the annotated result | Must |
| FR-9 | For video, detection runs on every 5th frame. Frames in between reuse the most recent detections, so every frame has boxes and a count | Must |
| FR-10 | For video, the app reports a product count per frame | Must |
| FR-11 | Unsupported file types show a clear error message | Must |
| FR-12 | Files that are too large, or videos that are too long, show a clear error message | Must |
| FR-13 | Errors never show a raw stack trace to the user | Should |
| FR-14 | The user can adjust the confidence threshold with a slider | Could |
| FR-15 | The page shows processing time | Could |
| FR-16 | If no strong model is found, an open-vocabulary fallback (for example YOLO-World) can be used by typing what to find | Could |

## 5. Non-functional requirements

| ID | Requirement | How it is checked |
| --- | --- | --- |
| NFR-1 | A shelf photo returns an annotated image in under 5 seconds | Time 10 photos, record the slowest and the average |
| NFR-2 | A 10-second video returns an annotated video with a count per frame | Upload a 10-second clip and check the output |
| NFR-3 | A teammate can run the app from the README in under 10 minutes | Ask a teammate to follow the README without help |
| NFR-4 | The app runs locally on a laptop with Python 3.10 or newer | Run it on a laptop without a GPU |
| NFR-5 | The Roboflow API key is never committed to Git | `.env` is in `.gitignore`; only `.env.example` is committed |
| NFR-6 | Setup is reproducible | Package versions are pinned in `requirements.txt` |

## 6. Technology

| Tool | Used for |
| --- | --- |
| Roboflow Universe | Find and test a pretrained shelf model |
| Roboflow Inference | Run the model from Python |
| Supervision | Draw boxes, count detections, read and write video |
| Streamlit (or Gradio) | The upload page |
| Python 3.10+ | Everything else |

The starter code uses Streamlit. Gradio would also satisfy the brief.

## 7. Acceptance criteria ("done when")

- [ ] Uploading any shelf photo returns an annotated image in under 5 seconds.
- [ ] Uploading a 10-second video returns an annotated video with a count per frame.
- [ ] The app shows a clear error for unsupported files and for files that are too large.
- [ ] A teammate can run the app from the README in under 10 minutes.

## 8. Deliverables

- [ ] Code in a Git repo with a README covering setup, how to run, and which model ID was chosen and why.
- [ ] 5 example inputs and their annotated outputs (in `samples/`).
- [ ] A short demo to the team: upload a photo, upload a video, show the results.

## 9. Assumptions and decisions to confirm

| # | Item | Current decision |
| --- | --- | --- |
| A1 | The brief is titled both "Shelf Product Counter" and "Smart Shelf Monitor" | Treated as one project, named "Shelf Product Counter". Confirm with the project owner |
| A2 | The brief says "too large" without a number | Image limit 10 MB, video limit 100 MB. Adjust in `src/config.py` |
| A3 | `.jpeg` files | Accepted as an alias of `.jpg` |
| A4 | The video count is requested "per frame" but detection runs every 5th frame | Detection runs every 5th frame, last result reused in between, so each frame has a count |
| A5 | The headline count for a video | Highest per-frame count. Confirm, or switch to the average |
| A6 | Model names in the brief came from memory, not a live search | Decided after testing on 10 photos: use `planogram_sku110k/1` (trained on SKU-110K, one class `0`). It found 1,168 products against 692 for `retail-shelf-detection-peimi/1`. See `TESTING_AND_MODEL_SELECTION.md` |
| A7 | Where inference runs (local or hosted API) | Decided: local. 0.11 s per photo on a laptop CPU, well under the 5-second target |

## 10. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| No public shelf model on Universe performs well | High: everything depends on it | Test 2 or 3 candidates on 10 own photos; fall back to an open-vocabulary model |
| Inference is slower than 5 seconds on a laptop CPU | Medium: misses NFR-1 | Time early in Phase 2; try hosted inference; resize large images before detection |
| Dense shelves or glare cause missed products | Medium: lower accuracy | Tune confidence; document limits honestly in the README |
| Annotated video does not play in the browser | Medium: breaks the video demo | Test playback in Phase 4; re-encode with ffmpeg if needed |
| API key leaked in Git | High | `.env` in `.gitignore` from the first commit |
| The `inference` package is large and slow to install | Low | Warn in the README; pin versions |

## 11. Open questions for the project owner

1. Is "Shelf Product Counter" the correct project name?
2. What file size limits should the app enforce?
3. Should the video headline count be the maximum, the average, or the last frame?
4. Is a hosted Roboflow API acceptable, or must inference run fully offline on the laptop?
