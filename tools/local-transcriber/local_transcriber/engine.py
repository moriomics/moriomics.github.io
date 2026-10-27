from pathlib import Path
import os
import time
from .domain import Segment
from .media import AppError, check_cancel, probe, source_hash, normalize
from .models import gpu_check, model_path, model_ready


def transcribe(project, settings, temporary_dir, emit, cancel):
    settings.validate()
    started = time.perf_counter()
    project.apply_settings(settings)
    # Also protects libraries imported after this point from implicit network fallback.
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    emit('stage', '前処理中')
    check_cancel(cancel)
    metadata = probe(project.source_path, cancel)
    project.duration_seconds = metadata['duration_seconds']
    project.size_bytes = metadata['size_bytes']
    project.source_hash = source_hash(project.source_path, cancel)
    if not model_ready(settings.model_name):
        raise AppError('モデル未導入です。オフラインモードを解除し「モデル取得」を実行してください。')
    if settings.device == 'cuda':
        gpu_check()
    wav = Path(temporary_dir) / 'audio.wav'
    normalize(project.source_path, wav, metadata['audio_index'], cancel)
    check_cancel(cancel)
    emit('metadata', {'duration_seconds': project.duration_seconds, 'size_bytes': project.size_bytes,
                      'source_hash': project.source_hash})
    emit('stage', '認識中')
    from faster_whisper import WhisperModel
    try:
        model = WhisperModel(str(model_path(settings.model_name)), device=settings.device,
                             compute_type=settings.compute_type, local_files_only=True,
                             cpu_threads=settings.cpu_threads)
        segments, info = model.transcribe(str(wav), language=settings.language, task='transcribe',
                                         beam_size=settings.beam_size, best_of=settings.best_of,
                                         temperature=settings.temperatures, vad_filter=True, word_timestamps=False)
        project.detected_language = info.language
        project.segments = []
        for s in segments:
            check_cancel(cancel)
            segment = Segment(s.id, s.start, s.end, s.text.strip())
            segment.validate()
            project.segments.append(segment)
            emit('segment', segment.__dict__)
        check_cancel(cancel)
    except AppError:
        raise
    except Exception as exc:
        from .media import Cancelled
        if isinstance(exc, Cancelled):
            raise
        if settings.device == 'cuda':
            raise AppError('GPU認識に失敗しました。CUDA/cuDNN DLL・GPUメモリを確認するかCPUへ切り替えてください。') from None
        raise AppError('音声認識に失敗しました。モデルの破損・メモリ不足・依存ライブラリを確認してください。') from None
    project.model_name = settings.model_name
    project.device = settings.device
    project.compute_type = settings.compute_type
    project.language = settings.language
    project.processing_seconds = time.perf_counter() - started
    project.status = '完了'
    project.error = ''
    return project
