import ctypes
from ctypes import wintypes
import logging
import sys
import threading
import time
from typing import Optional

import pyperclip

logger = logging.getLogger("WisprClone.Injector")

user32 = getattr(ctypes, "windll", None).user32 if hasattr(ctypes, "windll") else None

VK_CONTROL = 0x11
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_V = 0x56
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_MENU = 0x12   # Alt
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_SHIFT = 0x10  # Shift
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1

# Define Win32 SendInput structures for reliable modern injection on Windows 10/11
ULONG_PTR = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint32


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


def _make_key_input(vk: int, flags: int = 0) -> INPUT:
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    inp.union.ki.wScan = user32.MapVirtualKeyW(vk, 0) if user32 else 0
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = 0
    return inp


def _send_inputs(inputs: list[INPUT]) -> bool:
    if user32 is None or not inputs:
        return False
    try:
        arr = (INPUT * len(inputs))(*inputs)
        sent = user32.SendInput(len(inputs), ctypes.byref(arr), ctypes.sizeof(INPUT))
        return sent == len(inputs)
    except Exception as e:
        logger.debug(f"SendInput failed: {e}")
        return False


_clipboard_lock = threading.Lock()
_restore_generation = 0


def get_clipboard_text(retries: int = 5, retry_delay: float = 0.02) -> Optional[str]:
    """Retrieve current clipboard text safely with retry for transient Windows clipboard locks."""
    for attempt in range(retries):
        try:
            return pyperclip.paste()
        except Exception as e:
            if attempt == retries - 1:
                logger.debug(f"Error reading clipboard after {retries} attempts: {e}")
            else:
                time.sleep(retry_delay)
    return None


def set_clipboard_text(text: str, retries: int = 5, retry_delay: float = 0.02) -> bool:
    """Set clipboard text safely with retry for transient Windows clipboard locks."""
    for attempt in range(retries):
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            if attempt == retries - 1:
                logger.error(f"Error writing to clipboard after {retries} attempts: {e}")
            else:
                time.sleep(retry_delay)
    return False


def release_modifier_keys(wait_timeout_sec: float = 0.25) -> None:
    """Ensure modifier keys (Win, Alt, Shift) are released before simulating Ctrl+V.

    Prevents Win+V (Windows clipboard history) or Alt+V from firing accidentally.
    """
    if user32 is None:
        return

    modifiers = [VK_LWIN, VK_RWIN, VK_MENU, VK_LMENU, VK_RMENU, VK_SHIFT, VK_LSHIFT, VK_RSHIFT]

    # Wait briefly if the user is still physically releasing the Win/Alt/Shift key
    deadline = time.monotonic() + wait_timeout_sec
    while time.monotonic() < deadline:
        still_down = any((user32.GetAsyncKeyState(vk) & 0x8000) != 0 for vk in modifiers)
        if not still_down:
            break
        time.sleep(0.015)

    # Explicitly send key-up for any still-pressed modifier keys
    release_events = []
    for vk in modifiers:
        if (user32.GetAsyncKeyState(vk) & 0x8000) != 0:
            flags = KEYEVENTF_KEYUP | (KEYEVENTF_EXTENDEDKEY if vk in (VK_LWIN, VK_RWIN, VK_RMENU) else 0)
            release_events.append(_make_key_input(vk, flags))
            try:
                user32.keybd_event(vk, 0, flags, 0)
            except Exception:
                pass

    if release_events:
        _send_inputs(release_events)
        time.sleep(0.02)


def simulate_ctrl_v() -> None:
    """Simulate Ctrl+V keystroke using Win32 SendInput with fallback to keybd_event."""
    if user32 is None:
        return

    down_inputs = [
        _make_key_input(VK_CONTROL, 0),
        _make_key_input(VK_V, 0),
    ]
    up_inputs = [
        _make_key_input(VK_V, KEYEVENTF_KEYUP),
        _make_key_input(VK_CONTROL, KEYEVENTF_KEYUP),
    ]

    if _send_inputs(down_inputs):
        time.sleep(0.025)
        _send_inputs(up_inputs)
    else:
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.03)
        user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


def paste_text(text: str, restore_clipboard: bool = True, restore_delay_sec: float = 0.35) -> bool:
    """Inject text into the currently focused application via clipboard + simulated Ctrl+V.

    Preserves and restores the user's previous clipboard text safely even across rapid dictations.
    """
    global _restore_generation

    if not text:
        return True

    with _clipboard_lock:
        _restore_generation += 1
        current_gen = _restore_generation

        old_clipboard: Optional[str] = None
        if restore_clipboard:
            try:
                old_clipboard = get_clipboard_text()
            except Exception as e:
                logger.debug(f"Error saving previous clipboard: {e}")

        # Set new text to clipboard
        if not set_clipboard_text(text):
            logger.error("Could not set clipboard text for injection.")
            return False

        # Release any lingering Win/Alt/Shift keys from the hotkey combination
        release_modifier_keys()

        # Simulate Ctrl+V
        logger.info(f"Injecting text ({len(text)} chars) via simulated Ctrl+V...")
        simulate_ctrl_v()

    # Wait for the target application to process the paste message before restoring clipboard
    if restore_clipboard and old_clipboard is not None:
        def _restore(expected_gen: int, saved_text: str):
            time.sleep(restore_delay_sec)
            with _clipboard_lock:
                # Only restore if another dictation hasn't overwritten the clipboard in the meantime
                if _restore_generation == expected_gen:
                    try:
                        set_clipboard_text(saved_text)
                        logger.debug("Previous clipboard content restored.")
                    except Exception as e:
                        logger.debug(f"Error restoring clipboard: {e}")

        threading.Thread(
            target=_restore,
            args=(current_gen, old_clipboard),
            daemon=True,
            name="ClipboardRestorer",
        ).start()

    return True
