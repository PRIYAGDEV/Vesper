"""Wispr Flow Clone - System-wide Voice Dictation for Windows 11.

Hold your push-to-talk hotkey (default: Ctrl+Win) anywhere in Windows to dictate,
release to transcribe locally and automatically paste into the focused window.
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.app import main

if __name__ == "__main__":
    main()
