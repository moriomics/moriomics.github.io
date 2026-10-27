import time
from pathlib import Path
import pytest
from local_transcriber.domain import Project, Segment
from local_transcriber.gui import MainWindow, SendDialog
from local_transcriber.controller import JobController
from tests.fakes import fake_worker

def until(app, predicate, timeout=15):
    deadline = time.monotonic() + timeout
    while not predicate():
        app.processEvents()
        time.sleep(.01)
        if time.monotonic() > deadline:
            raise AssertionError('Qt event processing timeout')
    app.processEvents()

def test_gui_edits_restore_and_send_preview(qapp):
    w = MainWindow()
    p = Project('missing.wav', segments=[Segment(0, 0, 1, '原文')], status='完了')
    p.ai_outputs = [{'text': '生成原文', 'input_text': '送信本文'}]
    w.projects.append(p)
    w.refresh_files()
    w.files.selectRow(0)
    w.show_project()
    assert p.segments[0].edited_text is None
    w.segments.item(0, 3).setText('修正')
    assert p.text() == '修正' and p.text(raw=True) == '原文'
    w.segments.item(0, 3).setText('')
    assert p.text() == ''
    w.segments.selectRow(0)
    w.restore_segments()
    assert p.segments[0].edited_text is None
    w.ai_result.setPlainText('生成を編集')
    assert p.ai_outputs[0]['text'] == '生成原文'
    assert p.ai_outputs[0]['edited_text'] == '生成を編集'
    d = SendDialog('要約', p.text(), 'm', w)
    d.text.setPlainText('送信範囲だけ')
    assert '6文字' in d.count.text()
    d.text.setPlainText('')
    assert not d.send.isEnabled()
    w.flush_dirty()
    w.close()

def test_sequential_queue_failure_does_not_stop_next(qapp, monkeypatch):
    import local_transcriber.controller as module
    monkeypatch.setattr(module, 'worker_main', fake_worker)
    w = MainWindow()
    w.add_files(['bad.wav', 'good.wav'])
    until(qapp, lambda: not w.controller.busy and not w.pending and w.active is None)
    assert [p.status for p in w.projects] == ['待機中', '待機中']
    assert 'ファイル検査完了' in w.status.text()
    assert '開始ボタン' in w.status.text()
    assert w.progress.value() == 100
    assert w.progress.format() == 'ファイル検査 %p%'
    assert w.start_b.isEnabled()
    w.start_queue()
    until(qapp, lambda: not w.controller.busy and not w.pending and w.active is None)
    assert [p.status for p in w.projects] == ['失敗', '完了']
    assert w.projects[1].text() == '認識した文章'
    from local_transcriber.storage import app_home, load_project
    saved = load_project(app_home() / 'projects' / (w.projects[1].project_id + '.json'))
    assert saved.status == '完了'
    assert len(w.projects[1].segments) == 1
    w.close()

@pytest.mark.parametrize('kind', ['slow', 'stuck'])
def test_cancel_cleanup_and_restart(qapp, monkeypatch, kind):
    import local_transcriber.controller as module
    monkeypatch.setattr(module, 'worker_main', fake_worker)
    c = JobController()
    results, events = [], []
    c.event.connect(lambda *x: events.append(x))
    c.finished.connect(lambda *x: results.append(x))
    c.start(kind, {})
    temp = Path(c.temp)
    until(qapp, lambda: bool(events))
    c.cancel()
    until(qapp, lambda: not c.busy)
    assert results[-1][0] == 'cancelled' and not temp.exists()
    c.start('probe', {})
    until(qapp, lambda: not c.busy)
    assert results[-1][0] == 'result'

def test_ai_dispatch_preserves_transcription_status(qapp, monkeypatch):
    # No external call: inspect dispatch while the process launcher is replaced.
    w = MainWindow()
    p = Project('missing.wav', status='完了', segments=[Segment(0, 0, 1, '記録')])
    w.projects = [p]
    w.refresh_files()
    w.files.selectRow(0)
    monkeypatch.setattr(w.controller, 'start', lambda *args: None)
    w.pending.append(('ai', 0, {}))
    w.dispatch()
    assert p.status == '完了'
    w.worker_finished('result', {'kind': '要約', 'text': '生成', 'input_text': '記録'})
    assert p.status == '完了' and p.segments[0].raw_text == '記録'
    w.pending.clear()
    w.active = None
    w.close()


def test_copy_selected_rows_keeps_full_copy(qapp):
    from PySide6.QtCore import QItemSelectionModel
    from PySide6.QtWidgets import QApplication
    w = MainWindow()
    p = Project('copy.wav', status='完了', segments=[
        Segment(0, 0, 1, '原文1', '編集1'), Segment(1, 1, 2, '原文2'),
        Segment(2, 2, 3, '原文3', '編集3')])
    w.projects = [p]
    w.refresh_files()
    w.files.selectRow(0)
    w.show_project()
    selection = w.segments.selectionModel()
    flag = QItemSelectionModel.SelectionFlag.Select
    selection.select(w.segments.model().index(2, 3), flag)
    selection.select(w.segments.model().index(0, 3), flag)
    w.copy_selected_b.click()
    assert QApplication.clipboard().text() == '編集1\n編集3'
    w.copy_text()
    assert QApplication.clipboard().text() == '編集1\n原文2\n編集3'
    w.segments.clearSelection()
    w.copy_selected_rows()
    assert QApplication.clipboard().text() == '編集1\n原文2\n編集3'
    assert '選択してください' in w.status.text()
    w.close()


def test_recognition_table_refresh_is_batched_without_duplicate_rows(qapp):
    w = MainWindow()
    p = Project('stream.wav', duration_seconds=4)
    w.projects = [p]
    w.refresh_files()
    w.files.selectRow(0)
    w.show_project()
    w.active = ('transcribe', 0, {})
    for i in range(3):
        w.worker_event('segment', {'id': i, 'start': float(i), 'end': float(i+1), 'raw_text': str(i)})
    assert len(p.segments) == 3 and w.segments.rowCount() == 0
    assert w.recognition_display_timer.isActive()
    w.recognition_display_timer.stop()
    w.flush_recognition_display()
    assert w.segments.rowCount() == 3
    w.flush_recognition_display()
    assert w.segments.rowCount() == 3
    w.worker_event('segment', {'id': 3, 'start': 3., 'end': 4., 'raw_text': '3'})
    w.recognition_display_timer.stop()
    w.flush_recognition_display()
    assert w.segments.rowCount() == 4
    w.active = None
    w.close()


def test_mouse_selection_highlights_only_edited_cells(qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    w = MainWindow()
    w.projects = [Project('selection.wav', status='完了', segments=[
        Segment(i, float(i), float(i+1), f'原文{i}', f'編集{i}') for i in range(3)])]
    w.refresh_files()
    w.files.selectRow(0)
    w.show_project()
    w.show()
    qapp.processEvents()
    def click(row, col, modifiers=Qt.KeyboardModifier.NoModifier):
        index = w.segments.model().index(row, col)
        point = w.segments.visualRect(index).center()
        QTest.mouseClick(w.segments.viewport(), Qt.MouseButton.LeftButton, modifiers, point)
        qapp.processEvents()
    click(0, 3)
    assert [(i.row(), i.column()) for i in w.segments.selectedIndexes()] == [(0, 3)]
    click(2, 3, Qt.KeyboardModifier.ControlModifier)
    assert {(i.row(), i.column()) for i in w.segments.selectedIndexes()} == {(0, 3), (2, 3)}
    click(1, 3, Qt.KeyboardModifier.ShiftModifier)
    assert w.segments.selectedIndexes()
    assert {i.column() for i in w.segments.selectedIndexes()} == {3}
    w.segments.clearSelection()
    click(0, 2)
    assert not w.segments.selectedIndexes()
    click(0, 0)
    assert not w.segments.selectedIndexes()
    w.close()
