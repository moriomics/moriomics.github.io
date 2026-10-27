from pathlib import Path
from .domain import MODELS
from .storage import app_home, write_json
from .media import AppError, check_cancel

REQUIRED = ('model.bin', 'config.json', 'tokenizer.json')


def model_path(name):
    if name not in MODELS:
        raise AppError('未対応のモデル名です。')
    return app_home() / 'models' / name


def model_ready(name):
    path = model_path(name)
    return (path / '.complete.json').is_file() and all((path / x).is_file() and (path / x).stat().st_size > 0 for x in REQUIRED)


def install_model(name, cancel=None):
    # Only called by explicit UI/CLI download command. No transcription path calls this.
    check_cancel(cancel)
    from faster_whisper.utils import download_model
    folder = model_path(name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / '.complete.json').unlink(missing_ok=True)
    download_model(name, output_dir=str(folder))
    check_cancel(cancel)
    if not all((folder / f).is_file() for f in REQUIRED):
        raise AppError('モデルファイルが不足しています。再取得してください。')
    write_json(folder / '.complete.json', {'model_name': name, 'complete': True})
    return str(folder)


def gpu_check():
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() < 1:
            raise AppError('CUDA対応GPUが検出されません。CPUへ切り替えてください。')
        types = ctranslate2.get_supported_compute_types('cuda')
        if 'float16' not in types:
            raise AppError('GPUのfloat16に対応していません。CPUへ切り替えてください。')
    except AppError:
        raise
    except Exception:
        raise AppError('GPUを初期化できません。NVIDIAドライバー・CUDA・cuDNNを確認するかCPUへ切り替えてください。') from None
