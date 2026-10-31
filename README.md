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
  <a href="#-quick-start-30-seconds"><img src="https://img.shields.io/badge/Platform-Windows%2011%20%7C%2010-0078D6?logo=windows&logoColor=white" alt="Platform"></a>
  <a href="#-option-b-run-from-source"><img src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white" alt="Python"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://github.com/SYSTRAN/faster-whisper"><img src="https://img.shields.io/badge/Engine-faster--whisper-blueviolet" alt="Engine"></a>
  <a href="#-nvidia-gpu-acceleration-recommended"><img src="https://img.shields.io/badge/Acceleration-NVIDIA%20CUDA%2012-76B900?logo=nvidia&logoColor=white" alt="CUDA"></a>
  <img src="https://img.shields.io/badge/Privacy-100%25%20Local%20%26%20Offline-success" alt="100% Local">
</p>

---

## ⚡ Quick Start (30 Seconds)

Get up and running with voice dictation in seconds:

1. **Download**: Grab the latest **[Vesper.exe](https://github.com/PRIYAGDEV/Vesper/releases/latest)** (~354 MB standalone).
2. **Launch**: Double-click `Vesper.exe` — it will dock cleanly in your **Windows System Tray** (bottom-right near your clock).
3. **Dictate Anywhere**:
   - Focus any text field (*VS Code, Chrome, Obsidian, Discord, Slack, Word, or Terminal*).
   - **Hold `Ctrl + Win`** (or your custom hotkey) and speak naturally.
   - **Release the hotkey** — your transcribed words instantly type right at your cursor!

> [!TIP]
> **Clipboard Safe**: Vesper uses instant paste injection to support every Windows application, but it seamlessly saves and restores your clipboard contents. Whatever you had copied before remains untouched!

---

## 💡 What is Vesper?

**Vesper** brings effortless, AI-powered speech-to-text to **every single application across Windows**. 

Unlike cloud dictation software that charges recurring subscriptions and transmits your private microphone audio to remote servers, Vesper runs **100% on your machine**:

- 🔒 **Absolute Privacy**: Zero bytes of audio or text ever leave your PC. Operates fully offline without internet.
- ⚡ **Near-Zero Latency**: Sub-second transcription with NVIDIA CUDA Tensor Cores (`float16`), with automatic CPU (`int8`) fallback.
- 🎯 **Universal Compatibility**: Works in every app you type in — IDEs, web browsers, document editors, and chat messengers.
- 🪄 **Hands-Free Polish**: Automatically removes filler words (*"um"*, *"uh"*, *"like"*), translates spoken punctuation (*"new line"*, *"period"*), and adjusts to your preferred tone.

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| 🎙️ **Global Push-to-Talk** | Hold `Ctrl + Win` (or customize to `Alt + Space`, `Ctrl + Space`, etc.) anywhere in Windows to record; release to inject text. |
| 🔮 **Obsidian Glassmorphism HUD** | Translucent floating pill overlay with liquid spring-physics waveform (9 harmonic bars), ruby recording beacon, and vector checkmark feedback. |
| 🧹 **Intelligent Filler Removal** | Automatically strips hesitation words (*"um"*, *"uh"*, *"like"*, *"you know"*) while preserving natural sentence structure. |
| 📝 **Spoken Formatting Commands** | Natural speech macros for formatting (*"new line"*, *"new paragraph"*, *"comma"*, *"period"*, *"question mark"*, *"colon"*). |
| 🎨 **Adaptive Writing Styles** | Select between **Casual**, **Professional**, **Bullet Points** (Markdown list format), and **Developer/Code** (`camelCase` / `snake_case`). |
| 🌐 **Live Translation Mode** | Built-in support for multilingual speech, including real-time **Hindi-to-English translation** with conditioned prompting. |
| 📋 **Non-Destructive Clipboard** | Injects text instantaneously using synthetic keystrokes while automatically restoring whatever text or image was in your clipboard. |
| 🛡️ **Silero VAD & Anti-Hallucination** | Voice Activity Detection (VAD) and repetition penalty filters eliminate phantom transcriptions, background noise, and Whisper chant loops. |
| 🔍 **Searchable History Viewer** | Browse your recent transcriptions with instant live search, timestamps, character counts, and one-click copy feedback. |
| ⚙️ **Interactive Settings GUI** | Sleek card-based configuration window with a real-time microphone level meter, hotkey recorder, and model selector. |

---

## 🗣️ Spoken Commands Reference

Vesper dynamically replaces spoken formatting instructions with proper punctuation and whitespace:

| Spoken Phrase | Output | Spoken Example | Injected Result |
| :--- | :---: | :--- | :--- |
| `"new line"` / `"newline"` | `\n` | *"Hello new line world"* | Hello<br>world |
| `"new paragraph"` | `\n\n` | *"First section new paragraph Second section"* | First section<br><br>Second section |
| `"period"` / `"full stop"` | `.` | *"Feature is ready period"* | Feature is ready. |
| `"comma"` | `,` | *"Fast comma private comma local"* | Fast, private, local |
| `"question mark"` | `?` | *"Did you review the PR question mark"* | Did you review the PR? |
| `"exclamation mark"` | `!` | *"Build succeeded exclamation mark"* | Build succeeded! |
| `"colon"` | `:` | *"Note colon update config"* | Note: update config |
| `"semicolon"` | `;` | *"Item A semicolon item B"* | Item A; item B |
| `"dash"` / `"hyphen"` | `-` | *"End to end test"* | End-to-end test |

---

## 🛠️ Architecture & How It Works

```
 ┌─────────────────────────────────────────────────────────┐
 │                   Global Hotkey Hook                    │
 │               (Windows Asynchronous Keys)               │
 └─────────────┬─────────────────────────────▲─────────────┘
               │ Press                       │ Release
               ▼                             │
 ┌───────────────────────────┐ ┌─────────────┴─────────────┐
 │       PyAudio Stream      │ │    Faster-Whisper Engine  │
 │     16 kHz Mono Audio     │ │    (CUDA fp16 / CPU int8) │
 └─────────────┬─────────────┘ └─────────────▲─────────────┘
               │ Raw Audio Chunks            │ Clean WAV
               ▼                             │
 ┌───────────────────────────┐ ┌─────────────┴─────────────┐
 │   Silero VAD / Filter     ├─►  Text Cleanup & Post-Proc │
 │   (Zero-Hallucination)    │ │  (Fillers, Commands, Tone)│
 └───────────────────────────┘ └─────────────┬─────────────┘
                                             │ Formatted Text
                                             ▼
 ┌─────────────────────────────────────────────────────────┐
 │           Non-Destructive Clipboard Injector            │
 │     (Backup Clipboard ➔ Ctrl+V ➔ Restore Clipboard)     │
 └─────────────────────────────────────────────────────────┘
```

1. **Zero-Latency Capture**: While the hotkey is held, raw audio is streamed at 16 kHz mono.
2. **Glass HUD Waveform**: Spring-physics animation reflects live microphone input levels on screen.
3. **Silero VAD Trimming**: Removes silence and background noise before inference.
4. **Faster-Whisper Inference**: Generates raw tokens locally using CTranslate2.
5. **Text Cleanup & Style Application**: Applies punctuation formatting, removes hesitation words, and applies tone formatting (e.g. code identifiers or bullet points).
6. **Non-Destructive Injection**: Backs up user clipboard, injects formatted text via `Ctrl+V`, and seamlessly restores the original clipboard content.

---

## 🚀 Installation & Setup

### ⚡ Option A: Standalone Executable (Recommended)

No Python installation or terminal configuration required:

1. Download **[Vesper.exe](https://github.com/PRIYAGDEV/Vesper/releases/latest)**.
2. *(Optional)* Verify binary integrity using PowerShell:
   ```powershell
   Get-FileHash .\Vesper.exe -Algorithm SHA256
   ```
   Compare with the official SHA-256 hash in [`checksums.txt`](https://github.com/PRIYAGDEV/Vesper/releases/latest).
3. Run `Vesper.exe`! The app docks to the system tray and is immediately ready.

---

### 🐍 Option B: Run from Source

#### 1. System Requirements
- **OS**: Windows 10 or Windows 11 (64-bit)
- **Python**: 3.10, 3.11, or 3.12
- **Microphone**: Any standard USB, 3.5mm, or integrated mic
- **GPU (Optional)**: NVIDIA GeForce GTX/RTX for hardware acceleration

#### 2. Clone & Environment Setup

```powershell
# Clone the repository
git clone https://github.com/PRIYAGDEV/Vesper.git
cd Vesper

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies (or use requirements-lock.txt for exact pinned versions)
pip install -r requirements.txt
```

#### 3. Download the Offline Model

Download the high-accuracy multilingual `small` Whisper model (~480 MB) into the local `models/` directory:

```powershell
python download_small.py
```

#### 4. Launch Vesper

```powershell
# Launch with live debug terminal logging:
python main.py
# (or double-click run_console.bat)

# Launch silently into the background / tray:
# double-click start.bat
```

---

## ⚡ NVIDIA GPU Acceleration (Recommended)

Vesper runs exceptionally fast on CPU using quantized `int8` CTranslate2 inference. However, if you have an NVIDIA GeForce RTX or GTX graphics card, you can unlock **sub-second inference speed**:

```powershell
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
```

Vesper automatically detects your NVIDIA CUDA libraries at startup and dynamically switches compute to **`float16`** on your GPU Tensor Cores.

---

## 📦 Building a Standalone Executable (`.exe`)

You can compile your own standalone, portable Windows application:

```powershell
python build_exe.py
```

The output executable will be generated at `dist/Vesper.exe` with bundled icons, UI assets, and an optional desktop shortcut.

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

Run the full automated test suite to verify every subsystem:

```powershell
python tests/test_hotkey.py
python tests/test_cleanup.py
python tests/test_injector.py
python tests/test_audio.py
python tests/test_full_pipeline.py
```

---

## ❓ Frequently Asked Questions (FAQ)

<details>
<summary><strong>Does any of my voice or audio data leave my computer?</strong></summary>
<br>
<strong>No. Absolutely never.</strong> All speech recognition, voice activity detection, and formatting are done 100% locally on your own CPU/GPU using CTranslate2 and Faster-Whisper. Vesper requires no internet connection and does not make external network requests for transcription.
</details>

<details>
<summary><strong>Do I need a dedicated NVIDIA graphics card to use Vesper?</strong></summary>
<br>
No! Vesper works out-of-the-box on standard multi-core CPUs using optimized <code>int8</code> quantization. Having an NVIDIA GPU simply accelerates transcription to sub-second speeds.
</details>

<details>
<summary><strong>How do I change the push-to-talk hotkey?</strong></summary>
<br>
Right-click the Vesper icon in your Windows System Tray and select <strong>Settings</strong>. In the hotkey card, click the hotkey recorder and press your preferred combination (e.g. <code>Ctrl + Win</code>, <code>Alt + Space</code>, <code>Ctrl + Space</code>).
</details>

<details>
<summary><strong>Will Vesper overwrite what I already copied to my clipboard?</strong></summary>
<br>
No. Vesper takes a snapshot of your clipboard contents right before injection and restores it immediately after pasting. Your copied text, code snippets, or images remain safely intact.
</details>

<details>
<summary><strong>Which Whisper models can I use?</strong></summary>
<br>
By default, Vesper uses the balanced <code>small</code> model. Through the settings menu or <code>config.json</code>, you can select from <code>tiny</code>, <code>base</code>, <code>small</code>, <code>medium</code>, or <code>large-v3</code> depending on your system RAM/VRAM capacity.
</details>

<details>
<summary><strong>How does the Hindi-to-English translation work?</strong></summary>
<br>
When the task is set to <code>translate</code> with language <code>hi</code>, Vesper utilizes Whisper's cross-lingual translation engine with conditioned prompting to transcribe spoken Hindi directly into polished English text in real time.
</details>

---

## 📜 Licenses & Third-Party Attributions

Vesper is open-source software licensed under the **[MIT License](LICENSE)**.

This project relies on the following open-source technologies:
- **[OpenAI Whisper](https://github.com/openai/whisper)**: Robust Speech Recognition model weights — [MIT License](https://github.com/openai/whisper/blob/main/LICENSE).
- **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)** by SYSTRAN: CTranslate2 Whisper implementation — [Apache 2.0 License](https://github.com/SYSTRAN/faster-whisper/blob/master/LICENSE).
- **[Silero VAD](https://github.com/snakers4/silero-vad)**: Voice Activity Detector — [MIT License](https://github.com/snakers4/silero-vad/blob/master/LICENSE).
- **[PySide6](https://wiki.qt.io/Qt_for_Python)**: Official Python bindings for Qt — LGPLv3 / Commercial.

---

## 🛡️ Security

For vulnerability disclosures and reporting guidelines, see [SECURITY.md](SECURITY.md).

---

## 🤝 Contributing

Contributions, bug reports, and suggestions are warmly welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting pull requests.

---

## 👨‍💻 Author & GitHub Activity

<div align="center">

Crafted with ⚡ by **[PRIYAGDEV](https://github.com/PRIYAGDEV)**

<br>

<p align="center">
  <img src="https://github-stats-extended.vercel.app/api?username=PRIYAGDEV&show_icons=true&theme=tokyonight&hide_border=true" alt="PRIYAGDEV's GitHub Stats" />
  <img src="https://streak-stats.demolab.com?user=PRIYAGDEV&theme=tokyonight&hide_border=true" alt="PRIYAGDEV's GitHub Streak" />
</p>
<p align="center">
  <img src="https://github-stats-extended.vercel.app/api/top-langs/?username=PRIYAGDEV&layout=compact&theme=tokyonight&hide_border=true" alt="Top Languages" />
</p>

[![GitHub followers](https://img.shields.io/github/followers/PRIYAGDEV?style=social)](https://github.com/PRIYAGDEV)
[![GitHub stars](https://img.shields.io/github/stars/PRIYAGDEV?style=social)](https://github.com/PRIYAGDEV)

</div>
