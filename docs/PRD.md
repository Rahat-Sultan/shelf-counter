# Product requirements: Shelf Product Counter

Status: **v2, built and live** (12 October 2026) · Owner: intern project · Source brief: "Intern Project: Shelf
Product Counter with Roboflow" (9 October 2026) · Live app: https://shelf-counter-rahat.streamlit.app (private)

| Version | Date | Change |
| --- | --- | --- |
| v1 | 9 Oct 2026 | Draft from the brief: FR-1 to FR-16, NFR-1 to NFR-6, assumptions A1 to A7 |
| v2 | 12 Oct 2026 | Status of every requirement, measured results, phone and hosting requirements (FR-17 to FR-24, NFR-7 to NFR-11), decisions made, updated risks |

How the system is built is described in [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md); this document
says **what** it must do and whether it does.

## 1. Summary

A small web app for counting products on retail shelves. The user gives it a shelf photo, a short video, or a
photo taken with the camera in the page. The app returns the same picture with every product boxed, shows how many
products it found, and lets the user download the result. It works in a laptop browser and on a phone.

The app uses a pretrained model from Roboflow Universe. There is no data labelling and no model training.

![A photo counted on a laptop](images/13_ui_desktop_photo_result.png)

## 2. Problem and context

Counting products on a shelf by hand is slow and error-prone, especially on packed shelves. The brief asks for a
simple tool that shows how far a ready-made detection model can take this, without the cost of collecting and
labelling data. The result is a demo and a working tool for the team, not a store system.

## 3. Goals and non-goals

### Goals

- Detect and count products on a retail shelf from a photo or a short video.
- Show the annotated result and the count on one page, with a download.
- Run locally on a laptop and be easy for a teammate to set up.
- Work on a phone, including taking the photo with the phone camera (added 12 October).
- Be reachable online through a private link (added 12 October).

### Non-goals (out of scope)

- Labelling data or training a model.
- Live camera feeds (a single camera photo is in scope; a continuous stream is not).
- Identifying brands or specific products. The app counts items; it does not name them.
- Photos with people in them. Test and demo shots must be framed so no one is visible.
- Processing more than one file at a time.
- User accounts, saved history, or server-side storage of results.
- A separate native mobile app (considered in [MOBILE_PLAN.md](MOBILE_PLAN.md), options B and C; not planned).

## 4. Users and scenarios

| User | Need | Scenario |
| --- | --- | --- |
| Team member or reviewer | See a boxed, counted result quickly | Opens the private link on a laptop, uploads a shelf photo, reads the count, downloads the result |
| Person at a shelf with a phone | Count without moving files around | Opens the link on the phone, selects **Take a photo** (or the upload box's camera), photographs the shelf |
| Teammate setting up the project | Run it locally from the README in under 10 minutes | Follows [STARTUP.md](../STARTUP.md): venv, install, `.env`, `streamlit run app.py` |
| Developer extending it | Understand and change the code safely | Reads PROJECT_DOCUMENTATION.md, runs `pytest -q`, works on the `develop` branch |

## 5. Functional requirements

Priority: **Must** = needed for "done", **Should** = clear value and cheap, **Could** = only if time allows.
Status: **Done**, **Not done** or **Not needed**, with where it is implemented.

### From the brief

| ID | Requirement | Priority | Status | Where |
| --- | --- | --- | --- | --- |
| FR-1 | The user can upload one image in `.jpg` or `.png` format | Must | Done (also `.jpeg`, and `.heic`/`.heif`, see FR-18) | `config.IMAGE_EXTENSIONS`, `validator.py` |
| FR-2 | The user can upload one video in `.mp4` format, under 30 seconds | Must | Done (also `.mov`, see FR-19) | `config.VIDEO_EXTENSIONS`, `validator.py` |
| FR-3 | Only one file is processed at a time | Must | Done | `app.py` (single uploader) |
| FR-4 | The app runs the file through a pretrained Roboflow shelf model using Roboflow Inference | Must | Done: `planogram_sku110k/1`, run locally on the CPU | `detector.py` |
| FR-5 | The app draws a box on every detected product using Supervision | Must | Done | `annotator.py` |
| FR-6 | The page shows the annotated image or video | Must | Done | `app.py` |
| FR-7 | The page shows the total number of products found | Must | Done (on the page and on the image) | `app.py`, `annotator.py` |
| FR-8 | The user can download the annotated result | Must | Done (JPEG or H.264 MP4; plus CSV for video) | `app.py` |
| FR-9 | For video, detection runs on every 5th frame; frames in between reuse the most recent detections | Must | Done | `processors.VideoProcessor` |
| FR-10 | For video, the app reports a product count per frame | Must | Done: chart and CSV download | `app.py` |
| FR-11 | Unsupported file types show a clear error message | Must | Done | `validator.py` |
| FR-12 | Files that are too large, or videos that are too long, show a clear error message | Must | Done, with the limit in the message | `validator.py` |
| FR-13 | Errors never show a raw stack trace to the user | Should | Done | `errors.friendly_message()` |
| FR-14 | The user can adjust the confidence threshold with a slider | Could | Done, in **Detection settings** | `app.py` |
| FR-15 | The page shows processing time | Could | Done | `app.py` |
| FR-16 | Open-vocabulary fallback (for example YOLO-World) if no strong model is found | Could | Not needed: a strong model was found | (see PROJECT_DOCUMENTATION.md section 18) |

### Added during the build

| ID | Requirement | Priority | Status | Where |
| --- | --- | --- | --- | --- |
| FR-17 | The user can take a photo with the camera in the page (laptop webcam or phone camera) | Should | Done, at a requested 1080p | `app.py` (`st.camera_input`) |
| FR-18 | iPhone photos (`.heic`, `.heif`) are accepted, rotated correctly, and previewed | Should | Done | `image_io.py` |
| FR-19 | iPhone videos (`.mov`, H.264 or HEVC) are accepted; the result is a playable `.mp4` | Should | Done | `config.py`, `processors.py` |
| FR-20 | All controls are reachable on a phone screen (no hidden sidebar) | Should | Done: settings in a popover, metrics side by side | `app.py` |
| FR-21 | Damaged, empty or disguised files show a specific message | Must | Done | `validator.py`, `image_io.py` |
| FR-22 | Wrong API key, wrong model ID and no network show specific messages | Must | Done | `errors.py` |
| FR-23 | A partly readable video is processed with a warning saying how much was read | Should | Done | `processors.VideoProcessor` |
| FR-24 | The page reminds the user to keep people out of the frame | Should | Done | `app.py` caption |

## 6. Non-functional requirements

| ID | Requirement | How it is checked | Result |
| --- | --- | --- | --- |
| NFR-1 | A shelf photo returns an annotated image in under 5 seconds | Time 10 photos, slowest and average | **Met:** 0.11 s average, 0.13 s slowest; 0.21 s for a 4000 × 3000 photo |
| NFR-2 | A 10-second video returns an annotated video with a count per frame | Upload a 10-second clip | **Met:** 602 counts for 602 frames; 34.7 s for 4K 60 fps |
| NFR-3 | A teammate can run the app from the README in under 10 minutes | A teammate follows the README without help | **Not tested yet.** The install alone takes 5 to 10 minutes |
| NFR-4 | Runs locally on a laptop with Python 3.10 or newer | Run on a laptop without a GPU | **Met, with a limit:** Python 3.10 to 3.12; `inference` does not support 3.13 and newer |
| NFR-5 | The Roboflow API key is never committed to Git | `.env` ignored; history scanned | **Met:** `detect-secrets` over every commit found only placeholders |
| NFR-6 | Setup is reproducible | Versions pinned | **Met:** `requirements.txt` pins direct dependencies and CPU-only PyTorch; `uv.toml` for Community Cloud |
| NFR-7 | The page appears quickly, even on the first start | Headless Chrome after a reboot | **Met:** title within 4 s, full page by 12 s (was 20 to 25 s blank) |
| NFR-8 | Uploads cannot exhaust memory | Decompression-bomb test files | **Met:** images over 100 MP rejected from the header; a 17 KB PNG that decoded to 432 MB is now refused |
| NFR-9 | Memory stays within a free host's limit for photos | Measure resident memory | **Met for photos** (about 760 MB); 4K video peaks at 1.1 to 1.25 GB |
| NFR-10 | Works on a phone browser | Chrome at 390 px width, real phone | **Met:** the live app (before Phase 7) was used on a phone and a laptop; the Phase 7 camera mode and layout were checked in Chrome at phone size with a fake camera, and reach the live app after the next push |
| NFR-11 | Online access is private | Community Cloud sharing | **Met:** private app; viewers invited by email |

![Video timing](images/11_video_timing.png)

## 7. Technology

| Tool | Used for |
| --- | --- |
| Roboflow Universe | finding and testing a pretrained shelf model |
| Roboflow Inference 1.7.3 | running the model from Python, on the CPU |
| Supervision 0.30.9 | boxes, detections, reading and writing video frames |
| Streamlit 1.65.0 | the page: upload, camera, settings, results |
| OpenCV 4.12, Pillow 12.3, pillow-heif 1.8.1 | decoding photos and videos, including HEIC |
| ffmpeg | re-encoding annotated video to H.264 for browsers |
| PyTorch 2.14.1 (CPU-only build) | required by Inference; the CPU build avoids several GB of GPU libraries |
| Python 3.12 | everything else |
| Streamlit Community Cloud | the private online link |

## 8. Acceptance criteria ("done when", from the brief)

- [x] Uploading any shelf photo returns an annotated image in under 5 seconds. _(0.11 s average)_
- [x] Uploading a 10-second video returns an annotated video with a count per frame.
- [x] The app shows a clear error for unsupported files and for files that are too large.
- [ ] A teammate can run the app from the README in under 10 minutes. _(not tested yet)_

## 9. Deliverables (from the brief)

- [x] Code in a Git repo with a README covering setup, how to run, and which model ID was chosen and why.
  _(GitHub: Rahat-Sultan/shelf-counter. The README's "why" is based on products found; add true counts to make it
  "misses the fewest", see open items.)_
- [ ] 5 example inputs and their annotated outputs (in `samples/`). _(folders ready; needs your own photos)_
- [ ] A short demo to the team: upload a photo, upload a video, show the results. _(script ready in
  TESTING_AND_MODEL_SELECTION.md section 6; the live link makes it easy)_

## 10. Assumptions and decisions

| # | Item | Decision |
| --- | --- | --- |
| A1 | The brief is titled both "Shelf Product Counter" and "Smart Shelf Monitor" | Treated as one project, "Shelf Product Counter". **Confirm with the project owner** |
| A2 | The brief says "too large" without a number | Images 10 MB, video 100 MB (plus 100 megapixels). Adjustable in `src/config.py` |
| A3 | `.jpeg` files | Accepted as `.jpg` |
| A4 | "Count per frame" while detecting every 5th frame | Detection every 5th frame, last result reused in between, so each frame has a count |
| A5 | The headline count for a video | Highest per-frame count, with the average shown beside it. **Confirm, or switch to the average** |
| A6 | Model names in the brief came from memory | Decided: `planogram_sku110k/1` (SKU-110K, one class `0`) at confidence 0.3, after comparing three candidates |
| A7 | Local or hosted inference | Decided: local CPU inference (0.11 s per photo, photos stay on the server, works offline once downloaded) |
| A8 | Phone support | Decided 12 Oct: one web app that works on phones (MOBILE_PLAN option A), not a separate mobile app |
| A9 | Hosting | Decided 12 Oct: Streamlit Community Cloud, private, Python 3.12 (livemy.app's free plan had too little memory; Vercel cannot run Streamlit) |
| A10 | Box labels | Not drawn: the only class is named `0`, and labels hide products on dense shelves. The count panel carries the number |

![Model comparison](images/10_model_comparison.png)

## 11. Risks

| Risk | Impact | Status and mitigation |
| --- | --- | --- |
| No public shelf model performs well | High | **Resolved:** the SKU-110K model works; still confirm with true counts |
| Inference slower than 5 s on a laptop CPU | Medium | **Resolved:** 0.11 s per photo |
| Dense shelves, glare, small or dark photos cause misses | Medium | **Open, documented:** use full-resolution photos; limits listed in the README |
| Annotated video does not play in the browser | Medium | **Resolved:** ffmpeg re-encodes to H.264 |
| API key leaked | High | **Mitigated:** never in Git (scanned). One key was pasted into a hosting chat and has been replaced |
| Memory limit of the free host | Medium | **Partly open:** photos are well within limits; 4K videos may approach them. Fallback: Roboflow's hosted API (PROJECT_DOCUMENTATION.md section 18) |
| Host defaults change (Python 3.14 on Community Cloud) | Medium | **Mitigated:** DEPLOY.md says to choose 3.12; it cannot be changed after creating the app |
| Model licence unknown | Medium | **Open:** confirm on the model's Universe page before publishing samples |
| `inference` is large and slow to install | Low | Documented; CPU-only PyTorch keeps it to about 1.5 GB of downloads |

## 12. Open questions for the project owner

1. Is "Shelf Product Counter" the correct project name (A1)?
2. Are the limits right: 10 MB and 100 MP for photos, 100 MB and 30 seconds for video (A2)?
3. Should the video headline count be the maximum, the average, or the last frame (A5)?
4. Is the private Community Cloud link acceptable for demos, and who should be invited?

The original question 4 (hosted API or offline) was answered by measurement: local inference is fast enough (A7).

## 13. Release history

| Date | Milestone |
| --- | --- |
| 9 Oct 2026 | Phase 0 setup; Phases 1 and 2: model chosen, photo script |
| 9 Oct 2026 | Phase 3: upload page; Phase 4: video; Phase 5: errors and validation |
| 12 Oct 2026 | Security and startup fixes; deployment preparation; Streamlit Community Cloud deploy (Phase 8) |
| 12 Oct 2026 | Phase 7: camera, iPhone formats, phone layout; detailed documentation |

![Project phases](images/09_phases.png)
