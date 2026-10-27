import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.hotkey import PushToTalkHotkeyListener, VK_MAP


def test_hotkey_parsing():
    listener = PushToTalkHotkeyListener("ctrl+win")
    assert len(listener._target_key_groups) == 2
    # First group is ctrl (0x11, 0xA2, 0xA3)
    assert 0x11 in listener._target_key_groups[0]
    # Second group is win (0x5B, 0x5C)
    assert 0x5B in listener._target_key_groups[1]

    listener.set_hotkey("alt+space")
    assert len(listener._target_key_groups) == 2
    assert 0x12 in listener._target_key_groups[0]
    assert 0x20 in listener._target_key_groups[1]

    # Fallback when invalid key string is passed
    listener.set_hotkey("invalid_unknown_key")
    assert len(listener._target_key_groups) == 2
    assert 0x11 in listener._target_key_groups[0]
    print("[PASS] Hotkey parsing test passed.")


def test_hotkey_mock_state():
    events = []

    def on_start():
        events.append("start")

    def on_stop():
        events.append("stop")

    listener = PushToTalkHotkeyListener("ctrl+win", on_start=on_start, on_stop=on_stop, poll_interval_sec=0.01)

    # Mock _check_hotkey_pressed
    state = False
    listener._check_hotkey_pressed = lambda: state

    listener.start()
    time.sleep(0.05)
    assert events == []

    # Simulate press
    state = True
    time.sleep(0.05)
    assert events == ["start"]

    # Simulate release
    state = False
    time.sleep(0.05)
    assert events == ["start", "stop"]

    # Simulate pressing and updating hotkey while active -> should fire stop automatically
    state = True
    time.sleep(0.05)
    assert events == ["start", "stop", "start"]
    listener.set_hotkey("alt+space")
    assert events == ["start", "stop", "start", "stop"]

    listener.stop()
    print("[PASS] Mock push-to-talk press, release, and live hotkey change test passed.")


if __name__ == "__main__":
    test_hotkey_parsing()
    test_hotkey_mock_state()
