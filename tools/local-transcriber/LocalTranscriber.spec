# Build only on the target OS. Use onedir for native ML/Qt runtime compatibility.
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

root = Path(SPECPATH)
datas, binaries, hiddenimports = [], [], []
for module in ('faster_whisper', 'ctranslate2', 'onnxruntime', 'av', 'tokenizers', 'huggingface_hub'):
    d, b, h = collect_all(module)
    datas += d
    binaries += b
    hiddenimports += h
for dist in ('faster-whisper', 'ctranslate2', 'huggingface-hub', 'openai', 'keyring', 'python-docx'):
    datas += copy_metadata(dist)
hiddenimports += collect_submodules('keyring.backends')
for exe in ('ffmpeg.exe', 'ffprobe.exe'):
    binaries.append((str(root / 'vendor' / 'ffmpeg' / exe), 'vendor/ffmpeg'))
# Include distributor-supplied third-party notices beside bundled binaries.
for notice in (root / 'vendor' / 'ffmpeg').glob('*.txt'):
    datas.append((str(notice), 'vendor/ffmpeg'))
a = Analysis(['run.py'], pathex=[str(root)], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, excludes=['tkinter', 'PyQt5', 'PyQt6'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='LocalTranscriber',
          debug=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='LocalTranscriber')
