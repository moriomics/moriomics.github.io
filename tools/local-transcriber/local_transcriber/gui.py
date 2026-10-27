from __future__ import annotations
from collections import deque
from dataclasses import asdict
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QSplitter, QComboBox,
    QProgressBar, QFileDialog, QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QLineEdit, QCheckBox, QPlainTextEdit, QTabWidget, QInputDialog, QSpinBox,
)
from .ai import BASE, MAX_CHARS, PROMPTS, get_key, set_key, delete_key
from .controller import JobController
from .domain import Project, Segment, Settings, MODELS, EXTENSIONS, now
from .models import model_ready
from .storage import app_home, load_settings, save_settings, save_project, load_project, export_project, timestamp, settings_path, storage_error_message


def button(text, callback, layout):
    b = QPushButton(text)
    b.clicked.connect(callback)
    layout.addWidget(b)
    return b


def readonly(text=''):
    widget = QPlainTextEdit(text)
    widget.setReadOnly(True)
    return widget


class SettingsDialog(QDialog):
    def __init__(self, settings, parent):
        super().__init__(parent)
        self.setWindowTitle('設定')
        self.settings = Settings(**asdict(settings))
        form = QFormLayout(self)
        self.folder = QLineEdit(settings.output_folder)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder)
        button('選択', self.browse, folder_row)
        form.addRow('出力フォルダ', folder_row)
        self.threads = QSpinBox()
        self.threads.setRange(0, 128)
        self.threads.setSpecialValueText('自動')
        self.threads.setValue(settings.cpu_threads)
        self.threads.setToolTip('CPU認識用です。増やしすぎると遅くなる場合があります。')
        form.addRow('CPUスレッド数', self.threads)
        self.stamps = QCheckBox('TXT・DOCXに時刻を付ける')
        self.stamps.setChecked(settings.timestamps)
        form.addRow(self.stamps)
        self.offline = QCheckBox('オフラインモード（モデル取得・AI通信を禁止）')
        self.offline.setChecked(settings.offline)
        form.addRow(self.offline)
        self.enabled = QCheckBox('AI通信を有効にする（送信ごとに確認）')
        self.enabled.setChecked(settings.ai_enabled)
        form.addRow(self.enabled)
        self.model = QLineEdit(settings.ai_model)
        self.model.setPlaceholderText('利用可能なResponses API対応モデルIDを入力')
        form.addRow('AIモデル', self.model)
        keyrow = QHBoxLayout()
        button('APIキー登録', self.register_key, keyrow)
        button('APIキー削除', self.remove_key, keyrow)
        form.addRow('Windows資格情報', keyrow)
        note = QLabel('キーは設定JSONに保存しません。\nAPIの従量課金はChatGPTの契約と別です。')
        form.addRow(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def browse(self):
        folder = QFileDialog.getExistingDirectory(self, '出力フォルダ', self.folder.text())
        if folder:
            self.folder.setText(folder)

    def register_key(self):
        key, ok = QInputDialog.getText(self, 'APIキー登録', 'OpenAI APIキー', QLineEdit.EchoMode.Password)
        if ok and key.strip():
            try:
                set_key(key)
                QMessageBox.information(self, '登録', '資格情報マネージャーに登録しました。')
            except Exception:
                QMessageBox.warning(self, '登録失敗', '資格情報マネージャーに登録できませんでした。')

    def remove_key(self):
        try:
            delete_key()
            QMessageBox.information(self, '削除', 'APIキーを削除しました。')
        except Exception:
            QMessageBox.warning(self, '削除失敗', '資格情報マネージャーを操作できませんでした。')

    def accept(self):
        self.settings.output_folder = self.folder.text().strip()
        self.settings.cpu_threads = self.threads.value()
        self.settings.timestamps = self.stamps.isChecked()
        self.settings.offline = self.offline.isChecked()
        self.settings.ai_enabled = self.enabled.isChecked()
        self.settings.ai_model = self.model.text().strip()
        super().accept()


class SendDialog(QDialog):
    def __init__(self, kind, text, model, parent):
        super().__init__(parent)
        self.setWindowTitle('API送信前の確認')
        self.resize(820, 660)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'処理: {kind} / モデル: {model}\n送信先: https://api.openai.com/v1/responses'))
        layout.addWidget(QLabel('下の本文と処理指示だけを送信します。本文は範囲を絞って編集できます。'))
        self.text = QPlainTextEdit(text)
        layout.addWidget(self.text, 3)
        self.count = QLabel()
        layout.addWidget(self.count)
        layout.addWidget(QLabel('一緒に送信する処理指示'))
        layout.addWidget(readonly(BASE + PROMPTS[kind]), 1)
        layout.addWidget(QLabel('送信後の取り消しは保証されません。生成文は原文と比較して確認してください。'))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.send = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.send.setText('この内容を送信')
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.text.textChanged.connect(self.update_count)
        self.update_count()

    def update_count(self):
        text = self.text.toPlainText()
        self.count.setText(f'送信本文: {len(text):,}文字 / 上限 {MAX_CHARS:,}文字（料金はトークン数で決まります）')
        self.send.setEnabled(bool(text.strip()) and len(text) <= MAX_CHARS)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Local Transcriber 0.2.1 — ローカル文字起こし')
        self.resize(1320, 880)
        self.setAcceptDrops(True)
        self.settings = load_settings()
        self.projects = []
        self.pending = deque()
        self.active = None
        self.dirty = set()
        self.rendering = False
        self.closing = False
        self.recognition_display_timer = QTimer(self)
        self.recognition_display_timer.setSingleShot(True)
        self.recognition_display_timer.setInterval(200)
        self.recognition_display_timer.timeout.connect(self.flush_recognition_display)
        self.controller = JobController(self)
        self.controller.event.connect(self.worker_event)
        self.controller.finished.connect(self.worker_finished)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        top = QHBoxLayout()
        self.add_b = button('ファイル追加', self.add_dialog, top)
        self.remove_b = button('削除', self.remove_files, top)
        self.open_b = button('プロジェクトを開く', self.open_projects, top)
        button('プロジェクト保存', self.save_current, top)
        self.settings_b = button('設定', self.edit_settings, top)
        button('保存先を開く', self.open_autosaves, top)
        layout.addLayout(top)
        self.privacy = QLabel()
        layout.addWidget(self.privacy)
        split = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(split, 1)
        files_panel = QWidget()
        files_layout = QVBoxLayout(files_panel)
        self.files = QTableWidget(0, 5)
        self.files.setHorizontalHeaderLabels(['ファイル名', '再生時間', 'サイズ', '状態', '通知'])
        self.files.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.files.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.files.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.files.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.files.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.files.itemSelectionChanged.connect(self.show_project)
        files_layout.addWidget(self.files)
        controls = QHBoxLayout()
        controls.addWidget(QLabel('言語'))
        self.language = QComboBox()
        for label, value in [('日本語', 'ja'), ('自動判定', None), ('英語', 'en')]:
            self.language.addItem(label, value)
        self.language.setCurrentIndex(max(0, self.language.findData(self.settings.language)))
        controls.addWidget(self.language)
        controls.addWidget(QLabel('モデル'))
        self.model = QComboBox()
        self.model.addItems(MODELS)
        self.model.setCurrentText(self.settings.model_name)
        controls.addWidget(self.model)
        self.device = QComboBox()
        self.device.addItem('CPU / int8', 'cpu')
        self.device.addItem('GPU (NVIDIA CUDA) / float16', 'cuda')
        self.device.setCurrentIndex(max(0, self.device.findData(self.settings.device)))
        controls.addWidget(self.device)
        self.download_b = button('モデル取得', self.download, controls)
        self.start_b = button('文字起こし開始', self.start_queue, controls)
        self.cancel_b = button('キャンセル', self.cancel, controls)
        files_layout.addLayout(controls)
        performance = QHBoxLayout()
        performance.addWidget(QLabel('認識モード'))
        self.speed = QComboBox()
        self.speed.addItem('高速（速度優先）', 'fast')
        self.speed.addItem('標準（従来設定）', 'standard')
        self.speed.setCurrentIndex(max(0, self.speed.findData(self.settings.recognition_mode)))
        performance.addWidget(self.speed)
        performance.addWidget(QLabel('高速は探索・再試行を減らします。認識精度が下がる場合があります。'))
        performance.addStretch()
        files_layout.addLayout(performance)
        self.model_status = QLabel()
        files_layout.addWidget(self.model_status)
        self.model.currentTextChanged.connect(self.refresh_settings_labels)
        split.addWidget(files_panel)
        results = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel('文字起こし結果（編集テキストを直接変更できます）'))
        self.segments = QTableWidget(0, 4)
        self.segments.setHorizontalHeaderLabels(['開始', '終了', '認識原文', '編集テキスト'])
        self.segments.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.segments.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.segments.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.segments.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.segments.itemChanged.connect(self.segment_changed)
        left_layout.addWidget(self.segments, 1)
        result_actions = QHBoxLayout()
        button('選択行を原文に戻す', self.restore_segments, result_actions)
        button('全文コピー', self.copy_text, result_actions)
        self.copy_selected_b = button('選択行コピー', self.copy_selected_rows, result_actions)
        self.copy_selected_b.setToolTip('編集テキストのセルを選択してコピーします。CtrlやShiftで複数セルを選択できます。')
        button('書き出し', self.export_current, result_actions)
        left_layout.addLayout(result_actions)
        results.addWidget(left)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel('AIテキスト処理（原文とは別に保持）'))
        ai_actions = QHBoxLayout()
        self.ai_buttons = [button(kind, lambda checked=False, k=kind: self.run_ai(k), ai_actions) for kind in PROMPTS]
        right_layout.addLayout(ai_actions)
        self.ai_selector = QComboBox()
        self.ai_selector.currentIndexChanged.connect(self.show_ai)
        right_layout.addWidget(self.ai_selector)
        tabs = QTabWidget()
        self.ai_result = QPlainTextEdit()
        self.ai_result.textChanged.connect(self.ai_changed)
        self.ai_input = readonly()
        self.raw_full = readonly()
        tabs.addTab(self.ai_result, '生成結果・編集')
        tabs.addTab(self.ai_input, '送信した本文')
        tabs.addTab(self.raw_full, '認識原文')
        right_layout.addWidget(tabs)
        ai_save = QHBoxLayout()
        button('AI結果コピー', lambda: QApplication.clipboard().setText(self.ai_result.toPlainText()), ai_save)
        button('AI結果をTXT保存', self.export_ai, ai_save)
        right_layout.addLayout(ai_save)
        results.addWidget(right)
        results.setSizes([820, 500])
        split.addWidget(results)
        split.setSizes([260, 530])
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.status = QLabel('ファイルを追加してください。音声・動画は外部へ送信しません。')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(1500)
        self.autosave_timer.timeout.connect(self.flush_dirty)
        self.autosave_timer.start()
        self.refresh_settings_labels()
        self.set_busy(False)

    def selected_index(self):
        row = self.files.currentRow()
        return row if 0 <= row < len(self.projects) else None

    def current_project(self):
        i = self.selected_index()
        return None if i is None else self.projects[i]

    def snapshot_settings(self):
        self.settings.model_name = self.model.currentText()
        self.settings.device = self.device.currentData()
        self.settings.language = self.language.currentData()
        self.settings.recognition_mode = self.speed.currentData()
        return asdict(self.settings)

    def refresh_settings_labels(self):
        states = ' / '.join(f'{m}: {"導入済み" if model_ready(m) else "未導入"}' for m in MODELS)
        self.model_status.setText(states)
        self.privacy.setText('オフラインモード: ' + ('有効' if self.settings.offline else '無効') +
            '  /  AI通信: ' + ('有効（送信時確認）' if self.settings.ai_enabled else '無効'))

    def set_busy(self, busy):
        for w in (self.add_b, self.remove_b, self.open_b, self.settings_b, self.model, self.device, self.language, self.speed):
            w.setEnabled(not busy)
        self.start_b.setEnabled(not busy and bool(self.projects))
        self.download_b.setEnabled(not busy and not self.settings.offline)
        self.cancel_b.setEnabled(busy)
        for w in self.ai_buttons:
            w.setEnabled(not busy and self.settings.ai_enabled and not self.settings.offline)
        self.segments.setEnabled(not (busy and self.active and self.active[0] == 'transcribe' and self.active[1] == self.selected_index()))

    def add_dialog(self):
        paths, _ = QFileDialog.getOpenFileNames(self, '音声・動画ファイル', '',
            'メディア (*.mp3 *.wav *.m4a *.flac *.mp4 *.mov *.mkv *.webm)')
        self.add_files(paths)

    def add_files(self, paths):
        if self.controller.busy or self.pending:
            return
        known = {Path(p.source_path).resolve() for p in self.projects}
        for path in paths:
            resolved = Path(path).resolve()
            if resolved in known:
                continue
            if resolved.suffix.lower() not in EXTENSIONS:
                self.status.setText('対応形式: MP3 / WAV / M4A / FLAC / MP4 / MOV / MKV / WebM')
                continue
            known.add(resolved)
            p = Project(str(resolved))
            self.projects.append(p)
            index = len(self.projects) - 1
            self.pending.append(('probe', index, {'path': str(resolved)}))
        self.refresh_files()
        if self.projects and self.files.currentRow() < 0:
            self.files.selectRow(0)
        self.dispatch()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.controller.busy and not self.pending:
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_files([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])

    def refresh_files(self):
        self.files.setRowCount(len(self.projects))
        for i, p in enumerate(self.projects):
            values = [p.filename, timestamp(p.duration_seconds), f'{p.size_bytes / 1048576:.1f} MiB', p.status, p.error]
            for c, value in enumerate(values):
                item = QTableWidgetItem(value)
                if c == 0:
                    item.setToolTip(p.source_path)
                self.files.setItem(i, c, item)

    def remove_files(self):
        if self.controller.busy or self.pending:
            return
        for row in sorted({x.row() for x in self.files.selectionModel().selectedRows()}, reverse=True):
            p = self.projects[row]
            if not self.checkpoint(p):
                continue
            self.projects.pop(row)
            self.dirty.discard(p.project_id)
        self.refresh_files()
        self.show_project()
        self.set_busy(False)

    def edit_settings(self):
        self.snapshot_settings()
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.settings
            try:
                save_settings(self.settings)
            except Exception as exc:
                QMessageBox.warning(self, '設定', '設定ファイルを保存できませんでした。\n\n'
                    + f'保存先: {settings_path()}\n' + storage_error_message(exc)
                    + '\n\nこの起動中の設定には反映されていますが、再起動後の保持はできません。')
        self.refresh_settings_labels()
        self.set_busy(False)

    def download(self):
        if self.settings.offline or self.controller.busy:
            return
        model = self.model.currentText()
        if QMessageBox.question(self, 'モデル取得',
            f'{model}モデルをHugging Faceから取得します。大きなモデルは数GBとなる場合があります。続行しますか？') != QMessageBox.StandardButton.Yes:
            return
        self.pending.append(('download', None, {'model_name': model}))
        self.dispatch()

    def start_queue(self):
        if self.controller.busy:
            return
        settings = self.snapshot_settings()
        try:
            save_settings(self.settings)
        except Exception as exc:
            self.status.setText('設定ファイルの保存に失敗しました。' + storage_error_message(exc))
        for i, p in enumerate(self.projects):
            if p.status in ('待機中', '失敗', 'キャンセル'):
                if p.segments and QMessageBox.question(self, '再実行',
                    f'{p.filename}の認識・編集結果を再生成します。既存結果は別プロジェクトとして自動保存します。続行しますか？') != QMessageBox.StandardButton.Yes:
                    continue
                if p.segments or p.ai_outputs:
                    if not self.checkpoint(p):
                        continue
                    # Retain previous checkpoint and create a new identity for rerun.
                    p = Project(p.source_path, duration_seconds=p.duration_seconds, size_bytes=p.size_bytes)
                    self.projects[i] = p
                self.pending.append(('transcribe', i, {'project': p.to_dict(), 'settings': settings}))
        self.dispatch()

    def dispatch(self):
        if self.controller.busy:
            return
        if not self.pending:
            self.active = None
            self.set_busy(False)
            if self.closing:
                self.close()
            return
        self.active = self.pending.popleft()
        kind, index, payload = self.active
        self.progress.setFormat({'probe': 'ファイル検査 %p%', 'transcribe': '文字起こし（概算） %p%',
                                 'download': 'モデル取得 %p%', 'ai': 'AI処理 %p%'}[kind])
        self.progress.setRange(0, 100 if kind == 'transcribe' else 0)
        self.progress.setValue(0)
        if index is not None and kind in ('probe', 'transcribe'):
            self.projects[index].status = '前処理中'
            self.projects[index].error = ''
            if kind == 'transcribe':
                p = self.projects[index]
                p.apply_settings(Settings(**payload['settings']))
                self.files.selectRow(index)
        self.refresh_files()
        self.status.setText({'probe': 'ファイル検査中', 'download': 'モデル取得中（容量により時間がかかります）',
                             'ai': 'AI処理中', 'transcribe': '前処理中'}[kind])
        self.set_busy(True)
        try:
            self.controller.start(kind, payload)
        except Exception:
            self.worker_finished('error', {'message': 'ワーカーを起動できませんでした。', 'code': 'SpawnError'})

    def cancel(self):
        self.pending.clear()
        self.controller.cancel()
        self.status.setText('キャンセル処理中… キューの後続処理も停止します。')
        self.cancel_b.setEnabled(False)

    def worker_event(self, event, data):
        if not self.active:
            return
        _, index, _ = self.active
        if index is None:
            return
        p = self.projects[index]
        if event == 'stage':
            p.status = data
            self.status.setText(data)
            self.progress.setValue(5 if data == '前処理中' else 15)
            self.refresh_files()
        elif event == 'metadata':
            for k, v in data.items():
                setattr(p, k, v)
            self.refresh_files()
        elif event == 'segment':
            s = Segment(**data)
            p.segments.append(s)
            if not self.recognition_display_timer.isActive():
                self.recognition_display_timer.start()

    def flush_recognition_display(self):
        if not self.active or self.active[0] != 'transcribe':
            return
        index = self.active[1]
        p = self.projects[index]
        end = p.segments[-1].end if p.segments else 0
        value = 15 + min(79, int(79 * end / p.duration_seconds)) if p.duration_seconds else 15
        self.progress.setValue(value)
        self.status.setText(f'認識中: {len(p.segments)}セグメント / 進捗は概算')
        if index == self.selected_index():
            previous_rendering = self.rendering
            self.rendering = True
            self.segments.setUpdatesEnabled(False)
            try:
                for segment in p.segments[self.segments.rowCount():]:
                    self.append_segment(segment)
            finally:
                self.rendering = previous_rendering
                self.segments.setUpdatesEnabled(True)

    def worker_finished(self, outcome, data):
        self.recognition_display_timer.stop()
        if not self.active:
            return
        kind, index, payload = self.active
        p = self.projects[index] if index is not None else None
        if outcome == 'result':
            if kind == 'probe':
                p.duration_seconds, p.size_bytes = data['duration_seconds'], data['size_bytes']
                p.status = '待機中'
                self.status.setText(f'ファイル検査完了: {p.filename} ／ 開始ボタンで文字起こしを開始できます。')
            elif kind == 'transcribe':
                p = Project.from_dict(data)
                self.projects[index] = p
                self.status.setText('保存中')
                p.status = '保存中'
                self.refresh_files()
                p.status = '完了'
                if self.checkpoint(p):
                    self.status.setText(f'完了: {p.filename} / {len(p.segments)}セグメント'
                        + (f' / 処理時間 {p.processing_seconds:.1f}秒' if p.processing_seconds is not None else ''))
            elif kind == 'ai':
                p.ai_outputs.append(data)
                if self.checkpoint(p):
                    self.status.setText('AI生成が完了しました。原文と比較して確認してください。')
            elif kind == 'download':
                self.status.setText('モデル取得が完了しました。オフラインで文字起こしできます。')
        elif outcome == 'cancelled':
            if p and kind in ('probe', 'transcribe'):
                p.status = 'キャンセル'
                self.checkpoint(p)
            self.status.setText('キャンセルしました。取得済みセグメントを保存しました。')
        else:
            message = data['message']
            if p and kind in ('probe', 'transcribe'):
                p.status, p.error = '失敗', message
                self.checkpoint(p)
            logging.getLogger('LocalTranscriber').error('job=%s code=%s', kind, data.get('code', 'Unknown'))
            self.status.setText(message)
            if kind == 'transcribe' and payload['settings']['device'] == 'cuda':
                QMessageBox.warning(self, 'GPU処理に失敗', message + '\n装置をCPUへ変更して再実行できます。')
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if outcome == 'result' else 0)
        self.refresh_files()
        self.show_project()
        self.refresh_settings_labels()
        self.active = None
        QTimer.singleShot(0, self.dispatch)

    def checkpoint(self, p):
        try:
            save_project(p, app_home() / 'projects' / (p.project_id + '.json'))
            self.dirty.discard(p.project_id)
            return True
        except Exception as exc:
            self.dirty.add(p.project_id)
            self.status.setText('自動保存に失敗しました。' + storage_error_message(exc))
            return False

    def flush_dirty(self):
        for p in self.projects:
            if p.project_id in self.dirty:
                self.checkpoint(p)

    def append_segment(self, s):
        row = self.segments.rowCount()
        self.segments.insertRow(row)
        for col, text in enumerate((timestamp(s.start), timestamp(s.end), s.raw_text, s.text)):
            item = QTableWidgetItem(text)
            if col != 3:
                item.setFlags(item.flags() & ~(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable))
            self.segments.setItem(row, col, item)

    def show_project(self):
        self.rendering = True
        p = self.current_project()
        self.segments.setRowCount(0)
        self.ai_selector.clear()
        if p:
            for s in p.segments:
                self.append_segment(s)
            for a in p.ai_outputs:
                self.ai_selector.addItem(f'{a.get("created_at", "")} {a.get("kind", "")}')
            self.raw_full.setPlainText(p.text(raw=True))
            self.ai_selector.setCurrentIndex(len(p.ai_outputs) - 1)
        else:
            self.raw_full.clear()
        self.rendering = False
        self.show_ai()
        self.set_busy(self.controller.busy)

    def segment_changed(self, item):
        if self.rendering or item.column() != 3:
            return
        p = self.current_project()
        if p and item.row() < len(p.segments):
            p.segments[item.row()].edited_text = item.text()
            p.updated_at = now()
            self.dirty.add(p.project_id)

    def restore_segments(self):
        p = self.current_project()
        if not p or not self.segments.isEnabled():
            return
        for row in {x.row() for x in self.segments.selectedIndexes()}:
            p.segments[row].edited_text = None
            self.dirty.add(p.project_id)
        self.show_project()

    def copy_text(self):
        p = self.current_project()
        if p:
            QApplication.clipboard().setText(p.text())

    def copy_selected_rows(self):
        p = self.current_project()
        if not p:
            return
        rows = sorted({item.row() for item in self.segments.selectedIndexes() if item.column() == 3})
        if not rows:
            self.status.setText('コピーする編集テキストのセルを選択してください。CtrlやShiftで複数セルを選択できます。')
            return
        QApplication.clipboard().setText('\n'.join(p.segments[row].text for row in rows if row < len(p.segments)))
        self.status.setText(f'選択した{len(rows)}行をコピーしました。')

    def save_current(self):
        p = self.current_project()
        if not p:
            return
        path, _ = QFileDialog.getSaveFileName(self, 'プロジェクト保存',
            str(app_home() / 'projects' / (Path(p.filename).stem + '_project.json')), 'JSON (*.json)')
        if path:
            try:
                save_project(p, path)
                self.checkpoint(p)
                self.status.setText('プロジェクトを保存しました。')
            except Exception:
                QMessageBox.warning(self, '保存失敗', '保存できませんでした。元ファイル以外の保存先・空き容量を確認してください。')

    def open_projects(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'プロジェクトを開く', str(app_home() / 'projects'), 'JSON (*.json)')
        missing = []
        for path in paths:
            try:
                p = load_project(path)
                if any(x.project_id == p.project_id for x in self.projects):
                    continue
                if not Path(p.source_path).is_file():
                    p.error = '元ファイルが見つかりません。結果の閲覧・編集・保存は可能です。'
                    missing.append(p.filename)
                self.projects.append(p)
            except Exception:
                QMessageBox.warning(self, '読込失敗', 'プロジェクト形式が不正、未対応、またはファイルを読み取れません。')
        self.refresh_files()
        if self.projects:
            self.files.selectRow(len(self.projects) - 1)
        self.set_busy(False)
        if missing:
            QMessageBox.information(self, '元ファイルの参照', '元ファイルが見つかりません:\n' + '\n'.join(missing))

    def export_current(self):
        p = self.current_project()
        if not p:
            return
        path, selected = QFileDialog.getSaveFileName(self, '文字起こし書き出し',
            str(Path(self.settings.output_folder or app_home()) / (Path(p.filename).stem + '_transcript.txt')),
            'TXT (*.txt);;SRT (*.srt);;JSON (*.json);;Word (*.docx)')
        if path:
            expected = {'TXT (*.txt)': '.txt', 'SRT (*.srt)': '.srt', 'JSON (*.json)': '.json', 'Word (*.docx)': '.docx'}[selected]
            if Path(path).suffix.lower() != expected:
                QMessageBox.warning(self, '拡張子', '選択した形式と同じ拡張子を付けて保存してください。')
                return
            try:
                export_project(p, path, self.settings.timestamps)
                self.status.setText('書き出しました。')
            except Exception:
                QMessageBox.warning(self, '書き出し失敗', '保存できませんでした。保存先・空き容量を確認してください。')

    def run_ai(self, kind):
        p = self.current_project()
        if not p or self.controller.busy or not self.settings.ai_enabled or self.settings.offline:
            return
        if not p.text().strip():
            QMessageBox.information(self, 'AI処理', '先に文字起こしを実行してください。')
            return
        try:
            if not get_key():
                raise ValueError()
        except Exception:
            QMessageBox.warning(self, 'APIキー', '設定からAPIキーを登録してください。ローカル機能はそのまま利用できます。')
            return
        if not self.settings.ai_model.strip():
            QMessageBox.warning(self, 'AIモデル', '設定からResponses API対応のモデルIDを入力してください。')
            return
        dialog = SendDialog(kind, p.text(), self.settings.ai_model, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.pending.append(('ai', self.selected_index(), {'kind': kind, 'text': dialog.text.toPlainText(),
                                                          'settings': self.snapshot_settings()}))
        self.dispatch()

    def show_ai(self):
        p = self.current_project()
        index = self.ai_selector.currentIndex()
        previous_rendering = self.rendering
        self.rendering = True
        if p and 0 <= index < len(p.ai_outputs):
            a = p.ai_outputs[index]
            self.ai_result.setPlainText(a.get('edited_text', a['text']))
            self.ai_input.setPlainText(a.get('input_text', ''))
            self.ai_result.setReadOnly(False)
        else:
            self.ai_result.clear()
            self.ai_input.clear()
            self.ai_result.setReadOnly(True)
        self.rendering = previous_rendering

    def ai_changed(self):
        if self.rendering:
            return
        p = self.current_project()
        index = self.ai_selector.currentIndex()
        if p and 0 <= index < len(p.ai_outputs):
            p.ai_outputs[index]['edited_text'] = self.ai_result.toPlainText()
            self.dirty.add(p.project_id)

    def export_ai(self):
        p = self.current_project()
        if not p or self.ai_selector.currentIndex() < 0:
            return
        path, _ = QFileDialog.getSaveFileName(self, 'AI結果保存',
            str(Path(self.settings.output_folder or app_home()) / (Path(p.filename).stem + '_ai.txt')), 'TXT (*.txt)')
        if path:
            try:
                from .storage import atomic_target, protected_target
                protected_target(p, path)
                with atomic_target(path) as tmp:
                    tmp.write_text(self.ai_result.toPlainText(), encoding='utf-8')
            except Exception:
                QMessageBox.warning(self, '保存失敗', 'AI結果を保存できませんでした。')

    def open_autosaves(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        folder = app_home() / 'projects'
        folder.mkdir(exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def closeEvent(self, event):
        if self.controller.busy:
            if not self.closing and QMessageBox.question(self, '終了', '処理をキャンセルして終了しますか？') != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.closing = True
            self.cancel()
            event.ignore()
            return
        failed = [p for p in self.projects if p.project_id in self.dirty and not self.checkpoint(p)]
        if failed and QMessageBox.question(self, '未保存', '保存できない編集があります。保存せず終了しますか？') != QMessageBox.StandardButton.Yes:
            self.closing = False
            event.ignore()
            return
        try:
            self.snapshot_settings()
            save_settings(self.settings)
        except Exception:
            pass
        event.accept()


def launch():
    app = QApplication(sys.argv)
    app.setApplicationName('LocalTranscriber')
    app.setStyle('Fusion')
    if sys.platform == 'win32':
        from PySide6.QtGui import QFont
        app.setFont(QFont('Meiryo UI', 10))
    app.setStyleSheet('QTableWidget { font-size: 13px; } QPlainTextEdit { font-size: 14px; } QPushButton { padding: 6px; }')
    log_dir = app_home() / 'logs'
    log_dir.mkdir(exist_ok=True)
    handler = RotatingFileHandler(log_dir / 'app.log', maxBytes=1024 * 1024, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger = logging.getLogger('LocalTranscriber')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    window = MainWindow()
    window.show()
    return app.exec()
