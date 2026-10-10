# shouting.py
# Whisper sometimes locks into ALL CAPS for a sentence, or flips partway
# through one. That is the model, not the user. Rewrite those stretches
# into normal sentence case and leave real acronyms alone.

import re

# Ordinary words that show up in shouted transcripts. A hotword written in
# capitals is kept only when it is not one of these, so "REPLY" still becomes
# "reply" while "TESOL" can stay "TESOL".
_COMMON_WORDS = frozenset("""
a an the and or but if so to of in on at by for with from as is are was were
be been being it its this that these those i you he she we they me him her us
them my your his our their not no nor yes do did does done have has had having
will would can could should shall may might must just than then there here
when where what which who whom whose why how all any some every both few more
most other such only own same too very also back up out off over into about
after before because while during without within again still already even
now today well much many one two three new old good bad big small long right
left please thanks thank hello hi hey sir yes yeah okay ok uh um ah
want need like know think say said get got go going went come came make made
see look take give tell ask try use find work call feel seem leave put keep
let help start show hear play run move live believe mean include follow
somebody someone something anything nothing everything people person time
way day year thing world life man men woman women child
reply message text link post email name page file code
""".split())

# Short tokens people actually want in capitals. "US" is missing on purpose:
# in dictated sentences it is almost always the pronoun.
_ACRONYMS = frozenset("""
AI OK UK EU UN TV PC ID URL PDF API GPU CPU RAM USB SQL CSS HTML HTTP HTTPS
FAQ ASAP ETA CEO CFO CTO HR PR QA UI UX ESL OTC IQ GPS ATM PIN SMS DVD VIP
DIY RSVP TBD TBA IMO BTW FYI LLC INC SEO CRM MVP NASA FIFA COVID APP IOS
""".split())

_I_FORMS = frozenset({"i", "i'm", "i'd", "i'll", "i've"})

# MAX_RETRIES stays one token so a code constant is not sentence-cased.
# The second alternative is a normal word, including DON'T and FRAZER'S.
_WORD_RE = re.compile(
    r"[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+"
    r"|[A-Za-z]+(?:['’][A-Za-z]+)?"
)


def keep_tokens_from_hotwords(hotwords) -> list:
    # Hotwords the user wrote in capitals ("TESOL", "FRAZER'S") are names or
    # abbreviations. Keep that casing when a shouted sentence is rewritten.
    kept = []
    seen = set()
    for item in hotwords or []:
        for match in _WORD_RE.finditer(str(item)):
            token = match.group()
            if "_" in token or not _is_shouting_word(token):
                continue
            if token.casefold() in _COMMON_WORDS:
                continue
            key = _key(token)
            if key in seen:
                continue
            seen.add(key)
            kept.append(token)
    return kept


def fix_shouting(text: str, keep=()) -> str:
    if not text:
        return text
    keep_keys = set(_ACRONYMS)
    for token in keep or ():
        keep_keys.add(_key(str(token)))

    matches = list(_WORD_RE.finditer(text))
    if not matches:
        return text

    in_run = []
    for index, match in enumerate(matches):
        in_run.append(_belongs_in_shout_run(match.group()))

    spans = _shout_spans(matches, in_run, keep_keys, len(matches) == 1)
    if not spans:
        return text

    pieces = []
    cursor = 0
    for start, end in spans:
        span_from = matches[start].start()
        span_to = matches[end - 1].end()
        pieces.append(text[cursor:span_from])
        pieces.append(_rewrite_span(
            text[span_from:span_to],
            _at_sentence_start(text, span_from),
            keep_keys,
        ))
        cursor = span_to
    pieces.append(text[cursor:])
    return "".join(pieces)


def _shout_spans(matches, in_run, keep_keys, single_word_text: bool):
    spans = []
    index = 0
    count = len(matches)
    while index < count:
        if not in_run[index]:
            index += 1
            continue
        end = index + 1
        while end < count and in_run[end]:
            end += 1
        if _span_should_rewrite(matches[index:end], keep_keys, single_word_text and index == 0 and end == count):
            spans.append((index, end))
        index = end
    return spans


def _span_should_rewrite(span_matches, keep_keys, is_entire_text: bool) -> bool:
    shouted = [match for match in span_matches if _is_shouting_word(match.group())]
    if not shouted:
        return False
    if len(shouted) >= 2:
        return True
    word = shouted[0].group()
    if _key(word) in keep_keys:
        return False
    letters = _letters(word)
    if len(letters) >= 6:
        return True
    # A lone "HELLO" or "HI" is still the model shouting, not an acronym.
    return is_entire_text


def _rewrite_span(span: str, starts_sentence: bool, keep_keys) -> str:
    matches = list(_WORD_RE.finditer(span))
    pieces = []
    cursor = 0
    cap_next = starts_sentence
    prev_was_initial = False
    for match in matches:
        gap = span[cursor:match.start()]
        following = span[match.end():match.end() + 1]
        pieces.append(gap)
        # "A.I." has periods, but those periods are not sentence ends.
        if _gap_ends_sentence(gap) and not prev_was_initial:
            cap_next = True
        word = match.group()
        pieces.append(_rewrite_word(word, gap, following, cap_next, keep_keys))
        cap_next = False
        prev_was_initial = len(_letters(word)) == 1 and following == "."
        cursor = match.end()
    pieces.append(span[cursor:])
    return "".join(pieces)


def _rewrite_word(word: str, gap_before: str, following: str, cap_next: bool, keep_keys) -> str:
    if "_" in word:
        return word
    key = _key(word)
    if key in {"AM", "PM"} and re.search(r"\d\s*$", gap_before):
        return word.upper()
    # "A.I." is an abbreviation. A lone "A" in the middle of a sentence is not.
    if len(_letters(word)) == 1 and following == ".":
        return word.upper()
    if key in keep_keys:
        return word.upper()
    lowered = word.lower().replace("’", "'")
    if lowered in _I_FORMS:
        return "I" + word.lower()[1:]
    if cap_next and lowered:
        return lowered[0].upper() + lowered[1:]
    return word.lower()


def _belongs_in_shout_run(word: str) -> bool:
    if "_" in word:
        return False
    if _is_shouting_word(word):
        return True
    # A single capital ("A", "I", the letters in "A.I.") must not split the
    # surrounding shouted words into pieces too small to fix.
    return len(_letters(word)) == 1 and word.isupper()


def _is_shouting_word(word: str) -> bool:
    letters = _letters(word)
    return len(letters) >= 2 and all(char.isupper() for char in letters)


def _letters(word: str) -> str:
    return "".join(char for char in word if char.isalpha())


def _key(word: str) -> str:
    return _letters(word).upper()


def _at_sentence_start(text: str, index: int) -> bool:
    prev = text[:index].rstrip(" \t")
    if not prev:
        return True
    return prev[-1] in ".!?\n"


def _gap_ends_sentence(gap: str) -> bool:
    stripped = gap.rstrip(" \t")
    return bool(stripped) and stripped[-1] in ".!?\n"
