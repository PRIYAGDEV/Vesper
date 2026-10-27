"""Build script to compile Vesper into a standalone Windows .exe using PyInstaller and place a Desktop shortcut."""

import hashlib
import os
import subprocess
import sys
from pathlib import Path


def create_desktop_shortcut(target_exe: Path):
    """Create a Windows desktop shortcut pointing to Vesper.exe."""
    if sys.platform != "win32" or os.environ.get("GITHUB_ACTIONS") == "true":
        return
    try:
        user_profile = os.environ.get("USERPROFILE")
        if not user_profile:
            return
        desktop_dir = Path(user_profile) / "Desktop"
        if not desktop_dir.exists():
            return

        # Remove old shortcut if exists
        old_shortcut = desktop_dir / "Wispr Flow.lnk"
        old_shortcut.unlink(missing_ok=True)

        shortcut_path = desktop_dir / "Vesper.lnk"
        vbs_script = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{str(shortcut_path)}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{str(target_exe)}"
oLink.WorkingDirectory = "{str(target_exe.parent)}"
oLink.Description = "Vesper - System-Wide Voice Dictation"
oLink.Save
"""
        vbs_file = Path("create_shortcut.vbs")
        vbs_file.write_text(vbs_script, encoding="utf-8")
        subprocess.run(["cscript", "//nologo", str(vbs_file)], check=True)
        vbs_file.unlink(missing_ok=True)
        print(f"[SUCCESS] Desktop shortcut created at: {shortcut_path}")
    except Exception as e:
        print(f"[WARNING] Could not create desktop shortcut automatically: {e}")


def update_checksum(target_exe: Path):
    """Calculate SHA-256 hash of Vesper.exe and write to checksums.txt."""
    try:
        sha256 = hashlib.sha256()
        with open(target_exe, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                sha256.update(chunk)
        digest = sha256.hexdigest().upper()
        checksum_line = f"{digest} *{target_exe.name}\n"
        Path("checksums.txt").write_text(checksum_line, encoding="utf-8")
        print(f"[SUCCESS] SHA-256 checksum updated in checksums.txt:\n  {checksum_line.strip()}")
    except Exception as e:
        print(f"[WARNING] Could not update checksums.txt: {e}")


def build():
    print("=" * 60)
    print(" Building Vesper Standalone Executable (.exe)")
    print("=" * 60)

    sep = ";" if sys.platform == "win32" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Vesper",
        "--noconsole",
        "--onefile",
        "--clean",
        "--collect-data=faster_whisper",
        "--collect-binaries=ctranslate2",
        "--collect-binaries=onnxruntime",
        "--collect-binaries=sounddevice",
        "--collect-data=_sounddevice_data",
        "--collect-all=PySide6",
        "--exclude-module=PySide6.QtWebEngineCore",
        "--exclude-module=PySide6.QtWebEngineWidgets",
        "--exclude-module=PySide6.QtWebEngineQuick",
        "--exclude-module=PySide6.QtQml",
        "--exclude-module=PySide6.QtQuick",
        "--exclude-module=PySide6.QtQuickWidgets",
        "--exclude-module=PySide6.Qt3DCore",
        "--exclude-module=PySide6.Qt3DRender",
        "--exclude-module=PySide6.QtDesigner",
        "--exclude-module=PySide6.QtPdf",
        "--exclude-module=PySide6.QtPdfWidgets",
        "--exclude-module=PySide6.QtMultimedia",
        "--exclude-module=PySide6.QtMultimediaWidgets",
        "--collect-submodules=scipy.signal",
        "--collect-submodules=sounddevice",
        "--collect-submodules=onnxruntime",
        "--collect-submodules=pynput",
        "--collect-submodules=pyperclip",
        "--collect-submodules=keyboard",
        f"--add-data=config.json{sep}.",
        "main.py",
    ]

    print("Running PyInstaller for Vesper...")
    subprocess.check_call(cmd)

    exe_name = "Vesper.exe" if sys.platform == "win32" else "Vesper"
    dist_exe = Path("dist") / exe_name
    if dist_exe.exists():
        resolved = dist_exe.resolve()
        print(f"\n[SUCCESS] Standalone executable compiled successfully at:\n  {resolved}")
        update_checksum(resolved)
        create_desktop_shortcut(resolved)
    else:
        print(f"[ERROR] Build failed: Executable not found at {dist_exe}")
        sys.exit(1)


if __name__ == "__main__":
    build()
