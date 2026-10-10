# key_swallow.py
# Stops a registered shortcut from also landing in the focused app. The hotkey
# library only watches keys, so Google Docs was replacing a highlight with the
# letter in the chord. This hook eats the key that completes one of our chords.
# Keys this app injects itself (Ctrl+C, Ctrl+V) are left alone.

import ctypes
import logging
import queue
import threading
from ctypes import wintypes

logger = logging.getLogger(__name__)

WH_KEYBOARD_LL = 13
LLKHF_UP = 0x80
LLKHF_INJECTED = 0x10
HC_ACTION = 0

# Either side counts. The low-level hook reports the specific key, not "ctrl".
_TOKEN_VKS = {
    "ctrl": (0xA2, 0xA3, 0x11),
    "control": (0xA2, 0xA3, 0x11),
    "alt": (0xA4, 0xA5, 0x12),
    "shift": (0xA0, 0xA1, 0x10),
    "win": (0x5B, 0x5C),
    "windows": (0x5B, 0x5C),
}

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_LRESULT = ctypes.c_ssize_t

class _KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]

_HOOKPROC = ctypes.WINFUNCTYPE(_LRESULT, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
_user32.CallNextHookEx.restype = _LRESULT
_user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
_user32.SetWindowsHookExW.restype = wintypes.HHOOK
_user32.SetWindowsHookExW.argtypes = [ctypes.c_int, _HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD]

# Modifier families. A chord does not fire while an extra one of these is held,
# so Ctrl+Win does not also run when Alt is down for Ctrl+Alt+Win.
_MODIFIER_GROUPS = (
    (0xA2, 0xA3, 0x11),
    (0xA4, 0xA5, 0x12),
    (0xA0, 0xA1, 0x10),
    (0x5B, 0x5C),
)

_lock = threading.Lock()
_bindings = []
_enabled = True
_down = set()
_swallowed = set()
_hook = None
_callback = None
_thread = None
_worker = None
_jobs = queue.Queue()


def _token_vks(token: str):
    token = token.strip().lower()
    if token in _TOKEN_VKS:
        return _TOKEN_VKS[token]
    if len(token) > 1 and token[0] == "f" and token[1:].isdigit():
        number = int(token[1:])
        if 1 <= number <= 24:
            return (0x6F + number,)
    if len(token) == 1 and token.isalpha():
        return (ord(token.upper()),)
    if len(token) == 1 and token.isdigit():
        return (ord(token),)
    return ()


def _parse_chord(hotkey: str):
    # A single key such as Ctrl or Esc is not swallowed. Those are also used
    # for normal typing and for stopping a recording.
    parts = [part.strip() for part in (hotkey or "").lower().split("+") if part.strip()]
    if len(parts) < 2:
        return None
    groups = []
    for part in parts:
        vks = _token_vks(part)
        if not vks:
            return None
        groups.append(vks)
    return groups


def _held(groups, down: set) -> bool:
    return all(any(key in down for key in group) for group in groups)


def _any_held(groups, down: set) -> bool:
    return any(any(key in down for key in group) for group in groups)


def _extra_modifier(groups, down: set) -> bool:
    # Alt held during Ctrl+Win is a different shortcut, not this one.
    used = set()
    for group in groups:
        used.update(group)
    for modifiers in _MODIFIER_GROUPS:
        if any(key in used for key in modifiers):
            continue
        if any(key in down for key in modifiers):
            return True
    return False


def _belongs_to_live_chord(vk: int) -> bool:
    for binding in _bindings:
        if not _held(binding["groups"], _down) or _extra_modifier(binding["groups"], _down):
            continue
        if any(vk in group for group in binding["groups"]):
            return True
    return False


def _enqueue(callback):
    if callback:
        _jobs.put(callback)


def _sync_bindings():
    # Press when the chord is fully down. Release only once every key is up,
    # matching the push-to-talk setting actuate_on_partial_release=False.
    actions = []
    for binding in _bindings:
        groups = binding["groups"]
        live = _held(groups, _down) and not _extra_modifier(groups, _down)
        if live and not binding["active"]:
            binding["active"] = True
            actions.append(binding["press"])
        elif binding["active"] and not _any_held(groups, _down):
            binding["active"] = False
            actions.append(binding["release"])
        elif binding["active"] and not live and binding["partial_release"]:
            binding["active"] = False
            actions.append(binding["release"])
    return actions


def _on_key(n_code, w_param, l_param):
    if n_code != HC_ACTION:
        return _user32.CallNextHookEx(_hook, n_code, w_param, l_param)
    event = ctypes.cast(l_param, ctypes.POINTER(_KBDLLHOOKSTRUCT)).contents
    # SendInput from this app (copy and paste) must still reach the target.
    if event.flags & LLKHF_INJECTED:
        return _user32.CallNextHookEx(_hook, n_code, w_param, l_param)
    vk = int(event.vkCode)
    is_up = bool(event.flags & LLKHF_UP)
    actions = []
    with _lock:
        if not _enabled:
            if is_up:
                _down.discard(vk)
                _swallowed.discard(vk)
            else:
                _down.add(vk)
            swallow = False
        elif is_up:
            _down.discard(vk)
            swallow = vk in _swallowed
            _swallowed.discard(vk)
            actions = _sync_bindings()
        else:
            _down.add(vk)
            # Swallow only the key that finishes a chord. The poller never sees
            # a swallowed key, so the press and release are fired from here.
            swallow = vk in _swallowed or _belongs_to_live_chord(vk)
            if swallow:
                _swallowed.add(vk)
            actions = _sync_bindings()
    for callback in actions:
        _enqueue(callback)
    if swallow:
        return 1
    return _user32.CallNextHookEx(_hook, n_code, w_param, l_param)


def _pump():
    # This hook swallowed ordinary keys and left Alt stuck down, so it
    # must never be installed again.
    return


def _run_jobs():
    while True:
        callback = _jobs.get()
        try:
            callback()
        except Exception:
            logger.exception("Shortcut callback failed")


def _ensure_hook():
    # The low-level hook froze normal typing, so it must not be installed.
    return


def update_bindings(bindings):
    # Multi-key chords are handled here. Single keys stay with the poller,
    # because swallowing Ctrl or Esc would break normal typing.
    parsed = []
    for binding in bindings:
        groups = _parse_chord(binding[0])
        if not groups:
            continue
        parsed.append({
            "groups": groups,
            "press": binding[1] if len(binding) > 1 else None,
            "release": binding[2] if len(binding) > 2 else None,
            "partial_release": bool(binding[3]) if len(binding) > 3 else False,
            "active": False,
        })
    with _lock:
        _bindings[:] = parsed
    _ensure_hook()


def update_chords(hotkeys):
    update_bindings([[hotkey, None, None, False] for hotkey in hotkeys])


def set_enabled(enabled: bool):
    # Pause turns swallowing off so those same keys work in other programs.
    releases = []
    with _lock:
        global _enabled
        _enabled = bool(enabled)
        if not _enabled:
            _swallowed.clear()
            for binding in _bindings:
                if binding["active"]:
                    binding["active"] = False
                    releases.append(binding["release"])
    for callback in releases:
        _enqueue(callback)
