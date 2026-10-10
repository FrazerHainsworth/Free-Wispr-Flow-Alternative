# emoji_speech.py
# Spoken emoji names become the character. "smiley face emoji" is the smiley,
# and the same "<name> emoji" pattern covers the standard emoji set. The word
# "emoji" is required so ordinary words like "fire" or "heart" stay words.

import re
import unicodedata

# How people actually say them. Official Unicode names are added on top, and
# these win when both exist ("smiley face" is not the Unicode name of 😊).
_ALIASES = {
    "smiley face": "😊",
    "smiley": "😊",
    "smiling face": "😊",
    "smile": "🙂",
    "slight smile": "🙂",
    "grin": "😀",
    "grinning": "😀",
    "laughing": "😂",
    "laugh": "😂",
    "lol": "😂",
    "joy": "😂",
    "tears of joy": "😂",
    "crying laughing": "😂",
    "rofl": "🤣",
    "wink": "😉",
    "heart eyes": "😍",
    "kiss": "😘",
    "kissing": "😘",
    "sad": "😢",
    "cry": "😢",
    "crying": "😢",
    "sob": "😭",
    "loudly crying": "😭",
    "angry": "😠",
    "mad": "😠",
    "rage": "😡",
    "thinking": "🤔",
    "think": "🤔",
    "sunglasses": "😎",
    "cool": "😎",
    "smirk": "😏",
    "eye roll": "🙄",
    "rolling eyes": "🙄",
    "shrug": "🤷",
    "facepalm": "🤦",
    "face palm": "🤦",
    "mind blown": "🤯",
    "exploding head": "🤯",
    "pleading": "🥺",
    "party face": "🥳",
    "sleeping": "😴",
    "sleep": "😴",
    "thumbs up": "👍",
    "thumb up": "👍",
    "thumbs down": "👎",
    "thumb down": "👎",
    "clap": "👏",
    "clapping": "👏",
    "pray": "🙏",
    "thanks": "🙏",
    "thank you": "🙏",
    "folded hands": "🙏",
    "wave": "👋",
    "waving": "👋",
    "raised hands": "🙌",
    "ok": "👌",
    "okay": "👌",
    "ok hand": "👌",
    "peace": "✌️",
    "victory": "✌️",
    "crossed fingers": "🤞",
    "fingers crossed": "🤞",
    "muscle": "💪",
    "flex": "💪",
    "point right": "👉",
    "point left": "👈",
    "point up": "👆",
    "point down": "👇",
    "right pointing thumb": "👉",
    "right pointing hand": "👉",
    "thumb pointing right": "👉",
    "hand pointing right": "👉",
    "pointing right thumb": "👉",
    "pointing thumb right": "👉",
    "right thumb": "👉",
    "rightwards thumb": "👉",
    "point to the right": "👉",
    "pointing to the right": "👉",
    "left pointing thumb": "👈",
    "left pointing hand": "👈",
    "thumb pointing left": "👈",
    "hand pointing left": "👈",
    "pointing left thumb": "👈",
    "left thumb": "👈",
    "point to the left": "👈",
    "pointing to the left": "👈",
    "up pointing thumb": "👆",
    "thumb pointing up": "👆",
    "pointing up thumb": "👆",
    "down pointing thumb": "👇",
    "thumb pointing down": "👇",
    "pointing down thumb": "👇",
    "fire": "🔥",
    "flame": "🔥",
    "heart": "❤️",
    "red heart": "❤️",
    "love": "❤️",
    "broken heart": "💔",
    "star": "⭐",
    "sparkles": "✨",
    "sparkle": "✨",
    "rocket": "🚀",
    "party": "🎉",
    "tada": "🎉",
    "celebration": "🎉",
    "check": "✅",
    "checkmark": "✅",
    "check mark": "✅",
    "tick": "✅",
    "tick mark": "✅",
    "green tick": "✅",
    "green check": "✅",
    "white tick": "✅",
    "tick box": "☑️",
    "ticked box": "☑️",
    "checkbox": "☑️",
    "check box": "☑️",
    "checked box": "☑️",
    "box with a tick": "☑️",
    "box with tick": "☑️",
    "tick in a box": "☑️",
    "tick in the box": "☑️",
    "ballot box": "☑️",
    "ballot": "☑️",
    "empty box": "☐",
    "empty checkbox": "☐",
    "unticked box": "☐",
    "cross": "❌",
    "red cross": "❌",
    "cross mark": "❌",
    "x mark": "❌",
    "x": "❌",
    "warning": "⚠️",
    "skull": "💀",
    "poop": "💩",
    "poo": "💩",
    "100": "💯",
    "hundred": "💯",
    "eyes": "👀",
    "brain": "🧠",
    "ghost": "👻",
    "robot": "🤖",
    "alien": "👽",
    "cat": "🐱",
    "dog": "🐶",
    "sun": "☀️",
    "moon": "🌙",
    "rainbow": "🌈",
    "coffee": "☕",
    "pizza": "🍕",
    "beer": "🍺",
    "cake": "🎂",
    "gift": "🎁",
    "trophy": "🏆",
    "crown": "👑",
    "lightbulb": "💡",
    "idea": "💡",
    "bell": "🔔",
    "pencil": "✏️",
    "book": "📖",
    "email": "✉️",
    "phone": "📱",
    "computer": "💻",
    "camera": "📷",
    "money": "💰",
    "speech bubble": "💬",
    "zzz": "💤",
}

_SKIP_NAME_PARTS = (
    "REGIONAL INDICATOR",
    "VARIATION SELECTOR",
    "EMOJI MODIFIER",
    "ZERO WIDTH",
    "COMBINING ",
    "TAG ",
)

_lookup = None
_pattern = None


def _is_emoji_codepoint(cp: int) -> bool:
    # Skin-tone modifiers and flag letters are not something you say on their own.
    if 0x1F3FB <= cp <= 0x1F3FF or 0x1F1E6 <= cp <= 0x1F1FF:
        return False
    if not (0x2600 <= cp <= 0x27BF or 0x2B00 <= cp <= 0x2BFF or 0x1F300 <= cp <= 0x1FAFF):
        return False
    char = chr(cp)
    if unicodedata.category(char) not in ("So", "Sk", "Sm"):
        return False
    try:
        name = unicodedata.name(char)
    except ValueError:
        return False
    return not any(part in name for part in _SKIP_NAME_PARTS)


def _display(cp: int) -> str:
    # BMP symbols like ❤ render as text unless the emoji presentation selector
    # is attached. The supplementary-plane pictographs already look like emoji.
    char = chr(cp)
    if cp < 0x1F000:
        return char + "\uFE0F"
    return char


def _phrases_for(name: str):
    phrase = name.lower()
    phrases = [phrase]
    for suffix in (" sign", " symbol", " mark"):
        if phrase.endswith(suffix):
            phrases.append(phrase[: -len(suffix)].strip())
    for prefix in ("white ", "black ", "heavy ", "large ", "small ", "medium "):
        if phrase.startswith(prefix):
            phrases.append(phrase[len(prefix):].strip())
    return [p for p in phrases if len(p) >= 2]


def _build_lookup() -> dict:
    lookup = {}
    for cp in range(0x2600, 0x1FB00):
        if not _is_emoji_codepoint(cp):
            continue
        try:
            name = unicodedata.name(chr(cp))
        except ValueError:
            continue
        shown = _display(cp)
        for phrase in _phrases_for(name):
            lookup.setdefault(phrase, shown)
    from .emoji_aliases import SPOKEN_ALIASES
    lookup.update(_ALIASES)
    lookup.update(SPOKEN_ALIASES)
    return lookup


def _phrase_pattern(phrase: str) -> str:
    return r"\s+".join(re.escape(part) for part in phrase.split())


def _ensure():
    global _lookup, _pattern
    if _pattern is not None:
        return
    lookup = _build_lookup()
    # Longest phrase first. Python alternation is left-to-right, so "smiley"
    # must not steal the match from "smiley face".
    phrases = sorted(lookup, key=len, reverse=True)
    body = "|".join(_phrase_pattern(phrase) for phrase in phrases)
    _lookup = lookup
    _pattern = re.compile(
        r"(?<!\w)(" + body + r")(?:\s*,\s*|\s+)emoji(?!\w)",
        re.IGNORECASE,
    )


def spoken_emoji_count() -> int:
    _ensure()
    return len(_lookup)


# Replace every "<name> emoji" with the character. Leaves the surrounding
# sentence alone, including a period Whisper added after the cue.
def apply_spoken_emoji(text: str) -> str:
    if not text or "emoji" not in text.casefold():
        return text
    _ensure()

    def _replace(match):
        key = re.sub(r"\s+", " ", match.group(1)).strip().lower()
        return _lookup.get(key, match.group(0))

    return _pattern.sub(_replace, text)
