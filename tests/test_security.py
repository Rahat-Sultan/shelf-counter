import os
import subprocess
import sys
import tomllib
from pathlib import Path

from PIL import Image

from src import config
from src.validator import validate

ROOT = Path(__file__).resolve().parent.parent


def test_rejects_decompression_bomb(tmp_path):
    f = tmp_path / "bomb.png"
    Image.new("1", (12000, 12000)).save(f, optimize=True)  # about 17 KB on disk, 144 MP when decoded
    assert f.stat().st_size < 100_000
    result = validate(f)
    assert not result.ok
    assert "megapixels" in result.message


def test_rejects_image_too_big_for_pillow(tmp_path):
    f = tmp_path / "huge.png"
    Image.new("1", (20000, 20000)).save(f, optimize=True)  # 400 MP, above Pillow's own bomb limit
    result = validate(f)
    assert not result.ok
    assert "megapixels" in result.message


def test_accepts_image_under_megapixel_limit(tmp_path, monkeypatch):
    f = tmp_path / "ok.png"
    Image.new("RGB", (2000, 1000)).save(f)
    monkeypatch.setattr(config, "MAX_IMAGE_MEGAPIXELS", 2)
    assert validate(f).ok


def test_page_modules_do_not_import_inference():
    """Importing inference takes 10 to 20 seconds; the page must draw before that happens."""
    code = "import sys, src.config, src.validator, src.annotator, src.processors, src.errors; print('inference' in sys.modules)"
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"


def test_model_cache_is_not_in_tmp():
    code = "import os, src; print(os.environ['MODEL_CACHE_DIR'])"
    env = {k: v for k, v in os.environ.items() if k != "MODEL_CACHE_DIR"}
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    assert not out.stdout.strip().startswith("/tmp")


def test_server_only_listens_on_localhost():
    settings = tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text())
    assert settings["server"]["address"] == "localhost"
    assert settings["server"]["maxUploadSize"] == config.MAX_VIDEO_MB


def test_env_and_scratch_outputs_ignored_but_samples_tracked():
    def ignored(path):
        return subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0

    assert ignored(".env")
    assert ignored("outputs/anything.jpg")
    assert not ignored("samples/outputs/01_clean_shelf_annotated.jpg")
