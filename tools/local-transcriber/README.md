# Local Transcriber

Version **0.2.1** — Windows desktop transcription MVP, source release.

A Python / PySide6 application for transcribing recorded audio and video locally with faster-whisper. Review and edit timestamped segments, copy the edited text, export documents or subtitles, and optionally send a confirmed text excerpt to OpenAI for formatting, meeting notes, or summarization.

The interface currently uses Japanese labels. [Japanese setup and usage guide](docs/README.ja.md).

## Features

- Queue MP3, WAV, M4A, FLAC, MP4, MOV, MKV, and WebM files.
- Inspect the first audio stream with ffprobe and convert it to temporary 16 kHz mono PCM using FFmpeg.
- Transcribe with tiny, base, small, medium, or large-v3 models; Japanese, English, or automatic language selection.
- CPU / int8 and optional NVIDIA CUDA / float16 execution.
- Fast and standard decoding modes, plus configurable CPU thread count.
- Run media inspection and recognition in a separate process, with cancellation and file-level failure handling.
- Preserve the raw transcript separately from edited text.
- Select only edited-text cells, use Ctrl or Shift for multiple selection, and copy selected cells or the full edited transcript.
- Export TXT, SRT, JSON, and DOCX. Timestamp display is optional for TXT and DOCX.
- Save and reload projects without rerunning recognition. Results remain readable when the source file is missing.
- Optional, text-only OpenAI Responses API integration with a preview and explicit confirmation before each request.

## Requirements

Target environment:

- Windows 10 / 11, 64-bit.
- Standard CPython 3.14, 64-bit, with the GIL. Free-threaded Python builds are not supported by this release configuration.
- FFmpeg and ffprobe executable files available in `vendor/ffmpeg` or on `PATH`.
- An explicitly downloaded speech model. After setup, local recognition can run without an internet connection.

The application source and Python dependency versions are included. FFmpeg binaries, CUDA/cuDNN runtime libraries, model weights, and a prebuilt Windows executable are **not** included.

Windows is the intended platform, but final Windows acceptance and packaging validation remain outstanding. See [Validation and limitations](docs/VALIDATION.md).

## Installation

This source lives in the portfolio repository under `tools/local-transcriber`.

1. Clone or download the portfolio repository and open the `tools/local-transcriber` folder.
2. Install standard 64-bit Python 3.14 with the Python Launcher.
3. Run `setup_windows.bat`. It creates a `.venv314` virtual environment and installs the pinned application and development dependencies.
4. Obtain a suitable Windows FFmpeg build through the [official FFmpeg download page](https://ffmpeg.org/download.html#build-windows). Put `ffmpeg.exe` and `ffprobe.exe` in `vendor/ffmpeg`. Shared-library builds also require their supporting DLLs.
5. Run `run_windows.bat`.
6. In Settings, temporarily disable offline mode, select a model such as `small`, and explicitly choose the model download action. Enable offline mode again after the download completes if external connectivity is not needed.

Models are downloaded only through the explicit download action. Transcription does not automatically download a missing model.

## Usage

1. Add files using the file dialog or drag and drop.
2. Wait for inspection to complete. Inspection reaching 100% means the file check is complete; recognition starts separately.
3. Choose the language, model, device, and decoding mode, then click **文字起こし開始** (Start transcription).
4. Edit cells in the **編集テキスト** column. Raw text and segment timestamps remain separate.
5. Use **選択行コピー** for selected edited-text cells, **全文コピー** for the full edited transcript, or export a file.
6. Save a project JSON to keep raw text, edits, timestamps, recognition settings, and AI results together.

Pending, failed, and cancelled files are processed in queue order. One failed file does not stop later files. Cancelling stops the current job and the remaining queue, retains received segments, and attempts to remove the temporary audio. Restarting recognition reruns the file; it does not resume from an exact audio offset. Earlier results are checkpointed before a rerun receives a new project identity.

Completed files can be transcribed again by saving their project, removing them from the list, and adding the original media again. Removing a row does not delete the media or saved projects.

## Decoding modes and performance

- **Fast:** `beam_size=1`, `best_of=1`, `temperature=(0.0,)`. Reduces candidate search and temperature fallback attempts. This is the default for new settings and older settings files that have no mode field.
- **Standard:** `beam_size=5`, `best_of=5`, temperatures from `0.0` through `1.0` in `0.2` increments. Retains the earlier decoding configuration.

Both modes use VAD and segment-level timestamps. Fast mode can reduce recognition accuracy. No measured speedup or accuracy improvement is claimed.

The CPU thread setting of `0` delegates to the recognition library. Increasing thread count does not necessarily improve throughput. Each file starts a separate worker and reloads its speech model; there is no cross-file model cache.

Received segments are retained immediately, while GUI updates are grouped at approximately 200 ms intervals. The recorded processing time includes hashing, preprocessing, model loading, and recognition, but excludes worker startup and result saving. Progress percentages are estimates rather than remaining-time predictions.

## Storage and privacy

Runtime files are stored under `%LOCALAPPDATA%\LocalTranscriber`:

- `projects`: project checkpoints, including transcript text and source-file paths.
- `models`: downloaded speech model files and installation markers.
- `settings.json`: settings, without an API key.
- `logs`: application job types and error codes; transcript text and API keys are not intentionally written to application logs.

The source media is referenced and is not overwritten. Work files and credentials are excluded from this publication.

The export-folder setting is the initial location shown by export dialogs. Automatic project checkpoints use the project folder above. A manually saved JSON is a snapshot; later edits are checkpointed to the standard project folder until another explicit save is made.

The offline setting blocks the application's model-download and AI actions. It is not an operating-system firewall. Models must be installed before offline recognition can be used. Interrupted model downloads may leave a cache for the next explicit download attempt.

Atomic file replacement is used for saved results. Temporary-audio deletion and recovery of the most recent edits are not guaranteed after a power failure or forced operating-system termination.

## Optional AI integration

Local transcription does not require an API key.

To use AI text processing:

1. Register an OpenAI API key in Settings. The application uses the Windows Credential Manager backend rather than a plaintext settings file.
2. Enter a Responses-compatible text model ID available to your API account.
3. Disable offline mode and enable AI communication.
4. Choose formatting, meeting notes, or summarization, then review and confirm the exact text and instructions before sending.

The application sends text and processing instructions to `https://api.openai.com/v1/responses`. It does not upload the source audio, video, or the project JSON. An individual request is limited to 60,000 input characters; longer text is not automatically split. The confirmed input and generated output are preserved separately from the raw transcript.

Requests use `store=False`, a 120-second timeout, no automatic retry, and a 6,000-token maximum output budget. These settings do not establish a guarantee of zero provider-side retention, successful completion for every length, or cancellation of an already sent request. Model availability and response behavior depend on the API account and selected model. Generated text must be checked against the original transcript.

The live API integration has not been verified in this release. No API key is supplied with the source.

## Command line

Run commands from the folder containing `run.py`:

```powershell
# Explicit download; requires network access.
.\.venv314\Scripts\python.exe -m local_transcriber.cli download small

# Local transcription after model installation.
.\.venv314\Scripts\python.exe -m local_transcriber.cli transcribe "C:\Audio\sample.wav" --model small --device cpu --language ja --mode fast --output "C:\Output\sample_project.json"

# Read-only dependency and model diagnostics; no credential lookup or API request.
.\.venv314\Scripts\python.exe tools\doctor.py

# Automated checks.
.\.venv314\Scripts\python.exe -m pytest -q
```

The CLI refuses to overwrite existing results unless `--overwrite` is supplied. It is a core-verification interface; unlike the GUI, it does not save partial recognition on cancellation.

## Windows packaging

After preparing the dependencies and FFmpeg files, run `build_windows.bat` on Windows. The script runs tests and then invokes PyInstaller using `LocalTranscriber.spec`.

The intended output is `dist/LocalTranscriber/LocalTranscriber.exe`. Distribute the **entire** `dist/LocalTranscriber` directory, not the executable alone. Model weights are separate. The build procedure is supplied, but a Windows build and clean-PC execution have not been validated.

Do not describe this source release as a tested Windows installer or a browser application.

## Project structure

- `local_transcriber/domain.py`: serializable projects, segments, and settings.
- `local_transcriber/media.py`: media inspection, source hashing, and preprocessing.
- `local_transcriber/engine.py`: local speech recognition and segment events.
- `local_transcriber/controller.py`, `worker.py`: spawned worker lifecycle, cancellation, IPC, and cleanup.
- `local_transcriber/storage.py`: atomic persistence and document/subtitle exports.
- `local_transcriber/ai.py`: credential backend and opt-in text processing.
- `local_transcriber/gui.py`: queue, edited-cell selection, exports, settings, and AI preview.
- `tests`: synthetic media, persistence, API mocks, GUI, and process-control checks.
- `tools/cer.py`: CER calculation against a separately prepared reference transcript.

## Validation

The public validation record is in [docs/VALIDATION.md](docs/VALIDATION.md). The [Windows acceptance checklist](docs/ACCEPTANCE_TESTS.md) is a procedure, not a statement that its unchecked items have passed.

Real-audio CER, Windows final acceptance, CUDA inference, live API behavior, and Windows executable distribution remain unverified. Speaker diarization, real-time capture, word-level timestamps, automatic translation, and cloud speech recognition are outside this MVP.

## Publication and third-party components

This publication contains application source, synthetic tests, and documentation. It excludes personal recordings, real meeting transcripts, user configuration, credentials, model weights, and executable binaries.

No open-source license is added to the application source. The portfolio repository's existing source-publication policy is preserved. Third-party components retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
