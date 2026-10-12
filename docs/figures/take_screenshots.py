"""Takes the app screenshots used in docs/PROJECT_DOCUMENTATION.md, with headless Google Chrome.

1. Start the app:  streamlit run app.py --server.port 8503 --server.headless true
2. From the shelf-counter folder:
       python docs/figures/take_screenshots.py --photo path/to/shelf.jpg --video path/to/shelf.mp4

Writes PNG files to docs/images/. Needs Google Chrome; websocket-client is installed with the project's packages.
Use photos and videos you own: the screenshots are committed to the repository.
"""

import argparse
import base64
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket

OUT = Path(__file__).resolve().parent.parent / "images"


class Browser:
    """One headless Chrome tab driven over the DevTools protocol."""

    def __init__(self, width, height, port=9335):
        self.profile = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.proc = subprocess.Popen(
            ["google-chrome", "--headless=new", "--no-first-run", "--disable-gpu", f"--remote-debugging-port={port}",
             f"--remote-allow-origins=http://127.0.0.1:{port}", f"--user-data-dir={self.profile.name}",
             f"--window-size={width},{height}", "--use-fake-device-for-media-stream", "--use-fake-ui-for-media-stream",
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                break
            except OSError:
                time.sleep(0.2)
        page = next(t for t in tabs if t["type"] == "page")
        self.ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=180, origin=f"http://127.0.0.1:{port}")
        self.n = 0
        self.call("Page.enable")
        self.call("Runtime.enable")
        phone = width < 600
        self.call("Emulation.setDeviceMetricsOverride", width=width, height=height,
                  deviceScaleFactor=2 if phone else 1, mobile=phone)

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.n:
                return message.get("result", {})

    def js(self, expression):
        return self.call("Runtime.evaluate", expression=expression, returnByValue=True)["result"].get("value")

    def open(self, url, wait=12):
        self.call("Page.navigate", url=url)
        time.sleep(wait)

    def upload(self, path, wait):
        root = self.call("DOM.getDocument", depth=-1, pierce=True)["root"]["nodeId"]
        node = self.call("DOM.querySelector", nodeId=root, selector="input[type=file]")["nodeId"]
        self.call("DOM.setFileInputFiles", files=[str(Path(path).resolve())], nodeId=node)
        time.sleep(wait)

    def click(self, text, wait=4):
        found = self.js(
            "(() => { const el = [...document.querySelectorAll('button, [role=button], label, p')]"
            f".find(e => e.innerText && e.innerText.trim().includes({json.dumps(text)}));"
            " if (!el) return false; (el.closest('button') || el).click(); return true; })()"
        )
        time.sleep(wait)
        return found

    def shot(self, name):
        OUT.mkdir(parents=True, exist_ok=True)
        data = self.call("Page.captureScreenshot", format="png")["data"]
        (OUT / name).write_bytes(base64.b64decode(data))
        print("wrote", OUT / name)

    def close(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.profile.cleanup()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8503")
    parser.add_argument("--photo", required=True)
    parser.add_argument("--video", required=True)
    args = parser.parse_args()

    desktop = Browser(1280, 1480)
    desktop.open(args.url)
    desktop.shot("12_ui_desktop_start.png")
    desktop.upload(args.photo, wait=15)
    desktop.shot("13_ui_desktop_photo_result.png")
    desktop.close()

    phone = Browser(390, 1500)
    phone.open(args.url)
    phone.upload(args.photo, wait=15)
    phone.shot("14_ui_phone_photo_result.png")
    phone.click("Take a photo", wait=6)
    phone.shot("15_ui_phone_camera.png")
    phone.click("Detection settings", wait=2)
    phone.shot("16_ui_phone_settings.png")
    phone.close()

    video = Browser(1280, 1900)
    video.open(args.url)
    video.upload(args.video, wait=60)
    video.shot("17_ui_desktop_video_result.png")
    video.close()


if __name__ == "__main__":
    main()
