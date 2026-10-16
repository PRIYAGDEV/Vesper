"""Build script to compile Vesper into a standalone Windows .exe using PyInstaller and place a Desktop shortcut."""

import os
import subprocess
import sys
from pathlib import Path


def create_desktop_shortcut(target_exe: Path):
    """Create a Windows desktop shortcut pointing to Vesper.exe."""
    try:
        desktop_dir = Path(os.environ["USERPROFILE"]) / "Desktop"
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


def build():
    print("=" * 60)
    print(" Building Vesper Standalone Executable (.exe)")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Vesper",
        "--noconsole",
        "--onefile",
        "--clean",
        "--collect-data=faster_whisper",
        "--collect-binaries=ctranslate2",
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
        "--collect-submodules=pynput",
        "--collect-submodules=pyperclip",
        "--collect-submodules=keyboard",
        "--add-data=config.json;.",
        "main.py"
    ]

    print(f"Running PyInstaller for Vesper...")
    subprocess.check_call(cmd)

    dist_exe = Path("dist/Vesper.exe").resolve()
    if dist_exe.exists():
        print(f"\n[SUCCESS] Standalone Vesper.exe compiled successfully at:\n  {dist_exe}")
        create_desktop_shortcut(dist_exe)
    else:
        print("[ERROR] Build failed: Executable not found in dist/")


if __name__ == "__main__":
    build()
