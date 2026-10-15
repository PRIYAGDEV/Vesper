# 🌊 FreeFlow

<p align="center">
  <strong>Ultra-fast, 100% local, system-wide voice dictation for Windows.</strong><br>
  <em>An open-source, completely private alternative to Wispr Flow.</em>
</p>

<p align="center">
  <a href="#features"><img src="https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078D6?logo=windows&logoColor=white" alt="Platform"></a>
  <a href="#quick-start"><img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/SYSTRAN/faster-whisper"><img src="https://img.shields.io/badge/Engine-faster--whisper-blueviolet" alt="Engine"></a>
  <a href="#nvidia-gpu-acceleration"><img src="https://img.shields.io/badge/Acceleration-NVIDIA%20CUDA%2012-76B900?logo=nvidia&logoColor=white" alt="CUDA"></a>
  <img src="https://img.shields.io/badge/Privacy-100%25%20Local%20%26%20Offline-success" alt="100% Local">
</p>

---

## 💡 What is FreeFlow?

**FreeFlow** gives you instant, AI-powered voice typing in **any application on Windows**—VS Code, Discord, Notepad, Google Chrome, Slack, Obsidian, Microsoft Office, or Windows Terminal.

Press and hold your hotkey (`Ctrl + Win`), speak naturally, and release. FreeFlow transcribes your speech in real time using local Whisper models, cleans up hesitation filler words, processes spoken formatting commands, and pastes the result directly at your active text cursor while preserving your original clipboard contents.

- **Zero Cloud Latency & Zero Subscriptions**: 100% offline. No API keys, no subscription paywalls, and zero bytes of audio ever leave your computer.
- **Hardware-Accelerated Speed**: Sub-second transcription with NVIDIA CUDA tensor cores (`float16`), with seamless automatic fallback to CPU (`int8`).

---

## ✨ Key Features

- 🎙️ **Global Push-to-Talk**: Hold `Ctrl + Win` (or configure your own custom hotkey like `Alt + Space`) anywhere in Windows to record; release to instantly inject text.
- 💻 **Audio-Reactive Floating Pill**: Translucent, non-intrusive floating overlay with a live bouncing waveform synchronized to your voice amplitude, shimmer animation during transcription, and status confirmation.
- 🧹 **Intelligent Filler Removal**: Automatically strips hesitation words (*"um"*, *"uh"*, *"like"*, *"you know"*) without losing sentence context.
- 📝 **Spoken Formatting Commands**: Speak punctuation and formatting naturally (*"new line"*, *"comma"*, *"period"*, *"question mark"*, *"colon"*).
- 🎨 **Multiple Tone & Writing Styles**:
  - **Casual**: Natural, expressive everyday text.
  - **Professional**: Clean, corporate-ready communication.
  - **Bullet Points**: Formats transcribed speech directly into structured `- ` Markdown lists.
  - **Developer / Code**: Automatically parses and converts identifier names to `camelCase` or `snake_case`.
- 📋 **Non-Destructive Clipboard Preservation**: FreeFlow uses simulated paste for instant typing into any app, but seamlessly backs up and restores whatever was already in your clipboard.
- ⏱️ **Transcription History & Tray Menu**: Quickly access previous transcriptions with one-click copy from the Windows system tray.
- 🤖 **Hallucination Prevention**: Integrated Silero Voice Activity Detection (VAD) and repetition penalty filters eliminate Whisper chant loops and phantom text.

---

## 🗣️ Spoken Commands Reference

FreeFlow listens for natural formatting phrases and replaces them inline:

| Spoken Phrase | Output | Example Spoken | Resulting Text |
| :--- | :--- | :--- | :--- |
| `"new line"` / `"newline"` | `\n` | *"Hello new line world"* | Hello<br>world |
| `"new paragraph"` | `\n\n` | *"Intro new paragraph Details"* | Intro<br><br>Details |
| `"period"` / `"full stop"` | `.` | *"Ready to go period"* | Ready to go. |
| `"comma"` | `,` | *"First comma second"* | First, second |
| `"question mark"` | `?` | *"Are you sure question mark"* | Are you sure? |
| `"exclamation mark"` | `!` | *"Look out exclamation mark"* | Look out! |
| `"colon"` | `:` | *"Note colon update"* | Note: update |
| `"semicolon"` | `;` | *"Part one semicolon part two"* | Part one; part two |

---

## 🚀 Quick Start

### 1. Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.10, 3.11, or 3.12**
- A working microphone

### 2. Clone & Setup

```powershell
# Clone the repository
git clone https://github.com/PRIYAGDEV/FreeFlow.git
cd FreeFlow

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Download the Offline Model
Run the setup script to download the high-accuracy multilingual `small` model (~480 MB) into `models/`:

```powershell
python download_small.py
```

### 4. Launch FreeFlow
```powershell
# Run with live console logging:
python main.py
# or double-click run_console.bat

# Or run silently in the background:
# double-click start.bat
```

1. Look for the microphone icon in your **Windows System Tray** (bottom-right taskbar).
2. Click into any text field (VS Code, browser, Word, Discord).
3. **Hold `Ctrl + Win`**, speak your message, and **release**.

---

## ⚡ NVIDIA GPU Acceleration (Recommended)

FreeFlow runs out-of-the-box on CPU using quantized `int8` inference. If you have an NVIDIA GeForce RTX or GTX GPU, you can enable sub-second tensor core inference:

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

FreeFlow will automatically detect the CUDA runtime and switch compute to **`float16`** on your GPU.

---

## 📦 Building a Standalone Executable (`.exe`)

You can compile FreeFlow into a portable Windows application that runs without requiring Python to be installed:

```powershell
python build_exe.py
```

The compiled binary will be placed at `dist/FreeFlow.exe`, and a desktop shortcut will automatically be created.

---

## 📁 Project Structure

```text
FreeFlow/
├── config.json               # User preferences & hotkey configuration
├── main.py                   # Application entry point
├── build_exe.py              # PyInstaller executable builder
├── download_small.py         # Offline model downloader
├── requirements.txt          # Python package dependencies
├── run_console.bat           # Quick launcher with debug terminal
├── start.bat                 # Silent background tray launcher
├── src/
│   ├── app.py                # Main application coordinator
│   ├── audio.py              # Audio recorder (16kHz mono, Silero VAD)
│   ├── cleanup.py            # Text post-processing, fillers & punctuation
│   ├── config.py             # Configuration manager
│   ├── hotkey.py             # Low-level Windows async key state listener
│   ├── injector.py           # Win32 clipboard text injector & key events
│   ├── transcriber.py        # Faster-Whisper engine (CUDA / CPU auto-detect)
│   └── ui/
│       ├── history.py        # Transcription history window
│       ├── overlay.py        # Audio-reactive floating status pill
│       ├── settings.py       # Configuration GUI & live mic meter
│       └── tray.py           # System tray icon & context menus
└── tests/
    ├── hello_world.wav       # Automated audio test fixture
    ├── test_audio.py         # Audio capture & WAV validation test
    ├── test_cleanup.py       # Filler removal & spoken command test
    ├── test_full_pipeline.py # End-to-end integration test
    ├── test_hotkey.py        # Hotkey trigger & release test
    └── test_injector.py      # Clipboard preservation & injection test
```

---

## 🧪 Running Tests

Run the comprehensive test suite to verify all subsystem components:

```powershell
python tests/test_hotkey.py
python tests/test_cleanup.py
python tests/test_injector.py
python tests/test_audio.py
python tests/test_full_pipeline.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
