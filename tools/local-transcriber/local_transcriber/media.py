from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time
from .domain import EXTENSIONS

class AppError(Exception):
    """Only fixed, safe user-facing messages should be placed here."""

class Cancelled(Exception):
    pass


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise Cancelled()


def binary(name):
    roots = [Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1])) / 'vendor' / 'ffmpeg',
             Path(sys.executable).parent / 'vendor' / 'ffmpeg']
    for root in roots:
        candidate = root / (name + ('.exe' if sys.platform == 'win32' else ''))
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if not found:
        raise AppError(f'{name}がありません。vendor/ffmpegへ配置するかPATHへ追加してください。')
    return found


def run_media(args, cancel=None, timeout=60):
    # No shell, no unbounded stderr, and no source text in application logs.
    creation = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    with subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, creationflags=creation) as proc:
        start = time.monotonic()
        try:
            while True:
                check_cancel(cancel)
                try:
                    out, _ = proc.communicate(timeout=.15)
                    break
                except subprocess.TimeoutExpired:
                    if time.monotonic() - start > timeout:
                        raise AppError('メディア処理がタイムアウトしました。ファイルを確認してください。')
            if proc.returncode:
                raise AppError('メディアを読み取れません。破損・未対応コーデックなどを確認してください。')
            return out
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


def probe(path, cancel=None):
    path = Path(path)
    if path.suffix.lower() not in EXTENSIONS:
        raise AppError('対応していないファイル拡張子です。')
    if not path.is_file():
        raise AppError('元ファイルが見つかりません。')
    raw = run_media([binary('ffprobe'), '-v', 'error', '-show_entries',
                     'format=duration:stream=index,codec_type,duration', '-of', 'json', str(path.resolve())], cancel, 30)
    data = json.loads(raw)
    audio = next((s for s in data.get('streams', []) if s.get('codec_type') == 'audio'), None)
    if audio is None:
        raise AppError('音声ストリームがありません。このファイルは処理できません。')
    try:
        duration = float(audio.get('duration') or data.get('format', {}).get('duration', 0))
    except (ValueError, TypeError):
        duration = 0.0
    if not math.isfinite(duration) or duration < 0:
        duration = 0.0
    return {'duration_seconds': duration, 'size_bytes': path.stat().st_size, 'audio_index': audio['index']}


def source_hash(path, cancel=None):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        while block := f.read(1024 * 1024):
            check_cancel(cancel)
            digest.update(block)
    return digest.hexdigest()


def normalize(path, output, audio_index, cancel=None):
    run_media([binary('ffmpeg'), '-nostdin', '-v', 'error', '-y', '-i', str(Path(path).resolve()),
               '-map', f'0:{audio_index}', '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(output)],
              cancel, timeout=24 * 3600)
