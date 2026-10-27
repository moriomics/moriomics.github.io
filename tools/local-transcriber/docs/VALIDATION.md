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

## Maintainer-confirmed manual verification

The project maintainer confirmed completion of the following checks on 2026-10-27:

- Operation on a Windows PC.
- GPU transcription.
- Live OpenAI API integration.

These manual checks were performed separately from the Linux automated suite described above. The earlier statement that Windows, GPU, and live API verification were incomplete is superseded by this report.

The [acceptance checklist](ACCEPTANCE_TESTS.md) remains available as a reusable testing template. Its blank environment fields and unchecked boxes are not the current validation status.

## Evaluation records

Measured CER and fast-versus-standard speed comparisons are not published. No numerical accuracy or speedup claim is made.

## Publication checks

The publication contains source and documentation only. Personal recordings, real transcripts, API credentials, user settings, model files, logs, local environments, compiled libraries, and executable files are excluded.

A scan of publication text found no API-key-shaped values, private-key blocks, personal absolute paths, or email addresses. Tests use synthetic media and placeholder data. This is a scoped source review, not an independent security audit.

The bilingual portfolio configuration was checked for valid JavaScript syntax, one visible Local Transcriber entry, a source-code link, and no live browser-demo link.
