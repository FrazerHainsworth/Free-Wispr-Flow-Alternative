# edit_learning.py
# After a dictation is pasted, watch the focused text field for a few seconds.
# If you retype a word, save that as a correction so the next dictation uses it.
# The diff itself is pure; only the Windows watcher touches UI Automation.

import logging
import re
import threading
import time
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

_WATCH_SECONDS = 20
_SETTLE_SECONDS = 1.5
_POLL_SECONDS = 0.4

# Function words. Swapping one of these for another is usually a rewrite of
# the sentence, not a misheard name, so it is not worth remembering.
_STOPWORDS = frozenset(
    "a an the to of and or in on for is it that this these those i you we they "
    "be as at by my me do if so but not just them there their then than what "
    "when where who how have has had was were are been from with your our his "
    "her she he its about into over some any all here now too also very really "
    "because after before".split()
)

_lock = threading.Lock()
_generation = 0


def _words(text: str) -> list:
    return re.findall(r"\S+", (text or "").replace("\u00a0", " "))


def _fold(words: list) -> list:
    return [word.casefold() for word in words]


def _contains_exact(field_words: list, original_words: list) -> bool:
    width = len(original_words)
    if width == 0 or len(field_words) < width:
        return False
    for start in range(len(field_words) - width + 1):
        if field_words[start:start + width] == original_words:
            return True
    return False


def _letters(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)


def _acceptable(heard: list, typed: list) -> bool:
    # A hunk is a mishearing we can replay later: a few words, not a rewrite,
    # and not a punctuation-only or "undo the capital" tweak.
    if not heard or not typed or len(heard) > 4 or len(typed) > 4:
        return False
    raw_heard = " ".join(heard)
    raw_typed = " ".join(typed)
    if raw_heard == raw_typed:
        return False
    heard_letters = _letters(raw_heard)
    typed_letters = _letters(raw_typed)
    if len(re.sub(r"\s", "", heard_letters)) < 2 or len(re.sub(r"\s", "", typed_letters)) < 1:
        return False
    if heard_letters.casefold() == typed_letters.casefold():
        if heard_letters == typed_letters:
            return False
        if (heard_letters[:1].isupper() and typed_letters[:1].islower()
                and heard_letters[1:] == typed_letters[1:]):
            return False
    heard_tokens = {word.casefold().strip(".,!?;:\"'") for word in heard}
    typed_tokens = {word.casefold().strip(".,!?;:\"'") for word in typed}
    # "these" changed to "MAKE.com" is an edit of the sentence, not a spelling
    # the app should replay on every future dictation.
    if heard_tokens and heard_tokens <= _STOPWORDS:
        return False
    return True


def _hunks(original_words: list, edited_words: list) -> list:
    matcher = SequenceMatcher(None, _fold(original_words), _fold(edited_words))
    pairs = []
    equal_words = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            equal_words += i2 - i1
            continue
        if tag != "replace":
            continue
        heard = original_words[i1:i2]
        typed = edited_words[j1:j2]
        if _acceptable(heard, typed):
            pairs.append((" ".join(heard), " ".join(typed)))
    # No shared words and a long utterance means they replaced the sentence.
    if equal_words == 0 and (len(original_words) > 4 or len(edited_words) > 4):
        return []
    if len(original_words) > 4 and equal_words < len(original_words) * 0.5:
        return []
    if len(pairs) > 2:
        return []
    return pairs


def _best_anchored_window(original_words: list, field_words: list):
    # Inside a long document, only trust a span that still shares almost every
    # word with what we pasted. A one-word dictation has no anchor, so skip it.
    count = len(original_words)
    if count < 2:
        return None
    if len(field_words) > 800:
        field_words = field_words[-800:]
    need = count - 1
    best = None
    best_equal = -1
    best_slack = 99
    for width in (count - 1, count, count + 1):
        if width < 1 or width > len(field_words):
            continue
        for start in range(len(field_words) - width + 1):
            window = field_words[start:start + width]
            equal, replaces = _alignment_counts(original_words, window)
            if replaces < 1 or equal < need:
                continue
            slack = abs(width - count)
            if equal > best_equal or (equal == best_equal and slack < best_slack):
                best = window
                best_equal = equal
                best_slack = slack
    return best


def _alignment_counts(original_words: list, window: list) -> tuple:
    matcher = SequenceMatcher(None, _fold(original_words), _fold(window))
    equal = 0
    replaces = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            equal += i2 - i1
        elif tag == "replace":
            replaces += 1
    return equal, replaces


# Heard text versus the field after the user stopped typing.
# Returns (misheard, typed) pairs worth saving. Empty when nothing usable changed.
def extract_corrections(original: str, field: str) -> list:
    original_words = _words(original)
    field_words = _words(field)
    if not original_words or not field_words:
        return []
    if _contains_exact(field_words, original_words):
        return []
    if len(field_words) <= len(original_words) + 8:
        window = field_words
    else:
        window = _best_anchored_window(original_words, field_words)
        if window is None:
            return []
    return _hunks(original_words, window)


def _worth_hotword(text: str) -> bool:
    # Hotwords bias the model. Only unusual spellings belong there; ordinary
    # words are handled by the replacement list alone.
    words = text.split()
    if not 1 <= len(words) <= 3:
        return False
    return any(char.isupper() or char.isdigit() for char in text)


def _bias_model(engine, word: str):
    if engine is None:
        return
    current = getattr(engine, "hotwords", None)
    if isinstance(current, list):
        if word not in current:
            current.append(word)
        return
    parts = [part.strip() for part in (current or "").split(",") if part.strip()]
    if word not in parts:
        parts.append(word)
        engine.hotwords = ", ".join(parts)


def _remember(pairs: list, engine, notify) -> None:
    from .corrections import add_replacement
    from .dictionary import add_word

    saved = []
    for heard, typed in pairs:
        if not add_replacement(heard, typed):
            continue
        saved.append((heard, typed))
        if _worth_hotword(typed):
            add_word(typed)
            _bias_model(engine, typed)
        logger.info(f"Remembered correction {heard!r} -> {typed!r}")
    if not saved or notify is None:
        return
    parts = [f'"{heard}" as "{typed}"' for heard, typed in saved]
    if len(parts) == 1:
        notice = f"Learned {parts[0]}"
        tail = "Remove it from Learned corrections if that is wrong."
    else:
        notice = "Learned " + " and ".join(parts)
        tail = "Remove them from Learned corrections if that is wrong."
    notify(f"{notice}. {tail}")


def _cancelled(generation: int) -> bool:
    return generation != _generation


def _watch(original: str, notify, engine, generation: int):
    from .platform import IS_WINDOWS
    if not IS_WINDOWS:
        return
    from .platform.windows.focused_text import FocusedTextReader

    reader = FocusedTextReader()
    deadline = time.monotonic() + _WATCH_SECONDS
    seen_original = False
    last = None
    stable_since = None
    judged = None
    while time.monotonic() < deadline and not _cancelled(generation):
        field = reader.read()
        now = time.monotonic()
        if field and _contains_exact(_words(field), _words(original)):
            seen_original = True
            last = field
            stable_since = now
            judged = None
        elif seen_original and field and field != last:
            last = field
            stable_since = now
        elif (seen_original and field and field == last and stable_since
              and field != judged and now - stable_since >= _SETTLE_SECONDS):
            # Wait until typing pauses, then learn. Keep watching if the edit
            # was only punctuation or extra words, in case a real fix follows.
            judged = field
            pairs = extract_corrections(original, field)
            if pairs and not _cancelled(generation):
                try:
                    _remember(pairs, engine, notify)
                except Exception as e:
                    logger.warning(f"Could not save a correction: {e}")
                return
        time.sleep(_POLL_SECONDS)


# Start a background watch for this paste. A newer dictation cancels the previous
# watch so a later field is not learned against the older text.
def watch_for_edit(original: str, notify=None, engine=None) -> None:
    global _generation
    if not original or not original.strip():
        return
    with _lock:
        _generation += 1
        generation = _generation
    threading.Thread(
        target=_watch,
        args=(original, notify, engine, generation),
        daemon=True,
        name="edit-learning",
    ).start()
