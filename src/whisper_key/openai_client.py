# openai_client.py
# One chat call for the editing shortcuts. Whisper still transcribes on this
# machine. A rewrite uses the user's own API key and, if they wrote one, their
# own style guide. Nothing personal is shipped with the app.

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_MASTER_CONTEXT = ""
_request_lock = threading.Lock()
_request_generation = 0
_active_response = None


_GENERIC_GUIDE = (
    "Rewrite the user's text so it is clear and natural. "
    "Keep their meaning. Do not add facts they did not give you. "
    "Output only the finished text."
)


def master_context(config_manager=None) -> str:
    # The style guide is whatever this person wrote for themselves. Check the
    # settings field first, then a local file that is never part of the repo.
    inline = ""
    if config_manager is not None:
        try:
            inline = str((config_manager.config.get("openai") or {}).get("context") or "").strip()
        except Exception:
            inline = ""
    if inline:
        return inline
    try:
        from .utils import get_user_app_data_path
        path = Path(get_user_app_data_path()) / "rewrite_context.txt"
        lines = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip().startswith("#"):
                lines.append(line)
        guide = "\n".join(lines).strip()
        if guide:
            return guide
    except OSError:
        pass
    return _GENERIC_GUIDE


def cancel_requests():
    # Esc. Closing the socket unblocks a rewrite that is sitting on the network
    # so the corner card can go away without waiting out the timeout.
    global _request_generation, _active_response
    with _request_lock:
        _request_generation += 1
        response = _active_response
        _active_response = None
    if response is not None:
        try:
            response.close()
        except Exception:
            pass


def complete(user_text: str, config_manager, system: str = "") -> str:
    # The user's style guide is the system context. A shortcut may add a
    # second system note. The changing part is `user_text`.
    cfg = {}
    try:
        cfg = dict(config_manager.config.get("openai") or {})
    except Exception:
        cfg = {}
    api_key = str(cfg.get("api_key") or "").strip()
    if not api_key:
        logger.warning("OpenAI edit skipped: no API key in user settings")
        return ""
    model = str(cfg.get("model") or "gpt-4.1-mini").strip()
    messages = []
    messages.append({"role": "system", "content": master_context(config_manager)})
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user_text})
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_completion_tokens": 800,
    }
    started = time.time()
    with _request_lock:
        token = _request_generation
    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        response = urllib.request.urlopen(req, timeout=60)
        with _request_lock:
            if token != _request_generation:
                response.close()
                return ""
            global _active_response
            _active_response = response
        try:
            raw = response.read()
        finally:
            with _request_lock:
                if _active_response is response:
                    _active_response = None
            try:
                response.close()
            except Exception:
                pass
        with _request_lock:
            if token != _request_generation:
                return ""
        data = json.loads(raw)
        text = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        logger.info(f"OpenAI {model} finished in {time.time() - started:.1f}s ({len(text)} chars)")
        return text
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:300]
        except Exception:
            pass
        logger.warning(f"OpenAI request failed ({e.code}): {detail}")
    except (urllib.error.URLError, OSError, ValueError) as e:
        logger.warning(f"OpenAI request failed: {e}")
    return ""
