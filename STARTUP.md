# Starting the project

Step-by-step setup for a fresh laptop, from nothing to a running app. Plan on 10 to 15 minutes, most of it
waiting for the install in step 4. Commands are for Linux and macOS; Windows differences are noted.

## 1. Check what you need

| You need | Check with | Get it |
| --- | --- | --- |
| Python 3.10, 3.11 or 3.12 | `python3.12 --version` | [python.org](https://www.python.org/downloads/) |
| ffmpeg (for video) | `ffmpeg -version` | `sudo apt install ffmpeg` (Ubuntu), `brew install ffmpeg` (macOS), [ffmpeg.org](https://ffmpeg.org/download.html) (Windows) |
| A free Roboflow account | | [roboflow.com](https://roboflow.com) |
| About 3 GB of free disk space | | |

Python 3.13 and newer do not work yet, because the `inference` package does not support them. If your
default `python3` is newer, install 3.12 alongside it and use `python3.12` in step 3. No GPU is needed.

## 2. Get the code

```bash
git clone https://github.com/Rahat-Sultan/shelf-counter.git
cd shelf-counter
```

Every command from here on runs inside the `shelf-counter` folder.

## 3. Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Windows: `py -3.12 -m venv .venv`, then `.venv\Scripts\activate`.

Your prompt now starts with `(.venv)`. Activate it again in every new terminal.

## 4. Install the packages

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This downloads about 1.5 GB and takes 5 to 10 minutes. It installs the CPU-only build of PyTorch on purpose.

Check that it worked:

```bash
python -c "import inference, supervision, streamlit; print('ok')"
```

It should print `ok`. Warnings about SAM, SAM3 or YOLO-World models are normal and can be ignored.

## 5. Add your Roboflow API key

```bash
cp .env.example .env
```

Windows: `copy .env.example .env`.

In Roboflow, open your workspace settings, go to **API Keys**, and copy the private API key. Open `.env` and
replace `your_api_key_here` with it:

```
ROBOFLOW_API_KEY=paste-your-key-here
MODEL_ID=planogram_sku110k/1
CONFIDENCE=0.3
PRODUCT_CLASS=0
```

Leave the other three lines as they are. Do not use quotes or spaces around `=`, and save the file.
`.env` is ignored by Git, so the key is never committed.

## 6. Run the tests

```bash
pytest -q
```

All tests should pass. They do not call Roboflow, so they work before the key is checked.

## 7. Start the app

```bash
streamlit run app.py
```

This only works while the venv from step 3 is active. Without activating it, run `.venv/bin/streamlit run app.py`
(Windows: `.venv\Scripts\streamlit run app.py`).

It opens http://localhost:8501 in your browser. If it does not, open that address yourself. The title shows within
a few seconds, then the page says "Loading the model..." for 10 to 30 seconds, longest on the first start after a
reboot. Once that message is gone, uploads are fast.

To open it from a phone on the same Wi-Fi, use the "Network URL" that `streamlit run` prints. To keep the app
on this laptop only, run `streamlit run app.py --server.address localhost`.

## 8. Try it

1. Upload a shelf photo (`.jpg`, `.png` or an iPhone `.heic`, up to 10 MB). The first upload downloads the model
   (about 7.5 MB), so it takes a few seconds. After that, photos take well under a second.
2. Check the boxes and the **Products found** count, then use **Download result**.
3. Upload a short shelf video (`.mp4` or an iPhone `.mov`, up to 30 seconds and 100 MB). A progress bar shows
   while it runs. You get the annotated video, a per-frame chart and a CSV of counts.
4. Select **Take a photo** at the top to use the laptop's webcam instead of a file. Allow camera access when the
   browser asks.
5. Open **Detection settings** and move the **Confidence threshold** slider to see how the count changes.

To stop the app, press `Ctrl+C` in the terminal.

## Optional: command-line tools

```bash
python -m scripts.count_image path/to/shelf.jpg          # box and count one or more photos
python -m scripts.evaluate --images path/to/photos       # compare models or confidence values
```

Results are saved in `outputs/`.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| `No matching distribution found for inference` or `torch` | Your Python is too new or too old. Recreate the venv with Python 3.12 (step 3) |
| `Disk quota exceeded` or `No space left on device` during install | `/tmp` is too small. Run `mkdir -p ~/.cache/pip-tmp` and then `TMPDIR=~/.cache/pip-tmp pip install -r requirements.txt` |
| `Error: Invalid value: File does not exist: app.py` | You are in the wrong folder. `cd` into `shelf-counter` (the folder with `app.py`), then run the command again |
| `streamlit: command not found` or `ModuleNotFoundError: No module named 'inference'` | The venv is not active. Run `source .venv/bin/activate` (step 3), or use `.venv/bin/streamlit run app.py` |
| Browser shows a blank or grey page | Check the terminal: if `streamlit run` printed an error, fix that first. Otherwise wait 30 seconds; the first start after a reboot is slow. Make sure you opened http://localhost:8501 |
| Page says the API key or MODEL_ID is not set | Check that `.env` exists in this folder, is saved, and has your real key (step 5). Restart the app |
| Page says Roboflow rejected the API key | The key is wrong or was copied with extra characters. Copy it again from Roboflow and restart |
| Page says it could not reach Roboflow | Check your internet connection. Once the model has been downloaded (to `~/.cache/shelf-counter/models`), the app also works offline |
| Video downloads but does not play in the page | ffmpeg is missing. Install it (step 1) and restart the app |
| `Port 8501 is already in use` | Another copy is running. Stop it, or run `streamlit run app.py --server.port 8502` |

More detail is in the [README](README.md) and in [docs/](docs/).
