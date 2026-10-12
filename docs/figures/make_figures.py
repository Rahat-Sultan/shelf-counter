"""Draws the diagrams and charts used in docs/PROJECT_DOCUMENTATION.md and docs/PRD.md.

Run from the shelf-counter folder:
    python docs/figures/make_figures.py

Writes PNG files to docs/images/. Uses matplotlib, which is installed with the project's packages.
Edit the figures here and re-run after changing the architecture, so the pictures stay accurate.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "images"

# Colours: chart slots from the validated reference palette (blue, orange, aqua), text and lines from its
# neutral tokens. In diagrams each colour marks a layer, explained in a legend on every figure.
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
MUTED = "#898781"
LINE = "#c3c2b7"
GRID = "#e1e0d9"
LAYERS = {
    "ui": ("#2a78d6", "#e8f0fb", "Page and user"),
    "core": ("#eb6834", "#fdeee7", "Our modules (src/)"),
    "ext": ("#1baf7a", "#e5f6ef", "Libraries and services"),
    "data": (MUTED, "#f1f0ec", "Files and settings"),
}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": TEXT})


class Diagram:
    """A canvas in data units (0..W, 0..H) with rounded boxes and labelled arrows."""

    def __init__(self, title, subtitle="", w=100, h=60, size=(13, 7.8)):
        self.fig, self.ax = plt.subplots(figsize=size, dpi=150)
        self.fig.patch.set_facecolor(SURFACE)
        self.ax.set_xlim(0, w)
        self.ax.set_ylim(0, h)
        self.ax.axis("off")
        self.boxes = {}
        self.w, self.h = w, h
        self.ax.text(1, h - 1.5, title, fontsize=17, fontweight="bold", va="top")
        if subtitle:
            self.ax.text(1, h - 5.2, subtitle, fontsize=11.5, color=TEXT_2, va="top")

    def box(self, key, x, y, w, h, title, lines=(), layer="core", title_size=12):
        edge, fill, _ = LAYERS[layer]
        self.ax.add_patch(
            FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.2", linewidth=1.6,
                           edgecolor=edge, facecolor=fill)
        )
        self.ax.text(x + w / 2, y + h - 1.6, title, ha="center", va="top", fontsize=title_size, fontweight="bold")
        for i, line in enumerate(lines):
            self.ax.text(x + w / 2, y + h - 4.6 - i * 2.7, line, ha="center", va="top", fontsize=9.5, color=TEXT_2)
        self.boxes[key] = (x, y, w, h)

    def _anchor(self, key, side):
        x, y, w, h = self.boxes[key]
        return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]

    def arrow(self, a, b, label="", sides=None, rad=0.0, label_pos=0.5, label_offset=(0, 1.0), dashed=False):
        """Arrow from box a to box b. sides like "rl" = from a's right edge to b's left edge."""
        if sides is None:
            ax_, ay_, aw, ah = self.boxes[a]
            bx_, by_, bw, bh = self.boxes[b]
            dx = (bx_ + bw / 2) - (ax_ + aw / 2)
            dy = (by_ + bh / 2) - (ay_ + ah / 2)
            sides = ("rl" if dx > 0 else "lr") if abs(dx) > abs(dy) else ("tb" if dy > 0 else "bt")
        p1, p2 = self._anchor(a, sides[0]), self._anchor(b, sides[1])
        self.ax.add_patch(
            FancyArrowPatch(p1, p2, arrowstyle="-|>,head_length=7,head_width=4", mutation_scale=1, linewidth=1.5,
                            color=TEXT_2, connectionstyle=f"arc3,rad={rad}", linestyle=(0, (4, 3)) if dashed else "-",
                            shrinkA=2, shrinkB=2)
        )
        if label:
            mx = p1[0] + (p2[0] - p1[0]) * label_pos + label_offset[0]
            my = p1[1] + (p2[1] - p1[1]) * label_pos + label_offset[1]
            self.ax.text(mx, my, label, ha="center", va="bottom", fontsize=9, color=TEXT_2,
                         bbox={"boxstyle": "round,pad=0.25", "facecolor": SURFACE, "edgecolor": "none"})

    def note(self, x, y, text, size=9.5, color=TEXT_2, **kw):
        self.ax.text(x, y, text, fontsize=size, color=color, va="top", **kw)

    def legend(self, layers=("ui", "core", "ext", "data"), y=1.6):
        x = 1
        for layer in layers:
            edge, fill, label = LAYERS[layer]
            self.ax.add_patch(FancyBboxPatch((x, y), 2.2, 1.6, boxstyle="round,pad=0,rounding_size=0.4",
                                             edgecolor=edge, facecolor=fill, linewidth=1.4))
            self.ax.text(x + 3, y + 0.8, label, va="center", fontsize=9.5, color=TEXT_2)
            x += 4.2 + len(label) * 0.95

    def save(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        self.fig.savefig(OUT / name, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.25)
        plt.close(self.fig)
        print("wrote", OUT / name)


def system_overview():
    d = Diagram("System overview", "Who uses the app, where it runs, and what it depends on")
    d.box("laptop", 2, 38, 17, 9, "Laptop browser", ["upload or webcam"], "ui")
    d.box("phone", 2, 25, 17, 9, "Phone browser", ["upload, Take photo,", "Record video"], "ui")
    d.box("page", 27, 28, 20, 16, "Streamlit page", ["app.py", "upload, camera, settings,", "results, downloads"], "ui")
    d.box("core", 55, 28, 20, 16, "Core modules", ["src/: validate, read,", "detect, annotate,", "encode video"], "core")
    d.box("model", 82, 37, 16, 9, "Roboflow model", ["planogram_sku110k/1", "runs on the CPU"], "ext")
    d.box("ffmpeg", 82, 25, 16, 9, "ffmpeg", ["H.264 for browsers"], "ext")
    d.box("host", 27, 6, 48, 11, "Where it runs", ["Laptop: streamlit run app.py (Python 3.12 venv)",
                                                  "Online: Streamlit Community Cloud, private link, Python 3.12"], "data")
    d.arrow("laptop", "page", "HTTP + WebSocket", sides="rl", label_offset=(0, 0.6))
    d.arrow("phone", "page", "HTTPS", sides="rl", label_offset=(0, 0.6))
    d.arrow("page", "core", "file path", sides="rl")
    d.arrow("core", "model", "frames", sides="rl", label_offset=(-1, 0.6))
    d.arrow("core", "ffmpeg", "raw video", sides="rl", label_offset=(-1, -3.2))
    d.arrow("core", "page", "Result: file + counts", sides="bb", rad=0.45, label_pos=0.5, label_offset=(0, -6.2))
    d.note(80, 21.5, "Model weights download once from\nRoboflow with the API key, then run\nlocally; no photo leaves the server.")
    d.legend()
    d.save("01_system_overview.png")


def module_map():
    d = Diagram("Module map", "Every file and what it uses. Arrows point from the caller to what it uses.", w=120, h=66, size=(14.5, 8.4))
    d.box("app", 48, 50, 24, 9, "app.py", ["Streamlit page; loads the", "detector lazily (load_detector)"], "ui")
    d.box("config", 2, 35, 17, 9.5, "config.py", ["settings, limits,", "warnings"], "core")
    d.box("errors", 22, 35, 17, 9.5, "errors.py", ["plain-English", "messages"], "core")
    d.box("validator", 42, 35, 17, 9.5, "validator.py", ["type, size, MP,", "duration checks"], "core")
    d.box("imageio", 62, 35, 17, 9.5, "image_io.py", ["JPEG, PNG, HEIC:", "header + decode"], "core")
    d.box("processors", 84, 35, 17, 9.5, "processors.py", ["Image/Video", "Processor, Result"], "core")
    d.box("env", 2, 20, 17, 9, ".env / secrets", ["key, model, class,", "confidence"], "data")
    d.box("annotator", 44, 20, 17, 9.5, "annotator.py", ["boxes + count", "overlay"], "core")
    d.box("detector", 84, 20, 17, 9.5, "detector.py", ["ShelfDetector,", "keep_products"], "core")
    d.box("ffmpeg", 104, 20, 14, 9.5, "ffmpeg", ["H.264 encode", "(subprocess)"], "ext")
    d.box("sv", 44, 5, 17, 9, "Supervision", ["boxes, video I/O"], "ext")
    d.box("cv", 62, 5, 17, 9, "OpenCV + Pillow", ["+ pillow-heif"], "ext")
    d.box("inf", 84, 5, 17, 9, "Roboflow Inference", ["model + weights"], "ext", title_size=10.5)
    for target in ("config", "errors", "validator", "imageio", "processors"):
        d.arrow("app", target, sides="bt")
    d.arrow("env", "config", sides="tb")
    d.arrow("validator", "imageio", sides="rl")
    d.arrow("processors", "imageio", sides="lr")
    d.arrow("processors", "annotator", sides="bt")
    d.arrow("processors", "detector", "detect()", sides="bt", label_offset=(3.5, -1))
    d.arrow("processors", "ffmpeg", sides="bt")
    d.arrow("imageio", "cv", sides="bt")
    d.arrow("annotator", "sv", sides="bt")
    d.arrow("detector", "inf", sides="bt")
    d.note(1, 15, "config.py is read by most modules\n(arrows omitted). app.py also uses\nannotator.py to build processors.", size=9)
    d.legend()
    d.save("02_module_map.png")


def image_flow():
    d = Diagram("Photo flow", "What happens between choosing a photo and seeing the boxed, counted result",
                w=134, h=56, size=(16, 7.0))
    steps = [
        ("up", "1. Photo in", ["file_uploader or", "camera_input (1080p)"], "ui"),
        ("tmp", "2. Temporary file", ["work folder; the", "original name is kept"], "data"),
        ("val", "3. validate()", ["type, size, header,", "megapixels"], "core"),
        ("read", "4. read_image()", ["BGR array; HEIC via", "Pillow, EXIF rotation"], "core"),
        ("det", "5. detect()", ["model at the chosen", "confidence, class 0"], "core"),
        ("ann", "6. annotate()", ["boxes and a", "'Products: N' panel"], "core"),
        ("res", "7. Result", ["JPEG, count, seconds;", "temp folder deleted"], "ui"),
    ]
    x = 1.5
    for key, title, lines, layer in steps:
        d.box(key, x, 29, 17, 12, title, lines, layer, title_size=11)
        x += 19
    keys = [s_[0] for s_ in steps]
    for a, b in zip(keys, keys[1:]):
        d.arrow(a, b, sides="rl")
    d.note(1.5, 47, "Typical time on a laptop CPU: 0.1 to 0.2 s for a photo (target: under 5 s).", size=10.5)
    d.box("err", 22, 8, 42, 11, "On any failure", ["the validator's message or errors.friendly_message()", "is shown on the page, never a stack trace"], "data")
    d.arrow("val", "err", "invalid", sides="bt", label_offset=(-4, -1))
    d.box("cache", 70, 8, 40, 11, "Cached detector", ["st.cache_resource: loaded once per server,", "warmed while the page waits for a file"], "ext")
    d.arrow("cache", "det", "reused", sides="tb", label_offset=(4, -1))
    d.legend()
    d.save("03_photo_flow.png")


def video_flow():
    d = Diagram("Video flow", "Every frame gets boxes and a count; the model runs on every 5th frame", w=110, h=60, size=(14.2, 7.8))
    d.box("in", 2, 36, 15, 11, "Video in", [".mp4 or .mov,", "H.264 or HEVC"], "ui")
    d.box("frame", 21, 36, 15, 11, "Next frame", ["Supervision", "frame generator"], "ext")
    d.box("resize", 40, 36, 15, 11, "Fit to 1280 px", ["even size,", "INTER_AREA"], "core")
    d.box("q", 59, 36, 16, 11, "Frame 0, 5, 10...?", ["i % FRAME_STEP", "== 0"], "core", title_size=10.5)
    d.box("det", 81, 44, 17, 9, "detect()", ["new boxes"], "core")
    d.box("reuse", 81, 29.5, 17, 9, "Reuse last boxes", ["frames in between"], "core", title_size=10.5)
    d.box("ann", 81, 13, 17, 10, "annotate()", ["boxes + count;", "count stored"], "core")
    d.box("sink", 59, 13, 16, 10, "VideoSink", ["writes mp4v", "(temporary)"], "ext")
    d.box("enc", 40, 13, 15, 10, "ffmpeg", ["H.264, yuv420p,", "faststart"], "ext")
    d.box("out", 21, 13, 15, 10, "Result", ["video, per-frame", "counts, fps, note"], "ui")
    d.arrow("in", "frame")
    d.arrow("frame", "resize")
    d.arrow("resize", "q")
    d.arrow("q", "det", "yes", sides="rl", label_offset=(0, 0.3))
    d.arrow("q", "reuse", "no", sides="rl", label_offset=(0, -3.2))
    d.arrow("det", "ann", sides="rr", rad=-0.35)
    d.arrow("reuse", "ann", sides="bt")
    d.arrow("ann", "sink", sides="lr")
    d.arrow("sink", "frame", "loop until the last frame", sides="tb", label_offset=(0, 0.4))
    d.arrow("sink", "enc", "after the loop", sides="lr", label_offset=(0, 3.6))
    d.arrow("enc", "out", sides="lr")
    d.note(2, 9, "After the loop, release_memory() hands freed frame buffers back to the OS (about 250 MB per 4K video).\n"
                 "Fewer readable frames than the header claims gives a warning; no readable frames gives a clear error.", size=9.5)
    d.legend(y=0.6)
    d.save("04_video_flow.png")


def validation_flow():
    d = Diagram("Upload checks", "validate() runs before any decoding; the first failing check decides the message", h=74, size=(13, 9.2))
    rows = [
        ("ext", "File type", ".jpg .jpeg .png .heic .heif / .mp4 .mov", "Unsupported file type. Please upload a photo ..."),
        ("empty", "Not empty", "more than 0 bytes", "The file is empty. ..."),
        ("size", "File size", "images 10 MB, video 100 MB", "Image is 19.4 MB. The limit is 10 MB."),
        ("head", "Readable header", "image signature or first video frame", "This file could not be read as an image. ..."),
        ("mp", "Megapixels (images)", "read from the header, limit 100 MP", "Image is 144 megapixels. The limit is 100 ..."),
        ("dur", "Duration (videos)", "frames / fps, limit 30 s", "Video is 31.0 seconds long. The limit is 30 ..."),
    ]
    y = 56
    for key, title, rule, message in rows:
        d.box(key, 4, y, 32, 6.5, title, [rule], "core", title_size=11)
        d.box(key + "_m", 52, y, 44, 6.5, "Message shown", [message], "data", title_size=10)
        d.arrow(key, key + "_m", "fails", sides="rl", label_offset=(0, 0.2))
        y -= 8.4
    for (a, *_), (b, *_) in zip(rows, rows[1:]):
        d.arrow(a, b, "passes", sides="bt", label_offset=(5, -1.2))
    d.box("ok", 4, 4.5, 32, 6, "Accepted: image or video", [], "ui", title_size=11)
    d.arrow(rows[-1][0], "ok", "passes", sides="bt", label_offset=(5, -1.2))
    d.note(52, 10.5, "Why the header checks matter: in testing a 17 KB PNG\ndecoded to 432 MB, and a renamed text file used to\nreach the model.", size=9.5)
    d.save("05_upload_checks.png")


def error_handling():
    d = Diagram("Error handling", "errors.friendly_message() turns every failure into one plain-English line", h=56, size=(13, 7.3))
    cases = [
        ("u", "UserFacingError", "damaged photo or video", "shown as is"),
        ("k", "Forbidden / Unauthorized", "wrong or revoked API key", "Roboflow rejected the API key ..."),
        ("n", "RoboflowAPINotNotFound", "wrong MODEL_ID", "Roboflow could not find the model ..."),
        ("c", "Connection / Timeout", "no internet, first download", "Could not reach Roboflow ..."),
        ("p", "PaymentRequired / UsagePaused", "Roboflow plan limits", "Roboflow refused ... usage limits"),
        ("x", "Anything else", "unexpected bug", "Something went wrong ... see the terminal"),
    ]
    d.box("fm", 38, 21, 20, 12, "friendly_message()", ["src/errors.py", "imports inference", "only when needed"], "core", title_size=10.5)
    y = 42
    for key, exc, cause, msg in cases:
        d.box(key, 2, y, 28, 6, exc, [cause], "ext", title_size=10.5)
        d.box(key + "m", 64, y, 34, 6, msg, [], "data", title_size=9.5)
        d.arrow(key, "fm", sides="rl")
        d.arrow("fm", key + "m", sides="rl")
        y -= 7.4
    d.note(36, 17, "Full details go to the terminal\n(logger.exception), never the page.", size=9.5)
    d.legend(("core", "ext", "data"), y=0.6)
    d.save("06_error_handling.png")


def settings_flow():
    d = Diagram("Where settings come from", "Real environment variables win over .env; Community Cloud secrets become environment variables first",
                w=110, h=54, size=(14, 7.0))
    d.box("secrets", 2, 31, 28, 13, "Community Cloud Secrets", ["ROBOFLOW_API_KEY = \"...\"", "MODEL_ID, PRODUCT_CLASS,", "CONFIDENCE"], "data", title_size=11)
    d.box("load", 36, 32, 30, 12, "st.secrets.load_if_toml_exists()", ["top of app.py, before", "src.config is imported"], "ui", title_size=10)
    d.box("environ", 74, 32, 20, 12, "os.environ", ["real environment", "variables"], "data")
    d.box("dotenv", 2, 14, 28, 11, ".env (laptop)", ["read with dotenv_values(),", "never exported"], "data")
    d.box("config", 62, 13, 30, 13, "src/config.py", ["settings = .env, then os.environ on top", "CONFIDENCE parsed and clamped", "bad values -> WARNINGS"], "core", title_size=11)
    d.box("page", 96, 14, 13, 11, "Page", ["'not set' error", "or warnings"], "ui")
    d.arrow("secrets", "load", sides="rl")
    d.arrow("load", "environ", "copies keys", sides="rl", label_offset=(0, 0.6))
    d.arrow("environ", "config", "wins", sides="bt", label_offset=(2.5, 0))
    d.arrow("dotenv", "config", "fallback", sides="rl", label_offset=(0, 0.6))
    d.arrow("config", "page", sides="rl")
    d.note(2, 9.5, "Why .env is not exported: the inference package parses CONFIDENCE itself at import, so a bad value "
                   "in the environment\nwould crash it before our own checks run.", size=9.5)
    d.legend(y=0.6)
    d.save("07_settings_flow.png")


def deployment_flow():
    d = Diagram("Deployment", "From a commit on the laptop to the private HTTPS link", h=58, size=(13, 7.5))
    d.box("dev", 2, 36, 18, 10, "Laptop", ["commit on develop,", "tests: pytest"], "ui")
    d.box("gh", 26, 36, 20, 10, "GitHub (private)", ["Rahat-Sultan/shelf-counter", "develop -> master"], "data")
    d.box("cc", 52, 25, 26, 27, "Streamlit Community Cloud", ["1. clone the branch", "2. apt: packages.txt", "   (ffmpeg, libgl1, libglib2.0-0)",
                                                             "3. uv + uv.toml: requirements.txt", "   (CPU-only PyTorch)", "4. Python 3.12 (set at create)", "5. Secrets -> environment"], "ext", title_size=11)
    d.box("app", 83, 36, 16, 10, "Live app", ["shelf-counter-rahat", ".streamlit.app"], "ui")
    d.box("users", 83, 18, 16, 10, "Invited viewers", ["sign in by email"], "ui")
    d.arrow("dev", "gh", "git push", sides="rl")
    d.arrow("gh", "cc", "auto-deploy", sides="rl", label_offset=(0, 0.5))
    d.arrow("cc", "app", sides="rl", label_offset=(0, 0.5))
    d.arrow("users", "app", sides="tb")
    d.box("docker", 2, 10, 30, 10, "Other hosts", ["Dockerfile: Python 3.12 bookworm,", "ffmpeg, OpenCV libs, PORT"], "data")
    d.note(36, 19.5, "Lessons: the Python version cannot be changed after creating\nthe app (the default was 3.14, which breaks inference), and\nlivemy.app's free plan had too little memory.", size=9.5)
    d.legend(y=1.2)
    d.save("08_deployment.png")


def phases_timeline():
    d = Diagram("Project phases", "What each phase delivered (9 to 12 October 2026)", h=58, size=(13, 7.6))
    phases = [
        ("0", "Setup", ["venv on Python 3.12,", "CPU PyTorch, pins"]),
        ("1", "Model", ["SKU-110K model wins:", "1,168 vs 692 boxes"]),
        ("2", "Photo script", ["count_image.py,", "0.11 s per photo"]),
        ("3", "Web page", ["upload, slider,", "download"]),
        ("4", "Video", ["every 5th frame,", "H.264, chart, CSV"]),
        ("5", "Errors", ["clear messages,", "bomb and key checks"]),
        ("6", "Docs", ["README, STARTUP,", "DEPLOY, this doc"]),
        ("7", "Phones", ["camera, HEIC, MOV,", "phone layout"]),
        ("8", "Deploy", ["Community Cloud,", "private HTTPS link"]),
    ]
    positions = [(1 + i * 19.6, 32) for i in range(5)] + [(1 + i * 19.6, 12) for i in range(4)]
    for (num, name, lines), (x, y) in zip(phases, positions):
        d.box(f"p{num}", x, y, 17.6, 11, f"{num}. {name}", lines, "ui" if num in ("7", "8") else "core", title_size=11)
    for i in range(1, len(phases)):
        a, b = f"p{phases[i - 1][0]}", f"p{phases[i][0]}"
        d.arrow(a, b, sides="bt" if i == 5 else "rl", rad=0.0)
    d.note(81, 22, "Phases 0 to 6 follow the original brief.\nPhases 7 and 8 were added on 12 October\n(docs/MOBILE_PLAN.md).", size=9.5)
    d.ax.add_patch(FancyBboxPatch((1, 2.2), 2.2, 1.6, boxstyle="round,pad=0,rounding_size=0.4",
                                  edgecolor=LAYERS["core"][0], facecolor=LAYERS["core"][1], linewidth=1.4))
    d.ax.text(4, 3.0, "From the brief", va="center", fontsize=9.5, color=TEXT_2)
    d.ax.add_patch(FancyBboxPatch((20, 2.2), 2.2, 1.6, boxstyle="round,pad=0,rounding_size=0.4",
                                  edgecolor=LAYERS["ui"][0], facecolor=LAYERS["ui"][1], linewidth=1.4))
    d.ax.text(23, 3.0, "Added for phones and hosting", va="center", fontsize=9.5, color=TEXT_2)
    d.save("09_phases.png")


def _style_chart(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(colors=TEXT_2, length=0)
    ax.grid(axis="y", color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def model_comparison_chart():
    """Products found on the 10 test photos (scripts/evaluate.py, 2026-10-09). Magnitude per group: grouped bars."""
    confidences = ["0.3", "0.4", "0.5"]
    peimi = [773, 692, 619]
    sku = [1302, 1168, 1053]
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    _style_chart(ax)
    width, gap = 0.2, 0.02
    xs = range(len(confidences))
    blue, orange = "#2a78d6", "#eb6834"
    for i, (vals, colour, label) in enumerate([(sku, blue, "planogram_sku110k/1 (chosen)"),
                                                (peimi, orange, "retail-shelf-detection-peimi/1")]):
        offs = [x + (i - 0.5) * (width + gap) for x in xs]
        bars = ax.bar(offs, vals, width=width, color=colour, label=label, zorder=2)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 18, f"{v:,}", ha="center", va="bottom", fontsize=10, color=TEXT)
    ax.set_xticks(list(xs), [f"confidence {c}" for c in confidences])
    ax.set_ylabel("Products found on 10 test photos", color=TEXT_2)
    ax.set_ylim(0, 1450)
    ax.legend(frameon=False, loc="upper right", labelcolor=TEXT_2)
    ax.set_title("Model comparison: the SKU-110K model finds about 70% more products", loc="left",
                 fontsize=13, fontweight="bold", color=TEXT, pad=14)
    fig.text(0.125, -0.03, "Boxes found on the 10 test photos (scripts/evaluate.py), checked by eye on the annotated images. "
             "True counts not yet recorded.", fontsize=9, color=MUTED)
    fig.savefig(OUT / "10_model_comparison.png", facecolor=SURFACE, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", OUT / "10_model_comparison.png")


def video_timing_chart():
    """Where the time goes for a 10 s 4K 60 fps clip (602 frames), measured 2026-10-09. One series: one hue."""
    steps = ["Detection (121 calls)", "Writing + H.264 encode", "Decoding 4K frames", "Scaling to 720p", "Drawing boxes"]
    seconds = [12.6, 8.0, 7.6, 4.9, 1.1]
    labels = ["12.6 s", "about 8 s (total minus the rest)", "7.6 s", "4.9 s", "1.1 s"]
    fig, ax = plt.subplots(figsize=(10, 4.4), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    _style_chart(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=1)
    bars = ax.barh(steps[::-1], seconds[::-1], height=0.3, color="#2a78d6", zorder=2)
    for bar, sec, label in zip(bars, seconds[::-1], labels[::-1]):
        ax.text(sec + 0.2, bar.get_y() + bar.get_height() / 2, label, va="center", fontsize=10, color=TEXT)
    ax.set_xlabel("Seconds", color=TEXT_2)
    ax.set_xlim(0, 16)
    ax.tick_params(axis="y", labelcolor=TEXT)
    ax.set_title("Video timing: a 10 s 4K clip takes about 35 s on a laptop CPU", loc="left",
                 fontsize=13, fontweight="bold", color=TEXT, pad=14)
    fig.text(0.02, -0.05, "Detection is fixed by the every-5th-frame rule; the rest scales with resolution and frame rate.",
             fontsize=9, color=MUTED)
    fig.savefig(OUT / "11_video_timing.png", facecolor=SURFACE, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print("wrote", OUT / "11_video_timing.png")


if __name__ == "__main__":
    system_overview()
    module_map()
    image_flow()
    video_flow()
    validation_flow()
    error_handling()
    settings_flow()
    deployment_flow()
    phases_timeline()
    model_comparison_chart()
    video_timing_chart()
