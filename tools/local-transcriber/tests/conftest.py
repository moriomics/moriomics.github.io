import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import pytest

@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'appdata'))

@pytest.fixture(scope='session')
def qapp():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app
