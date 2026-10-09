# Project Phases

This plan breaks the project into seven phases. Phases 0 to 2 are the foundation, 3 to 5 are the build, and 6 is delivery. Phase 1 is the biggest risk, because everything after it depends on the model being good.

Effort estimates are suggestions only. The brief gives no deadline.

```mermaid
flowchart LR
    P0[Phase 0<br/>Setup] --> P1[Phase 1<br/>Pick model]
    P1 --> P2[Phase 2<br/>Image script]
    P2 --> P3[Phase 3<br/>Web app]
    P3 --> P4[Phase 4<br/>Video]
    P4 --> P5[Phase 5<br/>Errors and speed]
    P5 --> P6[Phase 6<br/>Docs and demo]
```

| Phase | Name | Suggested effort | Main output |
| --- | --- | --- | --- |
| 0 | Setup | 0.5 day | Working environment, repo, API key |
| 1 | Test data and model selection | 1 to 2 days | Chosen model ID and comparison table |
| 2 | Single-image script | 0.5 to 1 day | Script that boxes and counts one image |
| 3 | Image web app | 1 day | Upload page for images |
| 4 | Video support | 1 to 2 days | Annotated video with per-frame counts |
| 5 | Validation and error handling | 0.5 to 1 day | Clear errors, speed check |
| 6 | Docs and deliverables | 1 day | README, samples, demo |

---

## Phase 0: Setup

**Goal:** a clean environment where a one-image script can run.

**Tasks**

- [ ] Create a free Roboflow account and copy the API key.
- [ ] Install Python 3.10 or newer.
- [ ] Create a virtual environment and install `inference`, `supervision`, `streamlit`, `opencv-python-headless`, `python-dotenv`.
- [ ] Copy `.env.example` to `.env` and add the API key.
- [ ] Confirm `.env` is in `.gitignore` before the first commit.
- [ ] Make the first Git commit.
- [ ] Run `pip freeze` and pin versions in `requirements.txt`.

**Exit criteria:** `python -c "import inference, supervision, streamlit"` runs without errors, and `.env` is not tracked by Git.

**Risks:** the `inference` install is large and slow. Give it time and note this in the README.

---

## Phase 1: Test data and model selection

**Goal:** choose the model that misses the fewest products. This is the highest-risk phase.

**Tasks**

- [ ] Take 10 shelf photos with no people in frame. Vary lighting, angle and shelf density.
- [ ] Record a few short shelf videos (under 30 seconds).
- [ ] Search Roboflow Universe for "retail shelf", "SKU-110K" and "shelf products".
- [ ] Keep only projects that have a trained model attached (a model tab where you can test an image). Many projects are datasets only.
- [ ] Shortlist 2 or 3 candidates.
- [ ] Test each candidate in the browser, then run it on all 10 photos.
- [ ] For each photo, count the real products by eye and record what each model found.
- [ ] Pick the winner and write down its model ID (`project-name/version`) and why it won.
- [ ] Fallback only if all candidates are poor: use an open-vocabulary model such as YOLO-World.

**Deliverable:** a completed comparison table (template in `TESTING_AND_MODEL_SELECTION.md`) and a chosen model ID in `.env`.

**Exit criteria:** one model chosen, with numbers to justify it.

**Risks:** the model names in the original brief came from memory and may be wrong. Confirm what exists before committing.

---

## Phase 2: Single-image script

**Goal:** prove the pipeline end to end on one image before building any UI.

**Tasks**

- [ ] Load an image with OpenCV.
- [ ] Run the model through Roboflow Inference.
- [ ] Convert the result to a Supervision `Detections` object.
- [ ] Draw boxes and the count.
- [ ] Save the annotated image and print the count.
- [ ] Time the inference call.
- [ ] Try a few confidence values and note which works best.

**Starter code:** `src/detector.py`, `src/annotator.py`, `src/processors.py` (`ImageProcessor`).

**Exit criteria:** a good annotated image from at least 3 of your test photos, with timing recorded.

**Risks:** if one image already takes close to 5 seconds, decide now whether to resize inputs or use hosted inference.

---

## Phase 3: Image web app

**Goal:** the same pipeline behind an upload page.

**Tasks**

- [ ] Build the Streamlit page in `app.py`: upload, annotated image, count, download button.
- [ ] Load the model once and cache it (`st.cache_resource`), not on every upload.
- [ ] Show a spinner while processing.
- [ ] Show processing time.
- [ ] Optional: confidence slider.

**Exit criteria:** upload a photo, see boxes and a count, and download the result, all in under 5 seconds after the first (warm-up) run.

**Risks:** loading the model on every upload will blow the speed target.

---

## Phase 4: Video support

**Goal:** accept a short `.mp4` and return an annotated video with a count per frame.

**Tasks**

- [ ] Read frames with Supervision.
- [ ] Run detection on every 5th frame and reuse the latest detections in between.
- [ ] Draw boxes and the running count on every frame.
- [ ] Write the annotated frames to a new `.mp4`.
- [ ] Show the video in the page with a download button.
- [ ] Show per-frame counts (for example a line chart).
- [ ] Test playback in the browser.

**Starter code:** `src/processors.py` (`VideoProcessor`).

**Exit criteria:** a 10-second video returns an annotated video that plays in the browser, with a count for every frame.

**Risks:** some video encodings do not play in browsers. Re-encode with ffmpeg (H.264) if playback fails.

---

## Phase 5: Validation and error handling

**Goal:** bad input produces a friendly message, never a crash.

**Tasks**

- [ ] Accept only `.jpg`, `.jpeg`, `.png` and `.mp4`.
- [ ] Enforce size limits and the 30-second video limit.
- [ ] Handle unreadable or corrupt files.
- [ ] Handle missing API key or model ID with a clear message.
- [ ] Handle model or network failures with a clear message.
- [ ] Test deliberately: upload a `.pdf`, a huge file, a 60-second video, and a renamed text file.
- [ ] Re-time the image path against the 5-second target.

**Starter code:** `src/validator.py`, `tests/test_validator.py`.

**Exit criteria:** every error case in the test matrix shows a plain-English message.

---

## Phase 6: Docs and deliverables

**Goal:** make the project easy to run, review and demo.

**Tasks**

- [ ] Finish the README: setup, how to run, model ID and why, known limits.
- [ ] Pick 5 example inputs, including good results and honest limits. Save each input and its annotated output in `samples/`.
- [ ] Ask a teammate to follow the README cold and time them. Fix anything that slows them down.
- [ ] Rehearse the demo: one photo, one video, results on screen.
- [ ] Final check of the acceptance criteria in `PRD.md`.

**Exit criteria:** all acceptance criteria and deliverables in `PRD.md` are ticked.

---

## Dependency notes

- Phases are mostly sequential. Phase 1 gates everything.
- Phase 4 depends on Phase 3 only for the UI. The video pipeline itself can be prototyped as a script right after Phase 2.
- Phase 5 can start in parallel with Phase 4 for the image path.
