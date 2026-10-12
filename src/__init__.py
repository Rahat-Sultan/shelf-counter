import os
from pathlib import Path

# The inference package caches downloaded models in /tmp/cache by default. /tmp is wiped on reboot on many
# systems, so the model would be downloaded again and the app would not work offline after a restart.
# This runs before any src module imports inference, which reads the setting at import time.
os.environ.setdefault("MODEL_CACHE_DIR", str(Path.home() / ".cache" / "shelf-counter" / "models"))
