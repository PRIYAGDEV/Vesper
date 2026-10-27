import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("WisprClone.Config")

DEFAULT_CONFIG: Dict[str, Any] = {
    "hotkey": "ctrl+win",
    "model_size": "small",
    "device_index": None,
    "language": "hi",
    "task": "translate",
    "style": "casual",
    "cleanup_filler": True,
    "spoken_commands": True,
    "audio_feedback": True,
    "vad_filter": True,
    "history_limit": 20,
}


def get_app_data_dir() -> Path:
    """Return a writable directory for user config, history, logs, and downloaded models."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if os.access(exe_dir, os.W_OK):
            return exe_dir
    else:
        repo_dir = Path(__file__).resolve().parent.parent
        if os.access(repo_dir, os.W_OK):
            return repo_dir

    if sys.platform == "win32":
        appdata = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if appdata:
            fallback = Path(appdata) / "Vesper"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

    fallback = Path.home() / ".vesper"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def get_config_path() -> Path:
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve().parent / "config.json"
        if exe_path.exists() and os.access(exe_path.parent, os.W_OK):
            return exe_path
        app_path = get_app_data_dir() / "config.json"
        if not app_path.exists() and exe_path.exists():
            try:
                app_path.write_text(exe_path.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass
        return app_path
    if Path("config.json").exists() and os.access(Path("."), os.W_OK):
        return Path("config.json")
    return get_app_data_dir() / "config.json"


CONFIG_FILE = get_config_path()


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from JSON file or return defaults."""
    path = config_path or get_config_path()
    config = DEFAULT_CONFIG.copy()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    config.update(saved)
        except Exception as e:
            logger.warning(f"Error loading {path}: {e}, using defaults.")
    else:
        save_config(config, path)
    return config


def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """Save configuration to JSON file atomically."""
    path = config_path or get_config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        tmp_path.replace(path)
    except Exception as e:
        logger.warning(f"Error saving {path}: {e}")
