import argparse
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.injector import paste_text, get_clipboard_text, set_clipboard_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("WisprClone.Step3")


def main():
    parser = argparse.ArgumentParser(description="Step 3: Test text insertion into focused app")
    parser.add_argument(
        "--text",
        default="Hello! This text was inserted at your cursor by Wispr Flow clone.",
        help="Text to paste into focused app"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=3,
        help="Seconds delay before pasting, giving you time to focus another window"
    )
    args = parser.parse_args()

    print("=" * 65)
    print(" Wispr Flow Clone - Step 3: Text Paste Injection")
    print("=" * 65)
    print(f"Target text to insert:\n  \"{args.text}\"\n")

    current_clip = get_clipboard_text() or "<empty>"
    print(f"[CURRENT CLIPBOARD]: \"{current_clip[:40]}...\" (will be preserved)")

    print(f"\nFocus your target application (e.g. Notepad, Chrome, VS Code) now!")
    for sec in range(args.delay, 0, -1):
        print(f"Pasting in {sec} second(s)...")
        time.sleep(1.0)

    print(">>> SIMULATING Ctrl+V NOW...")
    success = paste_text(args.text, restore_clipboard=True, restore_delay_sec=0.3)

    if success:
        print("[SUCCESS] Simulated Ctrl+V completed.")
    else:
        print("[ERROR] Failed to inject text.")

    time.sleep(0.5)
    restored_clip = get_clipboard_text() or "<empty>"
    print(f"[RESTORED CLIPBOARD]: \"{restored_clip[:40]}...\"")
    print("\nCheck your focused application window to verify the text appeared at your cursor!")


if __name__ == "__main__":
    main()
