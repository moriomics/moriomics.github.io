# Validation record

Publication date: 2026-10-27. Application version: 0.2.1.

## Automated checks performed

The curated public source was installed and tested in a fresh Linux x86_64 environment using standard CPython 3.14.8 and the pinned dependency files.

Result: **41 passed in 8.05s**, with no skipped tests.

The suite covers:

- Synthetic audio in WAV, MP3, M4A, FLAC, MP4, MOV, MKV, and WebM; ffprobe inspection and FFmpeg normalization.
- Invalid media and video without an audio stream.
- Raw versus edited transcript preservation, intentionally empty edits, and restoring the raw text.
- TXT, SRT, JSON, and DOCX exports, timestamp ordering, and project restoration when the original media is absent.
- Atomic replacement, writable flushing handles, preservation of prior files after simulated failure, and safe save-error diagnostics.
- Explicit model installation markers and missing-model behavior without an automatic download.
- Recognition-engine parameters for fast and standard modes, CPU-thread settings, and backwards-compatible project loading. Recognition itself is replaced with a test double in these checks.
- API request serialization with mocks, exact confirmed input, disabled/offline guards, and rejecting incomplete output. No live API request is made.
- Separate spawned processes, sequential queue behavior after one failure, cooperative and forced cancellation, temporary-directory cleanup, and starting another job afterward. Forced termination uses the Linux process-group route in this test environment.
- Copying only selected edited-text cells in display order while keeping full-text copy available.
- Qt mouse selection using Ctrl and Shift, with highlight selection restricted to edited-text cells.
- Grouped GUI updates without missing or duplicating received segments.

The Japanese interface was exercised in an offscreen Qt environment. Windows fonts, display scaling, and native dialogs were not visually accepted in this environment.

## Checks not completed

- Final Windows 10 / 11 installation and end-to-end acceptance.
- Windows Credential Manager operations and Windows process-tree cancellation.
- A Windows PyInstaller build and execution on a clean PC without Python.
- Live OpenAI API behavior or model availability for an individual account.
- NVIDIA CUDA/cuDNN inference or GPU memory limits.
- Real Japanese audio accuracy, CER, timing alignment, or measured fast-versus-standard speedup.
- Physical network disconnection while running an installed speech model.
- Long recordings, low disk space, and all supported media codecs in actual user files.

The [Windows acceptance checklist](ACCEPTANCE_TESTS.md) documents the outstanding manual procedure. Automated success is not a claim that all of those Windows checks passed.

## Publication checks

The publication contains source and documentation only. Personal recordings, real transcripts, API credentials, user settings, model files, logs, local environments, compiled libraries, and executable files are excluded.

A scan of publication text found no API-key-shaped values, private-key blocks, personal absolute paths, or email addresses. Tests use synthetic media and placeholder data. This is a scoped source review, not an independent security audit.

The bilingual portfolio configuration was checked for valid JavaScript syntax, one visible Local Transcriber entry, a source-code link, and no live browser-demo link.
