# Shelf Product Counter

Upload a shelf photo or a short video and get it back with every product boxed and counted.
Uses a pretrained model from Roboflow Universe, so there is no data labeling or training.

## Setup

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

## Run

```bash
streamlit run app.py
```

## Chosen model

- Model ID: `retail-shelf-detection-peimi/1`
  ([Universe page](https://universe.roboflow.com/tossoengineering/retail-shelf-detection-peimi))
- Type: Roboflow object detection model with two classes, `product` and `empty` (empty shelf space).
  The app draws and counts only `product` boxes.
- Training data: 425 images (per the Universe page).
- Why: _to be completed after testing on the 10 shelf photos: how many products it missed, and how it compares with any alternative tried_

## How it works

1. The page accepts a .jpg, .png or .mp4 file and validates type, size and video length.
2. The detector runs the Roboflow model through Roboflow Inference.
3. Supervision draws boxes and the product count.
4. For video, detection runs on every 5th frame and the last result is reused for the frames in between, so every frame carries boxes and a count.
5. The page shows the result, the count and a download button.

## Limits

- One file at a time, no live camera.
- Photos with people in them are out of scope.
- Dense shelves and glare can cause missed products (details to be added after testing).

## Project layout

```
app.py              Streamlit page
src/config.py       settings and limits
src/validator.py    file type, size and duration checks
src/detector.py     Roboflow model wrapper
src/annotator.py    boxes and count overlay
src/processors.py   image and video pipelines
tests/              unit tests
samples/            5 example inputs and outputs
docs/               project documentation (see below)
```

## Documentation

- [Product requirements](docs/PRD.md): goals, scope, requirements, acceptance criteria, risks
- [Project phases](docs/PHASES.md): the seven phases with tasks and exit criteria
- [Architecture](docs/ARCHITECTURE.md): components, diagrams, database decision, design choices
- [Testing and model selection](docs/TESTING_AND_MODEL_SELECTION.md): model comparison method, test matrix, demo script
