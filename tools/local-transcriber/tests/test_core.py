from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import json
import pytest
from local_transcriber.domain import Project, Segment, Settings
from local_transcriber.storage import export_project, load_project, save_project, atomic_target, timestamp, save_settings, load_settings
from local_transcriber.ai import generate
from local_transcriber.media import AppError
from tools.cer import cer, normalize

@pytest.fixture
def project(tmp_path):
    return Project(str(tmp_path / '元音声.wav'), duration_seconds=3.0,
        segments=[Segment(0, .125, 1.5, '原文', '編集文'), Segment(1, 2., 3., '二行目', '')],
        ai_outputs=[{'text': 'AI生成', 'kind': '要約', 'input_text': '編集文'}], status='完了')

def test_roundtrip_without_source_and_all_exports(project, tmp_path):
    target = tmp_path / 'プロジェクト.json'
    save_project(project, target)
    restored = load_project(target)
    assert not Path(restored.source_path).exists()
    assert restored.text() == '編集文\n'
    assert restored.text(raw=True) == '原文\n二行目'
    assert restored.ai_outputs[0]['text'] == 'AI生成'
    for ext in ('txt', 'srt', 'json', 'docx'):
        out = tmp_path / ('result.' + ext)
        export_project(restored, out)
        assert out.stat().st_size > 0
    assert '00:00:00,125 --> 00:00:01,500' in (tmp_path / 'result.srt').read_text(encoding='utf-8')
    assert '\n2\n' not in (tmp_path / 'result.srt').read_text(encoding='utf-8')
    from docx import Document
    text = '\n'.join(p.text for p in Document(tmp_path / 'result.docx').paragraphs)
    assert '元音声.wav' in text and '編集文' in text and '作成日' in text
    export_project(restored, tmp_path / 'plain.txt', False)
    assert (tmp_path / 'plain.txt').read_text(encoding='utf-8') == '編集文\n'

def test_source_never_overwritten(project):
    with pytest.raises(ValueError):
        save_project(project, project.source_path)
    with pytest.raises(ValueError):
        export_project(project, project.source_path)

def test_atomic_failure_preserves_prior_file(tmp_path):
    p = tmp_path / 'result.txt'
    p.write_text('prior')
    with pytest.raises(RuntimeError):
        with atomic_target(p) as tmp:
            tmp.write_text('partial')
            raise RuntimeError()
    assert p.read_text() == 'prior'
    assert list(tmp_path.iterdir()) == [p]

@pytest.mark.parametrize('change', [
    {'schema_version': 2}, {'duration_seconds': float('nan')}, {'project_id': '../../x'},
    {'segments': [{'id': 0, 'start': -1, 'end': 0, 'raw_text': 'x'}]},
    {'segments': [{'id': 0, 'start': 2, 'end': 1, 'raw_text': 'x'}]},
    {'segments': [{'id': 0, 'start': 0, 'end': 1, 'raw_text': 'x'}] * 2},
])
def test_invalid_project_is_rejected(project, change):
    data = project.to_dict()
    data.update(change)
    with pytest.raises((ValueError, TypeError)):
        Project.from_dict(data)

def test_settings_have_no_key():
    settings = Settings()
    save_settings(settings)
    assert load_settings() == settings
    assert 'key' not in json.dumps(asdict(settings))
    assert not settings.ai_enabled and settings.offline
    assert timestamp(59.9998, True) == '00:01:00,000'
    assert timestamp(3600) == '01:00:00.000'

def test_ai_request_exact_preview_and_no_overwrite(project):
    original = project.to_dict()
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(status='completed', output_text='要約結果')
    text = project.text()
    out = generate('要約', text, Settings(ai_enabled=True, offline=False, ai_model='user-selected-model'), client=client)
    call = client.responses.create.call_args.kwargs
    assert call['input'] == text and call['store'] is False
    assert '記載なし' in call['instructions']
    assert 'source_path' not in call and 'tools' not in call
    assert out['input_text'] == text and out['text'] == '要約結果'
    assert project.to_dict() == original

@pytest.mark.parametrize('settings,text', [(Settings(), 'x'),
    (Settings(ai_enabled=True, offline=True), 'x'),
    (Settings(ai_enabled=True, offline=False, ai_model='m'), ''),
    (Settings(ai_enabled=True, offline=False, ai_model='m'), 'x' * 60001)])
def test_ai_guards_never_call_network(settings, text):
    client = Mock()
    with pytest.raises(AppError):
        generate('要約', text, settings, client=client)
    client.responses.create.assert_not_called()

def test_ai_incomplete_is_not_saved():
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(status='incomplete', output_text='partial')
    with pytest.raises(AppError):
        generate('要約', '本文', Settings(ai_enabled=True, offline=False, ai_model='m'), client=client)

def test_srt_sorted(project, tmp_path):
    project.segments = [Segment(4, 4, 5, '後'), Segment(0, 0, 1, '先')]
    p = tmp_path / 'out.srt'
    export_project(project, p)
    text = p.read_text(encoding='utf-8')
    assert text.index('先') < text.index('後')
    assert text.startswith('1\n00:00:00,000')

def test_cer():
    assert cer('あいう', 'あいう') == 0
    assert cer('あいう', 'あえう') == pytest.approx(1/3)
    assert cer('あ', 'あいうえ') == 3
    assert normalize('Ａ Ｂ\n', 'nfkc-no-space') == 'AB'
    with pytest.raises(ValueError):
        cer('', 'x')

def test_sdk_responses_wire_contract():
    import httpx
    from openai import OpenAI
    requests = []
    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={
            'id': 'resp_test', 'object': 'response', 'created_at': 0, 'model': 'test',
            'status': 'completed', 'error': None, 'incomplete_details': None,
            'instructions': None, 'metadata': {}, 'output': [
                {'type': 'message', 'id': 'msg_test', 'role': 'assistant', 'status': 'completed',
                 'content': [{'type': 'output_text', 'text': '要約できました', 'annotations': []}]}],
            'parallel_tool_calls': False, 'tools': [], 'tool_choice': 'auto', 'temperature': 1, 'top_p': 1,
        })
    with OpenAI(api_key='unit-test-key', base_url='https://api.openai.com/v1',
                http_client=httpx.Client(transport=httpx.MockTransport(handler))) as client:
        result = generate('要約', '確認済み本文', Settings(ai_enabled=True, offline=False, ai_model='test'), client=client)
    assert len(requests) == 1
    assert str(requests[0].url) == 'https://api.openai.com/v1/responses'
    payload = json.loads(requests[0].content)
    assert payload['store'] is False and payload['input'] == '確認済み本文'
    assert result['text'] == '要約できました'


def test_atomic_flush_uses_writable_handle(tmp_path, monkeypatch):
    import os
    from local_transcriber import storage
    real_fsync = os.fsync
    checked = []
    def writable_fsync(fd):
        # Fails for a read-only descriptor on both Windows and Unix.
        os.write(fd, b'')
        checked.append(fd)
        real_fsync(fd)
    monkeypatch.setattr(storage.os, 'fsync', writable_fsync)
    target = tmp_path / 'settings.json'
    storage.write_json(target, {'language': 'ja'})
    assert checked and json.loads(target.read_text()) == {'language': 'ja'}


def test_sync_failure_preserves_prior_and_reports_stage(tmp_path, monkeypatch):
    import errno
    from local_transcriber import storage
    target = tmp_path / 'settings.json'
    target.write_text('prior')
    def fail(fd):
        raise OSError(errno.EBADF, 'sensitive text should never be displayed')
    monkeypatch.setattr(storage.os, 'fsync', fail)
    with pytest.raises(OSError) as result:
        storage.write_json(target, {'language': 'ja'})
    assert target.read_text() == 'prior'
    assert list(tmp_path.iterdir()) == [target]
    message = storage.storage_error_message(result.value)
    assert 'ディスクへの確定' in message and 'errno=9' in message
    assert 'sensitive text' not in message


def test_settings_permission_error_has_safe_details(monkeypatch):
    import errno
    from local_transcriber import storage
    def fail(*args, **kwargs):
        raise PermissionError(errno.EACCES, 'private text')
    monkeypatch.setattr(storage.tempfile, 'mkstemp', fail)
    with pytest.raises(PermissionError) as result:
        storage.save_settings(Settings())
    assert storage.settings_path().name == 'settings.json'
    message = storage.storage_error_message(result.value)
    assert '書き込みが拒否' in message and '保存先の準備' in message
    assert 'private text' not in message


def test_settings_error_dialog_contains_path_and_codes(qapp, monkeypatch):
    import errno
    from local_transcriber import gui
    from PySide6.QtWidgets import QDialog
    w = gui.MainWindow()
    monkeypatch.setattr(gui.SettingsDialog, 'exec', lambda self: QDialog.DialogCode.Accepted)
    def fail(settings):
        raise OSError(errno.EBADF, 'private text')
    monkeypatch.setattr(gui, 'save_settings', fail)
    messages = []
    monkeypatch.setattr(gui.QMessageBox, 'warning', lambda parent, title, text: messages.append(text))
    w.edit_settings()
    assert len(messages) == 1
    assert 'settings.json' in messages[0] and 'errno=9' in messages[0]
    assert 'private text' not in messages[0]
    w.close()


def test_performance_settings_and_project_backwards_compatibility(project):
    from local_transcriber.storage import load_settings, save_settings
    settings = Settings(recognition_mode='fast', cpu_threads=6)
    save_settings(settings)
    assert load_settings().recognition_mode == 'fast'
    assert load_settings().cpu_threads == 6
    project.apply_settings(settings)
    restored = Project.from_dict(project.to_dict())
    assert restored.beam_size == 1 and restored.cpu_threads == 6
    assert restored.recognition_mode == 'fast'
    old = project.to_dict()
    for field in ('recognition_mode', 'cpu_threads', 'best_of', 'temperature', 'processing_seconds'):
        old.pop(field)
    old['beam_size'] = 5
    old_project = Project.from_dict(old)
    assert old_project.recognition_mode == 'standard' and old_project.beam_size == 5
    assert old_project.text() == project.text()


@pytest.mark.parametrize('params', [{'cpu_threads': -1}, {'cpu_threads': 129}, {'cpu_threads': True}, {'recognition_mode': 'unknown'}])
def test_invalid_performance_settings_rejected(params):
    with pytest.raises(ValueError):
        Settings(**params).validate()
