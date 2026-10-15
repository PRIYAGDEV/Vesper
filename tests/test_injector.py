import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.injector import get_clipboard_text, set_clipboard_text, paste_text


def test_clipboard_read_write():
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
    time.sleep(0.3)
    restored = get_clipboard_text()
    assert restored == sentinel, f"Expected restored '{sentinel}', got '{restored}'"
    print("[PASS] Clipboard preservation and restoration test passed.")

    # Cleanup
    if original:
        set_clipboard_text(original)


if __name__ == "__main__":
    test_clipboard_read_write()
