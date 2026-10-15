import ctypes
import logging
import threading
import time
from typing import Optional

import pyperclip

logger = logging.getLogger("WisprClone.Injector")

user32 = ctypes.windll.user32

VK_CONTROL = 0x11
VK_V = 0x56
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_MENU = 0x12   # Alt
VK_SHIFT = 0x10  # Shift
KEYEVENTF_KEYUP = 0x0002


def get_clipboard_text() -> Optional[str]:
    """Retrieve current clipboard text safely."""
    try:
        return pyperclip.paste()
    except Exception as e:
        logger.debug(f"Error reading clipboard: {e}")
        return None


def set_clipboard_text(text: str) -> bool:
    """Set clipboard text safely."""
    try:
        pyperclip.copy(text)
        return True
    except Exception as e:
        logger.error(f"Error writing to clipboard: {e}")
        return False


def release_modifier_keys() -> None:
    """Ensure modifier keys (Win, Alt, Shift) are released before simulating Ctrl+V.

    Prevents Win+V (Windows clipboard history) or Alt+V from firing accidentally.
    """
    modifiers = [VK_LWIN, VK_RWIN, VK_MENU, VK_SHIFT]
    for vk in modifiers:
        if (user32.GetAsyncKeyState(vk) & 0x8000) != 0:
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.02)


def paste_text(text: str, restore_clipboard: bool = True, restore_delay_sec: float = 0.25) -> bool:
    """Inject text into the currently focused application via clipboard + simulated Ctrl+V.

    Preserves and restores the user's previous clipboard text.
    """
    if not text:
        return True

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

    # Release any lingering Win/Alt keys from the hotkey combination
    release_modifier_keys()

    # Simulate Ctrl+V
    logger.info(f"Injecting text ({len(text)} chars) via simulated Ctrl+V...")
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    user32.keybd_event(VK_V, 0, 0, 0)
    time.sleep(0.03)
    user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    # Wait for the target application to process the paste message before restoring clipboard
    if restore_clipboard and old_clipboard is not None:
        def _restore():
            time.sleep(restore_delay_sec)
            try:
                set_clipboard_text(old_clipboard)
                logger.debug("Previous clipboard content restored.")
            except Exception as e:
                logger.debug(f"Error restoring clipboard: {e}")

        threading.Thread(target=_restore, daemon=True, name="ClipboardRestorer").start()

    return True
