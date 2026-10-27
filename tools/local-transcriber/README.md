# Local Transcriber

A Windows desktop app for transcribing audio and video locally with faster-whisper.

Version **0.2.1** · Japanese interface · [日本語ガイド](docs/README.ja.md)

## Features

- Local transcription with CPU or NVIDIA GPU.
- Multiple-file queue, fast/standard modes, and cancellation.
- Timestamped segments with separate original and edited text.
- Copy selected edited cells or the full transcript.
- Export TXT, SRT, JSON, and Word documents.
- Optional AI formatting, meeting notes, and summaries.

## Setup

Requires standard 64-bit Python 3.14.

1. Open `tools/local-transcriber` in this repository.
2. Run `setup_windows.bat`.
3. Place `ffmpeg.exe` and `ffprobe.exe` in `vendor/ffmpeg` or add them to `PATH`.
4. Run `run_windows.bat`.
5. Temporarily disable offline mode in Settings and download a speech model.

Add files, choose a model and device, then click **文字起こし開始** (Start transcription). After model setup, local transcription works offline.

## Optional AI

Register your own OpenAI API key and a Responses-compatible text model ID, disable offline mode, and enable AI communication.

Text is sent only after you review and confirm it. Source audio and video are not uploaded. The API key is stored in Windows Credential Manager.

## Validation

Windows operation, GPU transcription, and live OpenAI API integration have been verified by the maintainer. The automated suite also passed 41 tests on Linux / Python 3.14.

[Validation details](docs/VALIDATION.md)

## Distribution

Model weights, FFmpeg binaries, and a prebuilt executable are not included. Run `build_windows.bat` to build the Windows app.

No open-source license is provided. See the [repository policy](../../README.md#license) and [third-party notices](THIRD_PARTY_NOTICES.md).
