import hashlib
from pathlib import Path
import shutil
import subprocess
import threading
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from local_transcriber import engine
from local_transcriber.domain import Project, Settings
from local_transcriber.media import probe, normalize, source_hash, AppError, Cancelled, binary
from local_transcriber.models import model_ready

@pytest.fixture
def media_files(tmp_path):
    try:
        ffmpeg = binary('ffmpeg')
        binary('ffprobe')
    except AppError:
        pytest.skip('FFmpeg/ffprobe not installed')
    files = []
    for ext in ('wav', 'mp3', 'm4a', 'flac', 'mp4', 'mov', 'mkv', 'webm'):
        path = tmp_path / ('音声.' + ext)
        subprocess.run([ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.3', '-y', str(path)], check=True, capture_output=True)
        files.append(path)
    silent = tmp_path / 'no_audio.mp4'
    subprocess.run([ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=64x64:d=0.2', '-an', '-c:v', 'mpeg4', '-y', str(silent)], check=True, capture_output=True)
    return files, silent

def test_all_formats_probe_and_decode(media_files, tmp_path):
    files, no_audio = media_files
    for path in files:
        metadata = probe(path)
        assert metadata['duration_seconds'] > 0
        output = tmp_path / 'normalized.wav'
        normalize(path, output, metadata['audio_index'])
        assert probe(output)['duration_seconds'] > 0
        assert source_hash(path) == hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(AppError, match='音声ストリーム'):
        probe(no_audio)
    bad = tmp_path / 'broken.wav'
    bad.write_bytes(b'not audio')
    with pytest.raises(AppError):
        probe(bad)
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        normalize(files[0], tmp_path / 'cancel.wav', 0, cancel)

def test_missing_model_never_downloads(monkeypatch, tmp_path):
    p = Project(str(tmp_path / 'source.wav'))
    Path(p.source_path).write_bytes(b'fake')
    monkeypatch.setattr(engine, 'probe', lambda *args: {'duration_seconds': 1., 'size_bytes': 4, 'audio_index': 0})
    assert not model_ready('small')
    import faster_whisper.utils
    download = Mock(side_effect=AssertionError('must not download'))
    monkeypatch.setattr(faster_whisper.utils, 'download_model', download)
    with pytest.raises(AppError, match='モデル未導入'):
        engine.transcribe(p, Settings(), tmp_path, lambda *x: None, threading.Event())
    download.assert_not_called()

@pytest.mark.parametrize('mode,beam,temps', [('fast', 1, (0.0,)), ('standard', 5, (0.0, .2, .4, .6, .8, 1.0))])
def test_recognition_configuration_and_original_preserved(monkeypatch, tmp_path, mode, beam, temps):
    import faster_whisper
    source = tmp_path / 'source.wav'
    source.write_bytes(b'original')
    monkeypatch.setattr(engine, 'probe', lambda *args: {'duration_seconds': 2., 'size_bytes': 8, 'audio_index': 0})
    monkeypatch.setattr(engine, 'model_ready', lambda *args: True)
    monkeypatch.setattr(engine, 'normalize', lambda *args: None)
    model = Mock()
    model.transcribe.return_value = (iter([SimpleNamespace(id=0, start=0., end=1.5, text=' 日本語 ')]), SimpleNamespace(language='ja'))
    cls = Mock(return_value=model)
    monkeypatch.setattr(faster_whisper, 'WhisperModel', cls)
    events = []
    p = engine.transcribe(Project(str(source)), Settings(recognition_mode=mode), tmp_path, lambda *e: events.append(e), threading.Event())
    assert cls.call_args.kwargs == {'device': 'cpu', 'compute_type': 'int8', 'local_files_only': True, 'cpu_threads': 0}
    assert model.transcribe.call_args.kwargs == {'language': 'ja', 'task': 'transcribe', 'beam_size': beam, 'best_of': beam, 'temperature': temps, 'vad_filter': True, 'word_timestamps': False}
    assert p.segments[0].raw_text == '日本語' and p.segments[0].edited_text is None
    assert p.status == '完了' and source.read_bytes() == b'original'
    assert any(e[0] == 'segment' for e in events)
    assert p.recognition_mode == mode and p.beam_size == beam
    assert p.temperature == list(temps) and p.processing_seconds >= 0

def test_model_install_is_explicit_and_marker_written(monkeypatch):
    import faster_whisper.utils
    from local_transcriber.models import install_model, model_path, REQUIRED
    def fake_download(name, output_dir):
        folder = Path(output_dir)
        for file in REQUIRED:
            (folder / file).write_text('test')
        return output_dir
    fake = Mock(side_effect=fake_download)
    monkeypatch.setattr(faster_whisper.utils, 'download_model', fake)
    assert not model_ready('tiny')
    install_model('tiny')
    fake.assert_called_once()
    assert model_ready('tiny')
