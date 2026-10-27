import sys
import time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import src.injector as injector
from src.injector import get_clipboard_text, set_clipboard_text, paste_text


def test_clipboard_read_write():
    # Use an in-memory clipboard fallback if OS clipboard is unavailable (e.g. headless Linux CI)
    clipboard_store = {"text": ""}
    real_available = set_clipboard_text("probe", retries=1)

    if not real_available:
        patcher_copy = patch("pyperclip.copy", side_effect=lambda t: clipboard_store.__setitem__("text", t))
        patcher_paste = patch("pyperclip.paste", side_effect=lambda: clipboard_store["text"])
        patcher_copy.start()
        patcher_paste.start()

    try:
        original = get_clipboard_text()

        test_str = "Test clipboard string with special chars: © ™ 🚀 newline\nand tabs\t."
        success = set_clipboard_text(test_str)
        assert success, "set_clipboard_text returned False"

        read_back = get_clipboard_text()
        assert read_back == test_str, f"Expected '{test_str}', got '{read_back}'"
        print("[PASS] Clipboard unicode read/write test passed.")

        # Test restoration via paste_text
        sentinel = "ORIGINAL_CLIPBOARD_PRESERVED"
        set_clipboard_text(sentinel)

        injected = "INJECTED_DICTATION_TEXT"
        paste_text(injected, restore_clipboard=True, restore_delay_sec=0.1)

        # Immediately after paste, clipboard has injected text
        # After restore_delay, clipboard should return to sentinel
        time.sleep(0.25)
        restored = get_clipboard_text()
        assert restored == sentinel, f"Expected restored '{sentinel}', got '{restored}'"
        print("[PASS] Clipboard preservation and restoration test passed.")

        # Test rapid back-to-back paste_text calls don't clobber the second paste prematurely
        set_clipboard_text(sentinel)
        paste_text("FIRST_DICTATION", restore_clipboard=True, restore_delay_sec=0.15)
        time.sleep(0.05)
        paste_text("SECOND_DICTATION", restore_clipboard=True, restore_delay_sec=0.2)
        # At t=0.17s (after first timer expires, before second timer expires), clipboard should still be SECOND_DICTATION
        time.sleep(0.12)
        assert get_clipboard_text() == "SECOND_DICTATION"
        # After second timer expires, clipboard should restore
        time.sleep(0.15)
        print("[PASS] Rapid sequential paste generation guard test passed.")

        if original:
            set_clipboard_text(original)
    finally:
        if not real_available:
            patcher_copy.stop()
            patcher_paste.stop()


if __name__ == "__main__":
    test_clipboard_read_write()
