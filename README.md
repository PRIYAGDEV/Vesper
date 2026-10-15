# FreeFlow 🎙️

> **High-performance, 100% private system-wide voice dictation for Windows 11.**  
> An open-source, local alternative to **Wispr Flow**. Dictate anywhere—Notepad, VS Code, Google Chrome, Word, Slack, or any active window—with a single push-to-talk hotkey.

---

## ✨ Features

- **🎯 Global Push-to-Talk**: Hold `Ctrl+Win` (or customize to `Alt+Space`, `Ctrl+Space`, etc.) to record from your microphone; release to instantly transcribe and paste into your active window.
- **🔒 100% Offline & Private**: Powered locally by `faster-whisper`. No cloud API keys, no subscriptions, and zero audio ever leaves your computer.
- **⚡ NVIDIA GPU Acceleration**: Native support for NVIDIA GeForce RTX/GTX GPUs using CUDA `float16` tensor cores for sub-second transcriptions (~0.2s–0.3s), with an automatic CPU `int8` fallback.
- **🌊 Audio-Reactive Floating Overlay**: Non-focus-stealing translucent floating pill with a dynamic waveform that bounces live to your voice amplitude, violet shimmer during transcription, and green checkmark on completion.
- **📋 Automatic Clipboard Preservation**: Injects text at your exact cursor position via simulated `Ctrl+V` and **automatically restores your previous clipboard contents**.
- **🧹 Smart Cleanup & Spoken Commands**:
  - Automatically strips hesitation fillers: *"um"*, *"uh"*, *"like"*, *"you know"*.
  - Converts spoken punctuation commands:
    - `"new line"` / `"newline"` → `\n`
    - `"new paragraph"` → `\n\n`
    - `"period"` / `"full stop"` → `.`
    - `"comma"` → `,`
    - `"question mark"` → `?`
    - `"exclamation mark"` → `!`
    - `"colon"` → `:`
    - `"semicolon"` → `;`
- **✍️ Writing Style Modes**: Toggle between **Casual**, **Professional** (polishes business tone), **Bullet Points** (auto-formats lists), and **Developer / Code** (formats `camelCase` and `snake_case`).
- **🎛️ Modern Settings & History**: Access system preferences and a 20-item transcription history with one-click copy buttons from the Windows System Tray.

---

## 📁 Repository Structure

```text
freeflow/
├── config.json               # Default user configuration
├── download_small.py         # Script to download offline Whisper model
├── main.py                   # Application launch script
├── requirements.txt          # Python dependencies
├── build_exe.py              # Standalone PyInstaller builder
├── run_console.bat           # Launcher with visible terminal logs
├── start.bat                 # Background tray launcher
├── src/
│   ├── app.py                # Main application coordinator
│   ├── audio.py              # Audio recorder (16kHz mono, Silero VAD)
│   ├── cleanup.py            # Text post-processing, fillers & spoken commands
│   ├── config.py             # Configuration manager
│   ├── hotkey.py             # Low-level Windows async key state listener
│   ├── injector.py           # Win32 clipboard text injector & keybd_event
│   ├── transcriber.py        # Faster-Whisper engine (CUDA/CPU fallback)
│   └── ui/
│       ├── history.py        # Transcription history dialog
│       ├── overlay.py        # Floating translucent status pill
│       ├── settings.py       # Preferences & live microphone meter
│       └── tray.py           # Windows system tray icon & menu
└── tests/
    ├── hello_world.wav       # Automated test audio sample
    ├── test_audio.py         # Audio capture & WAV validation test
    ├── test_cleanup.py       # Filler removal & spoken commands test
    ├── test_full_pipeline.py # End-to-end integration test
    ├── test_hotkey.py        # Hotkey parser and state triggers test
    └── test_injector.py      # Clipboard preservation & injection test
```

---

## 🚀 Quick Start

### 1. Prerequisites
- Windows 10 or 11 (64-bit)
- Python 3.10, 3.11, or 3.12
- A working microphone

### 2. Clone & Setup Environment

```powershell
# Clone the repository
git clone https://github.com/your-username/freeflow.git
cd freeflow

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Download the Local Whisper Model
Run the helper script to download the high-accuracy multilingual `small` model (~480 MB) into the `models/` directory for 100% offline use:

```powershell
python download_small.py
```

### 4. Run FreeFlow
```powershell
# With console logs:
python main.py
# or double-click run_console.bat

# Silent background mode:
# double-click start.bat
```

- FreeFlow docks into your **Windows System Tray** (near the clock on the bottom-right).
- Click into any text window (VS Code, Notepad, Browser, Discord, Word).
- **Hold `Ctrl+Win`**, speak into your mic, and **release**.

---

## ⚡ Enabling NVIDIA GPU Acceleration (Optional)

If your PC has a dedicated NVIDIA GPU (RTX / GTX):

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

FreeFlow will automatically detect CUDA and activate **`float16`** tensor core inference for near-instantaneous transcription speeds.

---

## 📦 Building Standalone `.exe`

To package FreeFlow into a single portable Windows executable:

```powershell
python build_exe.py
```

The compiled standalone executable and a desktop shortcut will be generated at `dist/FreeFlow.exe`.

---

## 🧪 Running Tests

Verify the entire pipeline locally:

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
