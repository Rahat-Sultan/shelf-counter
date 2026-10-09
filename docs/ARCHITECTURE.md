# Architecture

## 1. Overview

The app is a single local Python process. A Streamlit page accepts an upload, a validator checks it, a processor runs it through the detector, and an annotator draws the result. The only external dependency is the Roboflow shelf model.

## 2. Components

| Component | File | Responsibility |
| --- | --- | --- |
| Upload page | `app.py` | File upload, shows result, count and download button, shows errors |
| Config | `src/config.py` | Settings and limits, reads `.env` |
| Validator | `src/validator.py` | Checks file type, size and video duration before any processing |
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
    A --> R[Result: file + count]
    R --> UI
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
        +process(path) Result
    }
    class ImageProcessor {
        +process(path) Result
    }
    class VideoProcessor {
        +int frame_step
        +process(path) Result
    }
    class ShelfDetector {
        -str model_id
        -float confidence
        +detect(frame) Detections
    }
    class Annotator {
        +annotate(frame, detections) frame
    }
    class Result {
        +Path output_path
        +int count
        +list per_frame_counts
        +float seconds
    }
    Processor <|-- ImageProcessor
    Processor <|-- VideoProcessor
    ShelfApp --> FileValidator : validates with
    ShelfApp --> Processor : picks one
    Processor --> ShelfDetector : uses
    Processor --> Annotator : uses
    Processor ..> Result : returns
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
| Detect every 5th video frame and reuse results in between | Meets the "every 5th frame" speed requirement while still giving every frame boxes and a count |
| Detector and annotator as separate classes | The model can be swapped (for example to YOLO-World) without touching drawing code |
| Image and video share a `Processor` base class | Same flow, different frame source; keeps the page code simple |
| No label text on boxes | Shelves are dense, labels would clutter the image; the count overlay is enough |
| Config in `.env`, limits in `config.py` | Keeps the API key out of Git and limits easy to change |
| Temporary file for uploads | OpenCV and Supervision read from a path, not from memory |

## 8. Configuration

| Setting | Where | Default |
| --- | --- | --- |
| `ROBOFLOW_API_KEY` | `.env` | none (required) |
| `MODEL_ID` | `.env` | none (required, `project-name/version`) |
| `CONFIDENCE` | `.env` | 0.4 |
| `MAX_IMAGE_MB`, `MAX_VIDEO_MB`, `MAX_VIDEO_SECONDS` | `src/config.py` | 10, 100, 30 |
| `FRAME_STEP` | `src/config.py` | 5 |

## 9. Folder layout

```
shelf-counter/
  app.py
  requirements.txt
  .env.example
  .gitignore
  README.md
  docs/
    PRD.md
    PHASES.md
    ARCHITECTURE.md
    TESTING_AND_MODEL_SELECTION.md
  src/
    config.py
    validator.py
    detector.py
    annotator.py
    processors.py
  tests/
    test_validator.py
  samples/
    inputs/
    outputs/
```

## 10. Known technical risks

- Video output format may not play in some browsers. Re-encode to H.264 with ffmpeg if needed.
- Local CPU inference may exceed 5 seconds. Measure in Phase 2 and consider resizing images or hosted inference.
- The `inference` package is large; first install is slow.
