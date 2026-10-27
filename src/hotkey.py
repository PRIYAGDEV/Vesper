import ctypes
import logging
import sys
import threading
import time
from typing import Callable, Dict, List, Optional, Set

logger = logging.getLogger("WisprClone.Hotkey")

# Windows Virtual Key Codes
VK_MAP: Dict[str, List[int]] = {
    "ctrl": [0x11, 0xA2, 0xA3],      # VK_CONTROL, VK_LCONTROL, VK_RCONTROL
    "control": [0x11, 0xA2, 0xA3],
    "win": [0x5B, 0x5C],             # VK_LWIN, VK_RWIN
    "windows": [0x5B, 0x5C],
    "super": [0x5B, 0x5C],
    "cmd": [0x5B, 0x5C],
    "alt": [0x12, 0xA4, 0xA5],       # VK_MENU, VK_LMENU, VK_RMENU
    "shift": [0x10, 0xA0, 0xA1],     # VK_SHIFT, VK_LSHIFT, VK_RSHIFT
    "space": [0x20],                 # VK_SPACE
    "tab": [0x09],
    "enter": [0x0D],
    "return": [0x0D],
    "esc": [0x1B],
    "escape": [0x1B],
    "capslock": [0x14],
    "caps": [0x14],
    "backtick": [0xC0],
    "grave": [0xC0],
    "`": [0xC0],
}

# Add F1-F24
for i in range(1, 25):
    VK_MAP[f"f{i}"] = [0x6F + i]

# Add A-Z
for c in range(ord("a"), ord("z") + 1):
    VK_MAP[chr(c)] = [ord(chr(c).upper())]

# Add 0-9
for d in range(10):
    VK_MAP[str(d)] = [0x30 + d]


class PushToTalkHotkeyListener:
    """Robust global hotkey listener for Windows using low-level async state polling.

    Works across all focused applications (VS Code, Chrome, Office, games, Admin apps)
    without hook-latency or permission dropouts.
    """

    def __init__(
        self,
        hotkey_str: str = "ctrl+win",
        on_start: Optional[Callable[[], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        poll_interval_sec: float = 0.020,  # 20ms = 50 checks per second (~0.0% CPU)
    ):
        self.hotkey_str = hotkey_str
        self.on_start = on_start
        self.on_stop = on_stop
        self.poll_interval = poll_interval_sec

        self._target_key_groups: List[List[int]] = []
        self._target_key_names: Set[str] = set()
        self._set_hotkey_internal(hotkey_str)

        self._is_active = False
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Windows User32 function (guarded for cross-platform CI / non-Windows environments)
        self._user32 = getattr(ctypes, "windll", None).user32 if hasattr(ctypes, "windll") else None
        if self._user32 is not None:
            try:
                self._user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
                self._user32.GetAsyncKeyState.restype = ctypes.c_short
            except Exception:
                pass

    def _set_hotkey_internal(self, hotkey_str: str) -> None:
        parts = [p.strip().lower() for p in hotkey_str.split("+") if p.strip()]
        self._target_key_names = set(parts)
        self._target_key_groups = []

        for p in parts:
            if p in VK_MAP:
                self._target_key_groups.append(VK_MAP[p])
            elif len(p) == 1:
                vk = ord(p.upper())
                self._target_key_groups.append([vk])
            else:
                logger.warning(f"Unknown key in hotkey: '{p}'")

        # Fallback to ctrl+win if user input resulted in no valid keys
        if not self._target_key_groups and parts:
            logger.warning(f"No valid keys parsed from '{hotkey_str}', falling back to 'ctrl+win'.")
            self._target_key_names = {"ctrl", "win"}
            self._target_key_groups = [VK_MAP["ctrl"], VK_MAP["win"]]

    def set_hotkey(self, hotkey_str: str) -> None:
        """Update hotkey string dynamically."""
        should_stop = False
        with self._lock:
            if self._is_active:
                self._is_active = False
                should_stop = True
            self.hotkey_str = hotkey_str
            self._set_hotkey_internal(hotkey_str)
            logger.info(f"Hotkey updated to: '{hotkey_str}' (VK groups: {self._target_key_groups})")

        if should_stop and self.on_stop:
            try:
                self.on_stop()
            except Exception as e:
                logger.error(f"Error calling on_stop during hotkey update: {e}")

    def _is_group_pressed(self, vk_list: List[int]) -> bool:
        """Return True if any VK in the group (e.g. LCTRL or RCTRL) is pressed."""
        if self._user32 is None:
            return False
        for vk in vk_list:
            if (self._user32.GetAsyncKeyState(vk) & 0x8000) != 0:
                return True
        return False

    def _check_hotkey_pressed(self) -> bool:
        """Return True if all keys in the combination are currently pressed."""
        if not self._target_key_groups:
            return False
        for group in self._target_key_groups:
            if not self._is_group_pressed(group):
                return False
        return True

    def _suppress_start_menu(self) -> None:
        """Send a benign dummy key event while Win+modifier is held so Windows does not pop open the Start Menu on release."""
        if self._user32 is None:
            return
        if "win" in self._target_key_names or "cmd" in self._target_key_names or "windows" in self._target_key_names:
            try:
                # 0xFF is an unassigned virtual key code; tapping it masks the bare Win-key tap detection in Windows shell
                self._user32.keybd_event(0xFF, 0, 0, 0)
                self._user32.keybd_event(0xFF, 0, 0x0002, 0)
            except Exception:
                pass

    def _poll_loop(self) -> None:
        logger.info(f"Push-to-talk polling loop started for '{self.hotkey_str}'")
        while self._running:
            try:
                pressed = self._check_hotkey_pressed()
                trigger_start = False
                trigger_stop = False

                with self._lock:
                    if pressed and not self._is_active:
                        self._is_active = True
                        trigger_start = True
                        logger.debug(f"Hotkey [{self.hotkey_str}] pressed -> START")
                    elif not pressed and self._is_active:
                        self._is_active = False
                        trigger_stop = True
                        logger.debug(f"Hotkey [{self.hotkey_str}] released -> STOP")

                # Execute callbacks synchronously on the poller thread (which simply emits Qt signals)
                # to guarantee strict ordering of START before STOP and prevent race conditions.
                if trigger_start:
                    self._suppress_start_menu()
                    if self.on_start:
                        self.on_start()
                elif trigger_stop:
                    if self.on_stop:
                        self.on_stop()

                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Error in hotkey poll loop: {e}")
                time.sleep(self.poll_interval)

    def start(self) -> None:
        """Start listening for hotkey."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True, name="HotkeyPoller")
        self._thread.start()
        logger.info(f"Hotkey listener started (target: {self.hotkey_str}).")

    def stop(self) -> None:
        """Stop listening for hotkey."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._is_active = False
        logger.info("Hotkey listener stopped.")
