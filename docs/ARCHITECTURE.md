# Architecture

## 1. Overview

The app is a single local Python process. A Streamlit page accepts an upload, a validator checks it, a processor runs it through the detector, and an annotator draws the result. The only external dependency is the Roboflow shelf model.

## 2. Components

| Component | File | Responsibility |
| --- | --- | --- |
| Upload page | `app.py` | File upload, shows result, count and download button, shows errors |
| Config | `src/config.py` | Settings and limits, reads `.env` |
| Validator | `src/validator.py` | Checks file type, size, video duration, and that the file can be read, before any processing |
| Errors | `src/errors.py` | Turns model, key and network failures into plain-English messages |
| Detector | `src/detector.py` | Wraps Roboflow Inference; returns Supervision `Detections` |
| Annotator | `src/annotator.py` | Draws boxes and the product count on a frame |
| Image processor | `src/processors.py` | Image path: read, detect, annotate, save |
| Video processor | `src/processors.py` | Video path: read frames, detect every Nth frame, annotate, write video |
| Roboflow model | external | Pretrained shelf detection model |

## 3. Component flow

```mermaid
flowchart TD
    U[User browser] --> UI[Upload page<br/>app.py]
    UI --> V[Validator]
    V -->|invalid| E[Error message]
    V -->|image| IP[Image processor]
    V -->|video| VP[Video processor]
    IP --> D[Detector]
    VP --> D
    D <--> RF[Roboflow shelf model]
    IP --> A[Annotator]
    VP --> A
    VP --> FF[ffmpeg: re-encode to H.264]
    A --> R[Result: file + count]
    FF --> R
    R --> UI
    IP -.->|failure| ER[Errors: plain-English message]
    VP -.->|failure| ER
    D -.->|key, model or network failure| ER
    ER --> UI
```

## 4. Sequence of one upload

```mermaid
sequenceDiagram
    actor User
    participant UI as Upload page
    participant Val as Validator
    participant Proc as Processor
    participant Det as Detector
    participant RF as Roboflow model
    participant Ann as Annotator

    User->>UI: Upload file
    UI->>Val: validate(file)
    alt invalid file
        Val-->>UI: error message
        UI-->>User: show error
    else valid file
        Val-->>UI: ok and kind
        UI->>Proc: process(file)
        loop every 5th frame (image: once)
            Proc->>Det: detect(frame)
            Det->>RF: infer(frame)
            RF-->>Det: predictions
            Det-->>Proc: Detections
        end
        Proc->>Ann: annotate(frame, detections)
        Ann-->>Proc: annotated frame
        Proc-->>UI: Result (file, count, per-frame counts)
        UI-->>User: show result and download button
    end
```

## 5. Class diagram

```mermaid
classDiagram
    class ShelfApp {
        +run()
        +handle_upload(file)
    }
    class FileValidator {
        +validate(path) ValidationResult
    }
    class Processor {
        <<abstract>>
        +float confidence
        +Path output_dir
        +process(path) Result
    }
    class ImageProcessor {
        +process(path) Result
    }
    class VideoProcessor {
        +int frame_step
        +int max_width
        +on_progress(fraction)
        +process(path) Result
    }
    class ShelfDetector {
        -str model_id
        -float confidence
        -str product_class
        +detect(frame, confidence) Detections
    }
    class UserFacingError {
        +str message
    }
    class Annotator {
        +annotate(frame, detections) frame
    }
    class Result {
        +Path output_path
        +int count
        +list per_frame_counts
        +float seconds
        +float fps
        +str note
    }
    Processor <|-- ImageProcessor
    Processor <|-- VideoProcessor
    ShelfApp --> FileValidator : validates with
    ShelfApp --> Processor : picks one
    Processor --> ShelfDetector : uses
    Processor --> Annotator : uses
    Processor ..> Result : returns
    Processor ..> UserFacingError : raises for unreadable files
```

## 6. Do we need a database?

**No.** The reasons:

- The app handles one file at a time and keeps nothing between uploads.
- Results are files the user downloads. Nothing needs to be queried later.
- The brief has no accounts, history, or reporting.
- Configuration (API key, model ID, confidence) lives in `.env`.

A database would add setup steps and work the brief doesn't ask for, and it would put the 10-minute setup target at risk.

### Optional future extension: scan history

If the project owner later wants history, use one SQLite table. This is not part of the current scope.

```mermaid
erDiagram
    SCAN {
        integer id PK
        text filename
        text kind
        integer product_count
        text model_id
        real processing_seconds
        text created_at
    }
```

## 7. Key design decisions

| Decision | Reason |
| --- | --- |
| Validate before processing | Rejects bad files cheaply, with a clear message, before the model is loaded or called |
| Load the model once and cache it | Loading on every upload would break the 5-second target |
| Import `inference` only when the model loads, then warm the model as soon as the page is drawn | Importing `inference` takes 10 to 20 seconds; at the top of `app.py` it left the page blank that long. Warming right after drawing keeps the first upload fast and reports a bad key immediately |
| Listen on localhost only | Streamlit's default listens on every interface, so anyone on the same Wi-Fi could use the app |
| Model cache in `~/.cache/shelf-counter/models` | The default `/tmp/cache` is wiped on reboot, which forced a new download and broke offline use |
| Check image megapixels from the header before decoding | A 17 KB PNG decoded to 432 MB in testing; OpenCV accepts up to about 1 billion pixels |
| Detect every 5th video frame and reuse results in between | Meets the "every 5th frame" speed requirement while still giving every frame boxes and a count |
| Detector and annotator as separate classes | The model can be swapped (for example to YOLO-World) without touching drawing code |
| Image and video share a `Processor` base class | Same flow, different frame source; keeps the page code simple |
| No label text on boxes | Shelves are dense, labels would clutter the image; the count overlay is enough |
| Config in `.env`, limits in `config.py` | Keeps the API key out of Git and limits easy to change |
| `.env` is read with `dotenv_values`, not exported to the environment | The `inference` package parses `CONFIDENCE` itself on import, so a bad value would crash it before the app's own checks. Real environment variables still override `.env` |
| Bad settings warn instead of crashing | A non-numeric or out-of-range `CONFIDENCE` falls back to the default or the nearest limit, with a warning on the page |
| Temporary file for uploads | OpenCV and Supervision read from a path, not from memory |

## 8. Configuration

| Setting | Where | Default |
| --- | --- | --- |
| `ROBOFLOW_API_KEY` | `.env` | none (required) |
| `MODEL_ID` | `.env` | none (required, `project-name/version`); chosen: `planogram_sku110k/1` |
| `CONFIDENCE` | `.env` | 0.3 |
| `PRODUCT_CLASS` | `.env` | `0` (the only class of the chosen model) |
| `MAX_DETECTIONS` | `src/config.py` | 1000 (Inference defaults to 300, which undercounts packed shelves) |
| `MAX_IMAGE_MB`, `MAX_VIDEO_MB`, `MAX_VIDEO_SECONDS` | `src/config.py` | 10, 100, 30 |
| `FRAME_STEP` | `src/config.py` | 5 |
| `VIDEO_MAX_WIDTH` | `src/config.py` | 1280 (wider video frames are scaled down before detection) |

## 9. Folder layout

```
shelf-counter/
  app.py
  requirements.txt
  .env.example
  .gitignore
  .streamlit/
    config.toml
  README.md
  STARTUP.md
  docs/
    PRD.md
    PHASES.md
    ARCHITECTURE.md
    TESTING_AND_MODEL_SELECTION.md
  src/
    config.py
    validator.py
    errors.py
    detector.py
    annotator.py
    processors.py
  scripts/
    count_image.py
    evaluate.py
    probe_models.py
  tests/
    test_validator.py
    test_video.py
    test_errors.py
    test_security.py
  samples/
    inputs/
    outputs/
```

## 10. Known technical risks

- `wheel` 0.45.1 (CVE-2026-24049, path traversal in `wheel unpack`) is pinned by `inference` (`wheel<=0.45.1`). Not reachable from the app, which never unpacks wheels. Upgrade when `inference` allows it.

- Video output format: OpenCV can only write MPEG-4 Part 2 (`mp4v`), which browsers do not play. Resolved: the video processor re-encodes to H.264 with ffmpeg. Without ffmpeg the video still downloads but may not play in the page.
- Local CPU inference may exceed 5 seconds. Measure in Phase 2 and consider resizing images or hosted inference.
- The `inference` package is large; first install is slow.
