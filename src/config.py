import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": "ctrl+win",
    "model_size": "small",
    "device_index": None,
    "language": "en",
    "task": "transcribe",
    "style": "casual",
    "cleanup_filler": True,
    "spoken_commands": True,
    "audio_feedback": True,
    "vad_filter": True,
    "history_limit": 20
}

def get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).parent / "config.json"
        return exe_path
    if Path("config.json").exists():
        return Path("config.json")
    return Path(__file__).resolve().parent.parent / "config.json"

CONFIG_FILE = get_config_path()

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file or return defaults."""
    path = config_path or get_config_path()
    config = DEFAULT_CONFIG.copy()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                config.update(saved)
        except Exception as e:
            print(f"[Config] Error loading {path}: {e}, using defaults.")
    else:
        save_config(config, path)
    return config

def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """Save configuration to JSON file."""
    path = config_path or get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"[Config] Error saving {path}: {e}")
