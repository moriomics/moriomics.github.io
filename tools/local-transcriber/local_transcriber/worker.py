"""Spawn-safe entry point. Messages travel only through a private multiprocessing pipe."""
import logging
import os
import sys
from .domain import Project, Settings
from .media import AppError, Cancelled, check_cancel, probe


def worker_main(connection, cancel, kind, payload, temporary_dir):
    if sys.platform != 'win32':
        os.setsid()
    # Never persist library exceptions, HTTP bodies, transcripts or credentials.
    logging.disable(logging.CRITICAL)
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    def emit(event, data):
        connection.send((event, data))
    try:
        check_cancel(cancel)
        if kind == 'probe':
            emit('result', probe(payload['path'], cancel))
        elif kind == 'download':
            from .models import install_model
            emit('result', install_model(payload['model_name'], cancel))
        elif kind == 'transcribe':
            from .engine import transcribe
            p = Project.from_dict(payload['project'])
            result = transcribe(p, Settings(**payload['settings']), temporary_dir, emit, cancel)
            emit('result', result.to_dict())
        elif kind == 'ai':
            from .ai import generate
            emit('result', generate(payload['kind'], payload['text'], Settings(**payload['settings'])))
        else:
            raise AppError('未対応の処理です。')
    except Cancelled:
        emit('cancelled', None)
    except Exception as exc:
        if isinstance(exc, AppError):
            message = str(exc)
        elif kind == 'ai':
            message = 'AI処理に失敗しました。キー・モデルID・利用枠・接続を確認してください。'
        elif kind == 'download':
            message = 'モデル取得に失敗しました。接続・空き容量を確認し、再取得してください。'
        else:
            message = '処理に失敗しました。ファイル・空き容量・依存ライブラリを確認してください。'
        emit('error', {'message': message, 'code': type(exc).__name__})
    finally:
        connection.close()
