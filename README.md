# Shelf Product Counter

Upload a shelf photo or a short video and get it back with every product boxed and counted.
Uses a pretrained model from Roboflow Universe, so there is no data labeling or training.

## Setup

New to the project? Follow [STARTUP.md](STARTUP.md) for a step-by-step setup with checks and fixes for common problems.
To put it on a live link, follow [DEPLOY.md](DEPLOY.md).

Requires Python 3.10 to 3.12. The `inference` package does not support newer Python versions yet,
so if your default `python` is 3.13 or later, create the venv with `python3.12` instead.

The first install is large (about 1.5 GB) and can take 5 to 10 minutes. `requirements.txt` installs
the CPU-only build of PyTorch, so no GPU is needed. If pip still fails with "Disk quota exceeded"
or "No space left on device", your `/tmp` is too small; run the install with
`TMPDIR=~/.cache/pip-tmp pip install -r requirements.txt` (create that folder first).

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in your values
```

Get a free API key from your Roboflow account settings and put it in `.env`.

Install ffmpeg for video support (`sudo apt install ffmpeg`, or `brew install ffmpeg` on macOS). The app uses it
to convert annotated videos to H.264 so they play in the browser. Without it, videos still download but may not
play in the page.

## Run

```bash
streamlit run app.py
```

The page opens at http://localhost:8501. Upload a photo to see it boxed and counted, with the processing time
and a download button. The sidebar slider changes the confidence threshold (default 0.3). The first upload also
loads the model; later uploads reuse it.

The title appears within a few seconds; the model then loads for 10 to 30 seconds (longest after a reboot) while
the page shows "Loading the model...". If `streamlit` is not found, the venv is not active: activate it or run
`.venv/bin/streamlit run app.py`. See [STARTUP.md](STARTUP.md) for more fixes.

To box and count photos from the command line (no web page):

```bash
python -m scripts.count_image path/to/shelf.jpg
```

To compare models or confidence values on a folder of photos (writes `outputs/eval/results.csv`):

```bash
python -m scripts.evaluate --images path/to/photos --models planogram_sku110k/1=0 --confidence 0.3 0.4 0.5
```

## Chosen model

- Model ID: `planogram_sku110k/1`
  ([Universe workspace](https://universe.roboflow.com/sample-rzhbg), project Planogram_SKU110K)
- Type: Roboflow object detection model trained on SKU-110K (about 11.7k densely packed shelf images).
  It has one class, named `0`, so every box is a product. Set `PRODUCT_CLASS=0` in `.env`.
- Confidence: 0.3. Lower values found more real products on the test photos without adding false
  boxes; blank, grey, white and noise images return 0.
- Why: on 10 test photos at confidence 0.4 it found 1,168 products against 692 for the first candidate,
  `retail-shelf-detection-peimi/1`. That model skipped whole sections of shelves (for example 14 boxes
  on a snack stand where this model finds 35). A third candidate, `shelf-product/1`, recognises
  specific coffee brands rather than generic products, so it was ruled out.
- Speed: 0.11 s per photo on average, 0.13 s slowest (Intel i5-8350U laptop CPU, no GPU).
- Labels: boxes are drawn without label text. The model's only class is named `0`, so every label would read
  "0", and on dense shelves labels hide the products. The "Products: N" overlay carries the count instead.
- Fallback: the brief suggests an open-vocabulary model such as YOLO-World if no shelf model works well.
  It was not needed, because the SKU-110K model works, so it is not installed.
- License: not yet confirmed. Check the "Cite This Project" section on the model's Universe page and add the
  license and credit here before publishing results.

## How it works

1. The page accepts a .jpg, .png or .mp4 file and validates type, size and video length.
2. The detector runs the Roboflow model through Roboflow Inference.
3. Supervision draws boxes and the product count.
4. For video, frames wider than 1280 px are scaled down first (the model works at about 640 px anyway).
   Detection runs on every 5th frame and the last result is reused for the frames in between, so every frame
   carries boxes and a count. The result is re-encoded to H.264 with ffmpeg so it plays in the browser.
   The page shows the highest per-frame count, the average, a per-frame chart, and a CSV of per-frame counts.
5. The page shows the result, the count and a download button.

## Limits

- One file at a time, no live camera.
- Photos with people in them are out of scope.
- Dense shelves and glare can cause missed products.
- A partly damaged photo is counted as far as it can be decoded, without a warning. A partly damaged video
  shows a warning saying how many frames could be read.
- Small or low-resolution photos (for example 200x360 px) miss many products. Use full-resolution photos.
- Very dark photos return fewer products (a shelf darkened to 15% brightness dropped from 230 to 155).
- Video takes longer than images: a 10-second 4K 60 fps clip takes about 35 seconds on a laptop CPU.
  Lower resolution or frame rate clips are faster. The page shows a progress bar.

## Security and privacy

- When run locally, the app can be opened by other devices on the same network, so you can test it from a phone.
  To keep it on this laptop only, run `streamlit run app.py --server.address localhost`. A fixed address is not
  set in `.streamlit/config.toml`, because that would stop phones and Streamlit Community Cloud from reaching it.
- Photos and videos never leave the laptop: the model runs locally. The `inference` package reports usage counts
  to Roboflow (frame counts, durations, a hashed API key), not images.
- The API key stays in `.env`, which Git ignores. `.env` is read only by the app's own settings, not exported
  to the environment.
- Uploads are checked before they are decoded: file type, file size (10 MB images, 100 MB video), image size from
  the file header (100 megapixels, which blocks "decompression bomb" files) and video length (30 seconds).
- The model is cached in `~/.cache/shelf-counter/models` (override with `MODEL_CACHE_DIR`), not in `/tmp`, so it
  survives a reboot and the app keeps working offline.
- Known and accepted: `wheel` 0.45.1 has CVE-2026-24049, a path traversal in the `wheel unpack` command.
  `inference` requires `wheel<=0.45.1`, and this app never unpacks wheel files.

## Project layout

```
STARTUP.md          step-by-step setup guide
DEPLOY.md           step-by-step deployment guide (Streamlit Community Cloud; Dockerfile for other hosts)
Dockerfile          container image for hosting
app.py              Streamlit page
src/config.py       settings and limits
src/validator.py    file type, size, duration and readability checks
src/errors.py       plain-English messages for model, key and network errors
src/detector.py     Roboflow model wrapper
src/annotator.py    boxes and count overlay
src/processors.py   image and video pipelines
scripts/            command-line tools: count_image, evaluate, probe_models
tests/              unit tests
samples/            5 example inputs and outputs
docs/               project documentation (see below)
```

## Documentation

- [Product requirements](docs/PRD.md): goals, scope, requirements, acceptance criteria, risks
- [Project phases](docs/PHASES.md): the seven phases with tasks and exit criteria
- [Architecture](docs/ARCHITECTURE.md): components, diagrams, database decision, design choices
- [Testing and model selection](docs/TESTING_AND_MODEL_SELECTION.md): model comparison method, test matrix, demo script
- [Mobile and web plan](docs/MOBILE_PLAN.md): proposal for a mobile app next to the web app, with phases, pros and cons (needs approval)
