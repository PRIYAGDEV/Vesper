# 🌙 Vesper

<p align="center">
  <strong>Ultra-fast, 100% local, whisper-accurate voice dictation for Windows.</strong><br>
  <em>An aesthetic, private, zero-latency open-source alternative to Wispr Flow.</em>
</p>

<p align="center">
  <a href="https://github.com/PRIYAGDEV/Vesper/releases/latest"><img src="https://img.shields.io/github/v/release/PRIYAGDEV/Vesper?label=Download%20Vesper.exe&style=for-the-badge&logo=windows&color=7C3AED" alt="Download Standalone"></a>
</p>

<p align="center">
  <a href="https://github.com/PRIYAGDEV/Vesper/actions/workflows/ci.yml"><img src="https://github.com/PRIYAGDEV/Vesper/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="#quick-start"><img src="https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078D6?logo=windows&logoColor=white" alt="Platform"></a>
  <a href="#developer-setup"><img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/SYSTRAN/faster-whisper"><img src="https://img.shields.io/badge/Engine-faster--whisper-blueviolet" alt="Engine"></a>
  <a href="#nvidia-gpu-acceleration"><img src="https://img.shields.io/badge/Acceleration-NVIDIA%20CUDA%2012-76B900?logo=nvidia&logoColor=white" alt="CUDA"></a>
  <img src="https://img.shields.io/badge/Privacy-100%25%20Local%20%26%20Offline-success" alt="100% Local">
</p>

---

## 💡 What is Vesper?

**Vesper** brings effortless, AI-powered speech-to-text to **every application across Windows**—VS Code, Obsidian, Discord, Notepad, Google Chrome, Slack, Word, or Windows Terminal.

Press and hold your push-to-talk key (`Ctrl + Win`), speak your thoughts naturally, and release. Vesper transcribes your speech in real time using local Whisper models, cleans up hesitation filler words, converts spoken formatting commands, and pastes the result directly at your active text cursor while preserving your original clipboard contents.

- **Zero Cloud Latency & Zero Subscriptions**: 100% offline. No API keys, no monthly fees, and zero bytes of audio ever leave your computer.
- **Hardware-Accelerated Speed**: Sub-second transcription with NVIDIA CUDA tensor cores (`float16`), with automatic CPU (`int8`) fallback.

---

## ✨ Key Features

- 🎙️ **Global Push-to-Talk**: Hold `Ctrl + Win` (or customize to `Alt + Space`, `Ctrl + Space`, etc.) anywhere in Windows to record; release to instantly inject text.
- 🔮 **Frosted Obsidian Glassmorphism**: Translucent floating HUD pill with liquid spring-physics waveform (9 harmonic bars), ruby recording beacon, and vector checkmark feedback.
- 🧹 **Intelligent Filler Removal**: Automatically strips hesitation words (*"um"*, *"uh"*, *"like"*, *"you know"*) without losing sentence context.
- 📝 **Spoken Formatting Commands**: Speak punctuation and formatting naturally (*"new line"*, *"comma"*, *"period"*, *"question mark"*, *"colon"*).
- 🎨 **Multiple Tone & Writing Styles**:
  - **Casual**: Natural, expressive everyday text.
  - **Professional**: Clean, corporate-ready communication.
  - **Bullet Points**: Formats transcribed speech directly into structured `- ` Markdown lists.
  - **Developer / Code**: Automatically parses and converts identifier names to `camelCase` or `snake_case`.
- 📋 **Non-Destructive Clipboard Preservation**: Vesper uses simulated paste for instant typing into any app, but seamlessly backs up and restores whatever was already in your clipboard.
- 🔍 **Searchable Transcription History**: Access previous transcriptions with instant live search and one-click copy feedback from the system tray.
- 🛡️ **Hallucination Prevention**: Integrated Silero Voice Activity Detection (VAD) and repetition penalty filters eliminate Whisper chant loops and phantom text.

---

## 🗣️ Spoken Commands Reference

Vesper listens for natural formatting phrases and replaces them inline:

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

### ⚡ Option A: Standalone Executable (Recommended)
No Python installation or terminal setup required:
1. Download **[Vesper.exe](https://github.com/PRIYAGDEV/Vesper/releases/latest)** (~354 MB).
2. Double-click `Vesper.exe` — it will dock into your **Windows System Tray** (near the taskbar clock).
3. Focus any text window (VS Code, browser, Word, Discord, Terminal).
4. **Hold `Ctrl + Win`**, speak your message, and **release**!

#### 🔒 Verifying Binary Integrity
To verify the SHA-256 checksum of your downloaded executable:
```powershell
Get-FileHash .\Vesper.exe -Algorithm SHA256
```
Compare the output against the hash published in [`checksums.txt`](https://github.com/PRIYAGDEV/Vesper/releases/latest).

---

### 🐍 Option B: Run from Source

#### 1. Prerequisites
- **Windows 10 / 11** (64-bit)
- **Python 3.10, 3.11, or 3.12**
- A working microphone

#### 2. Clone & Setup

```powershell
# Clone the repository
git clone https://github.com/PRIYAGDEV/Vesper.git
cd Vesper

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies (or use requirements-lock.txt for exact frozen versions)
pip install -r requirements.txt
```

#### 3. Download the Offline Model
Run the setup script to download the high-accuracy multilingual `small` model (~480 MB) into `models/`:

```powershell
python download_small.py
```

#### 4. Launch Vesper
```powershell
# Run with live console logging:
python main.py
# or double-click run_console.bat

# Or run silently in the background:
# double-click start.bat
```

---

## ⚡ NVIDIA GPU Acceleration (Recommended)

Vesper runs out-of-the-box on CPU using quantized `int8` inference. If you have an NVIDIA GeForce RTX or GTX GPU, you can enable sub-second tensor core inference:

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Vesper will automatically detect the CUDA runtime and switch compute to **`float16`** on your GPU.

---

## 📦 Building a Standalone Executable (`.exe`)

You can compile Vesper into a portable Windows application that runs without requiring Python to be installed:

```powershell
python build_exe.py
```

The compiled binary will be placed at `dist/Vesper.exe`, and a desktop shortcut will automatically be created.

---

## 📁 Project Structure

```text
Vesper/
├── .github/
│   ├── workflows/ci.yml      # Automated GitHub Actions test pipeline
│   └── ISSUE_TEMPLATE/       # Bug report & feature request templates
├── config.json               # User preferences & hotkey configuration
├── main.py                   # Application entry point
├── build_exe.py              # PyInstaller executable builder
├── download_small.py         # Offline model downloader
├── requirements.txt          # Package dependencies
├── requirements-lock.txt     # Exact frozen dependencies for reproducible builds
├── run_console.bat           # Launcher with debug terminal
├── start.bat                 # Background tray launcher
├── src/
│   ├── app.py                # Main application coordinator
│   ├── audio.py              # Audio recorder (16kHz mono, Silero VAD)
│   ├── cleanup.py            # Text post-processing, fillers & punctuation
│   ├── config.py             # Configuration manager
│   ├── hotkey.py             # Low-level Windows async key state listener
│   ├── injector.py           # Win32 clipboard text injector & key events
│   ├── transcriber.py        # Faster-Whisper engine (CUDA / CPU auto-detect)
│   └── ui/
│       ├── history.py        # Searchable transcription history window
│       ├── overlay.py        # Liquid spring-physics floating HUD pill
│       ├── settings.py       # Card-based configuration GUI & live mic meter
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

## 📜 Licenses & Third-Party Attributions

Vesper is open-source software licensed under the [MIT License](LICENSE).

This project relies on the following open-source technologies:
- **[OpenAI Whisper](https://github.com/openai/whisper)**: Robust Speech Recognition model weights — [MIT License](https://github.com/openai/whisper/blob/main/LICENSE).
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** by SYSTRAN: CTranslate2 Whisper implementation — [Apache 2.0 License](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE).
- **[Silero VAD](https://github.com/snakers4/silero-vad)**: Voice Activity Detector — [MIT License](https://github.com/snakers4/silero-vad/blob/master/LICENSE).
- **[PySide6](https://wiki.qt.io/Qt_for_Python)**: Official Python bindings for Qt — LGPLv3 / Commercial.

---

## 🛡️ Security

For vulnerability disclosures and reporting guidelines, see [SECURITY.md](SECURITY.md).

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting pull requests.
