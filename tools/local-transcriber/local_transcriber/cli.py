"""Stage 1: local-only command line interface."""
import argparse
import logging
from pathlib import Path
import tempfile
import threading
from .domain import Project, Settings
from .engine import transcribe
from .models import install_model
from .storage import save_project, export_project


def main():
    parser = argparse.ArgumentParser(description='Local Transcriber CLI（ローカル専用）')
    sub = parser.add_subparsers(dest='command', required=True)
    download = sub.add_parser('download', help='明示的にモデルを取得（ネット接続が必要）')
    download.add_argument('model', choices=['tiny', 'base', 'small', 'medium', 'large-v3'])
    t = sub.add_parser('transcribe')
    t.add_argument('source', type=Path)
    t.add_argument('--model', default='small')
    t.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    t.add_argument('--language', choices=['ja', 'en', 'auto'], default='ja')
    t.add_argument('--mode', choices=['fast', 'standard'], default='fast')
    t.add_argument('--cpu-threads', type=int, default=0)
    t.add_argument('--output', type=Path, required=True, help='プロジェクトJSON保存先')
    t.add_argument('--overwrite', action='store_true', help='既存出力の置換を明示的に許可')
    args = parser.parse_args()
    logging.disable(logging.CRITICAL)
    if args.command == 'download':
        install_model(args.model)
        print('モデル取得完了')
        return 0
    txt = args.output.with_suffix('.txt')
    if not args.overwrite and any(p.exists() for p in (args.output, txt)):
        parser.error('保存先が存在します。別名か--overwriteを指定してください。')
    if args.output.suffix.lower() != '.json':
        parser.error('--outputは.jsonにしてください。')
    settings = Settings(model_name=args.model, device=args.device,
                        language=None if args.language == 'auto' else args.language,
                        recognition_mode=args.mode, cpu_threads=args.cpu_threads)
    project = Project(str(args.source.resolve()))
    def emit(kind, data):
        if kind == 'stage':
            print(data)
        elif kind == 'segment':
            print(f'処理済みセグメント: {data["id"] + 1}')
    try:
        with tempfile.TemporaryDirectory(prefix='LocalTranscriber-') as tmp:
            project = transcribe(project, settings, tmp, emit, threading.Event())
        save_project(project, args.output)
        export_project(project, txt)
        print('保存完了')
        return 0
    except KeyboardInterrupt:
        print('キャンセルしました。')
        return 130
    except Exception as exc:
        from .media import AppError
        print(str(exc) if isinstance(exc, AppError) else '処理に失敗しました。ファイル・モデル・依存関係を確認してください。')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
