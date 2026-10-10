# ai_shortcuts.py
# Editing shortcuts. Whisper transcribes on this machine, then the text goes
# to OpenAI. Plain dictation and speaker transcription never call this.

import time

import pyperclip

REWRITE_GUIDE = """Rewrite the text below so it is clear, natural, and ready to send.

Keep the meaning and the facts. Do not add information that was not in the original.
If a style guide was provided with this request, follow that guide.
If the original wording is already good, change only what needs changing.
Output only the finished text. Do not explain the edits."""


def llm_config(config_manager) -> dict:
    raw = {}
    try:
        raw = dict(config_manager.get_postprocess_config().get("ollama") or {})
    except Exception:
        raw = {}
    model = str(raw.get("model") or "llama3.2").strip()
    try:
        timeout = float(raw.get("timeout") or 30)
    except (TypeError, ValueError):
        timeout = 30
    return {
        "enabled": bool(raw.get("enabled", False)),
        "endpoint": raw.get("endpoint") or "http://127.0.0.1:11434",
        "model": model,
        "timeout": timeout,
        "think": bool(raw.get("think", False)),
        "prompt": raw.get("prompt") or "{text}",
        "keep_alive": raw.get("keep_alive") or "5m",
        "num_predict": int(raw.get("num_predict") or 400),
        "num_ctx": int(raw.get("num_ctx") or 4096),
    }


def warmup_local_model(config_manager):
    # One tiny request at startup loads the weights. The first real rewrite
    # then does not wait on a cold start.
    from .text_postprocess import _ollama_polish

    cfg = llm_config(config_manager)
    cfg["num_predict"] = 1
    cfg["timeout"] = 120
    _ollama_polish("OK", cfg)


def rewrite_text(text: str, config_manager) -> str:
    from .openai_client import complete

    return complete(f"Text:\n{text}", config_manager, system=REWRITE_GUIDE) or ""


def answer_prompt(instruction: str, selection: str, config_manager) -> str:
    # Ctrl+Alt+F3. The reply guide is added in the API client. This message
    # is only the highlight and the spoken instruction for this request.
    from .openai_client import complete

    prompt = (
        f"Voice instruction:\n{(instruction or '').strip()}\n\n"
        f"Highlighted text:\n{selection}\n\n"
        "Follow the voice instruction. Output ONLY the finished text, "
        "with no preamble and no commentary."
    )
    return complete(prompt, config_manager) or ""


def answer_voice(speech: str, config_manager) -> str:
    # Ctrl+Alt+F8. The style guide is added by the API client. This message
    # is only what was just said.
    from .openai_client import complete

    prompt = (
        f"Voice instruction:\n{(speech or '').strip()}\n\n"
        "Follow the voice instruction. Output ONLY the finished text, "
        "with no preamble and no commentary."
    )
    return complete(prompt, config_manager) or ""


def wait_until_released(*names, timeout=0.8):
    # Ctrl+R is still physically held when the hotkey fires. Wait until those
    # keys are up so the following Ctrl+C is a real copy, not Ctrl+R+C.
    import ctypes
    user32 = ctypes.windll.user32
    codes = {
        "ctrl": (0xA2, 0xA3),
        "alt": (0xA4, 0xA5),
        "shift": (0xA0, 0xA1),
        "r": (0x52,),
        "p": (0x50,),
        "s": (0x53,),
    }
    deadline = time.time() + timeout
    while time.time() < deadline:
        held = False
        for name in names:
            for vk in codes.get(name, ()):
                if user32.GetAsyncKeyState(vk) < 0:
                    held = True
        if not held:
            return
        time.sleep(0.02)


# Put on the clipboard before Ctrl+C. If it is still there afterwards, nothing
# was copied — including when the highlight was already the same as the clipboard.
_SELECTION_MARKER = "\u2060wl-sel\u2060"


def _copy_keys():
    import ctypes
    from .platform import keyboard as kb

    user32 = ctypes.windll.user32
    # Drop Shift and Alt so the copy is Ctrl+C. Either one still held turns it
    # into a different shortcut (Ctrl+Shift+C or Ctrl+Alt+C).
    releases = []
    if user32.GetAsyncKeyState(0xA0) < 0 or user32.GetAsyncKeyState(0xA1) < 0:
        releases.extend([
            kb._make_vk_input(0xA0, kb.KEYEVENTF_KEYUP),
            kb._make_vk_input(0xA1, kb.KEYEVENTF_KEYUP),
        ])
    if user32.GetAsyncKeyState(0xA4) < 0 or user32.GetAsyncKeyState(0xA5) < 0:
        releases.extend([
            kb._make_vk_input(0xA4, kb.KEYEVENTF_KEYUP),
            kb._make_vk_input(0xA5, kb.KEYEVENTF_KEYUP),
        ])
    if releases:
        kb._send(releases)
    ctrl_held = user32.GetAsyncKeyState(0xA2) < 0 or user32.GetAsyncKeyState(0xA3) < 0
    if ctrl_held:
        kb.send_key("c")
    else:
        kb.send_hotkey("ctrl", "c")


def capture_selection():
    # Returns (selection, previous_clipboard). Selection is '' when nothing was
    # copied. Previous clipboard is restored only in that failure case.
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""
    try:
        pyperclip.copy(_SELECTION_MARKER)
        time.sleep(0.05)
        _copy_keys()
        time.sleep(0.18)
        selection = pyperclip.paste()
    except Exception:
        selection = ""
    if not selection or selection == _SELECTION_MARKER:
        try:
            pyperclip.copy(original)
        except Exception:
            pass
        return "", original
    return selection, original
