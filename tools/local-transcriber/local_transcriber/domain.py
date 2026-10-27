"""Serializable domain objects; no GUI or ML dependencies."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import math
from pathlib import Path
from uuid import uuid4

MODELS = ('tiny', 'base', 'small', 'medium', 'large-v3')
EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.mp4', '.mov', '.mkv', '.webm'}

def now():
    return datetime.now(timezone.utc).isoformat()

@dataclass
class Settings:
    model_name: str = 'small'
    device: str = 'cpu'
    language: str | None = 'ja'
    output_folder: str = ''
    timestamps: bool = True
    ai_enabled: bool = False
    ai_model: str = ''  # User supplies an available Responses-compatible model ID.
    offline: bool = True
    recognition_mode: str = 'fast'
    cpu_threads: int = 0

    @property
    def compute_type(self):
        return 'int8' if self.device == 'cpu' else 'float16'

    @property
    def beam_size(self):
        return 1 if self.recognition_mode == 'fast' else 5

    @property
    def best_of(self):
        return 1 if self.recognition_mode == 'fast' else 5

    @property
    def temperatures(self):
        return (0.0,) if self.recognition_mode == 'fast' else (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

    def validate(self):
        if self.recognition_mode not in ('fast', 'standard'):
            raise ValueError('認識モードが不正です。')
        if type(self.cpu_threads) is not int or not 0 <= self.cpu_threads <= 128:
            raise ValueError('CPUスレッド数は0〜128の整数にしてください。')
        if self.model_name not in MODELS or self.device not in ('cpu', 'cuda'):
            raise ValueError('モデル・装置の設定が不正です。')
        if self.language not in ('ja', 'en', None):
            raise ValueError('言語の設定が不正です。')
        if not all(isinstance(x, bool) for x in (self.timestamps, self.ai_enabled, self.offline)):
            raise ValueError('設定の形式が不正です。')
        if not isinstance(self.output_folder, str) or not isinstance(self.ai_model, str):
            raise ValueError('設定の形式が不正です。')

@dataclass
class Segment:
    id: int
    start: float
    end: float
    raw_text: str
    edited_text: str | None = None

    @property
    def text(self):
        # An intentionally empty edited string must remain empty.
        return self.raw_text if self.edited_text is None else self.edited_text

    def validate(self):
        if type(self.id) is not int or self.id < 0:
            raise ValueError('セグメントIDが不正です。')
        if not all(type(x) in (int, float) and math.isfinite(x) for x in (self.start, self.end)):
            raise ValueError('時刻は有限数にしてください。')
        if self.start < 0 or self.end < self.start:
            raise ValueError('セグメント時刻が不正です。')
        if not isinstance(self.raw_text, str) or (self.edited_text is not None and not isinstance(self.edited_text, str)):
            raise ValueError('認識・編集テキストの形式が不正です。')

@dataclass
class Project:
    source_path: str
    schema_version: int = 1
    project_id: str = field(default_factory=lambda: str(uuid4()))
    source_hash: str = ''
    duration_seconds: float = 0.0
    model_name: str = 'small'
    device: str = 'cpu'
    language: str | None = 'ja'
    compute_type: str = 'int8'
    beam_size: int = 5
    best_of: int = 5
    temperature: list[float] = field(default_factory=lambda: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    recognition_mode: str = 'standard'
    cpu_threads: int = 0
    processing_seconds: float | None = None
    vad_filter: bool = True
    word_timestamps: bool = False
    task: str = 'transcribe'
    detected_language: str | None = None
    segments: list[Segment] = field(default_factory=list)
    ai_outputs: list[dict] = field(default_factory=list)
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)
    status: str = '待機中'
    error: str = ''
    size_bytes: int = 0

    def apply_settings(self, settings):
        settings.validate()
        self.model_name = settings.model_name
        self.device = settings.device
        self.compute_type = settings.compute_type
        self.language = settings.language
        self.recognition_mode = settings.recognition_mode
        self.cpu_threads = settings.cpu_threads
        self.beam_size = settings.beam_size
        self.best_of = settings.best_of
        self.temperature = list(settings.temperatures)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1:
            raise ValueError('未対応のプロジェクト形式です。')
        data = dict(data)
        if not isinstance(data.get('segments'), list) or not isinstance(data.get('ai_outputs'), list):
            raise ValueError('プロジェクトの配列形式が不正です。')
        data['segments'] = [Segment(**s) for s in data['segments']]
        p = cls(**data)
        if not isinstance(p.source_path, str) or not isinstance(p.project_id, str) or not p.project_id:
            raise ValueError('ファイル参照または識別子が不正です。')
        if any(c not in '0123456789abcdef-' for c in p.project_id.lower()):
            raise ValueError('識別子が不正です。')
        if type(p.duration_seconds) not in (int, float) or not math.isfinite(p.duration_seconds) or p.duration_seconds < 0:
            raise ValueError('再生時間が不正です。')
        ids = set()
        for s in p.segments:
            s.validate()
            if s.id in ids:
                raise ValueError('セグメントIDが重複しています。')
            ids.add(s.id)
        p.segments.sort(key=lambda s: (s.start, s.end, s.id))
        for a in p.ai_outputs:
            if not isinstance(a, dict) or not isinstance(a.get('text'), str):
                raise ValueError('AI結果の形式が不正です。')
        Settings(model_name=p.model_name, device=p.device, language=p.language,
                 recognition_mode=p.recognition_mode, cpu_threads=p.cpu_threads).validate()
        if p.processing_seconds is not None and (type(p.processing_seconds) not in (int, float)
                or not math.isfinite(p.processing_seconds) or p.processing_seconds < 0):
            raise ValueError('処理時間が不正です。')
        if p.status not in ('完了', '失敗', 'キャンセル', '待機中'):
            p.status = 'キャンセル'  # Interrupted checkpoint, never auto-restart.
        return p

    def text(self, raw=False):
        return '\n'.join(s.raw_text if raw else s.text for s in sorted(self.segments, key=lambda x: (x.start, x.id)))

    @property
    def filename(self):
        return Path(self.source_path).name
