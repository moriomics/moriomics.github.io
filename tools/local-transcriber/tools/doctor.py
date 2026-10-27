"""Read-only environment diagnostics. Does not read credentials or use the network."""
import importlib.metadata
import json
import platform
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from local_transcriber.media import binary
from local_transcriber.models import model_ready
from local_transcriber.domain import MODELS

report = {'python': platform.python_version(), 'os': platform.platform(),
          'architecture': platform.architecture()[0], 'packages': {}, 'binaries': {}, 'models': {}}
for name in ('PySide6', 'faster-whisper', 'ctranslate2', 'huggingface-hub', 'openai', 'keyring', 'python-docx'):
    try:
        report['packages'][name] = importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        report['packages'][name] = 'NOT INSTALLED'
for name in ('ffmpeg', 'ffprobe'):
    try:
        report['binaries'][name] = binary(name)
    except Exception:
        report['binaries'][name] = 'NOT FOUND'
report['models'] = {name: model_ready(name) for name in MODELS}
print(json.dumps(report, ensure_ascii=False, indent=2))
