# corrections.py
# Persistence for post-transcription corrections (postprocess.replacements) —
# the backing store for the history window's one-click "Fix this everywhere...".
# Writes user_settings.yaml directly (same pattern as dictionary.py) so callers
# don't need a live ConfigManager; the running app hot-reloads the postprocess
# section on file change, so a correction takes effect on the next dictation.

import logging
from pathlib import Path
from typing import List

from ruamel.yaml import YAML

from .utils import get_user_app_data_path

logger = logging.getLogger(__name__)
USER_SETTINGS = "user_settings.yaml"


def _settings_path() -> Path:
    return Path(get_user_app_data_path()) / USER_SETTINGS


# Read the current correction list from user_settings.yaml (empty if unset).
def list_replacements() -> List[dict]:
    path = _settings_path()
    if not path.exists():
        return []
    try:
        with open(path, encoding='utf-8') as f:
            data = YAML().load(f) or {}
        items = (data.get('postprocess') or {}).get('replacements') or []
        return [dict(i) for i in items if isinstance(i, dict)]
    except Exception as e:
        logger.warning(f"Could not read replacements: {e}")
        return []


# Append a correction (from_text → to_text). Returns False for empty input, a
# no-op fix (from == to), or an existing identical rule; True once persisted.
def add_replacement(from_text: str, to_text: str,
                    whole_word: bool = True, case_sensitive: bool = False) -> bool:
    from_text = (from_text or '').strip()
    to_text = (to_text or '')
    if not from_text or from_text == to_text:
        return False

    path = _settings_path()
    yaml = YAML()
    if path.exists():
        with open(path, encoding='utf-8') as f:
            data = yaml.load(f) or {}
    else:
        data = {}

    postprocess = data.setdefault('postprocess', {})
    current = list(postprocess.get('replacements') or [])

    # Skip an exact duplicate, but allow updating the target for an existing
    # "from" by replacing that entry rather than stacking a second. Match the
    # "from" case-INsensitively (matching is case-insensitive by default), so
    # adding "teh" when "Teh" already exists updates it instead of creating a
    # second rule that double-fires on the same text.
    for existing in current:
        if isinstance(existing, dict) and str(existing.get('from', '')).lower() == from_text.lower():
            if str(existing.get('to', '')) == to_text:
                return False
            existing['from'] = from_text
            existing['to'] = to_text
            _write(path, yaml, data)
            return True

    entry = {'from': from_text, 'to': to_text}
    if not whole_word:
        entry['whole_word'] = False
    if case_sensitive:
        entry['case_sensitive'] = True
    current.append(entry)
    postprocess['replacements'] = current
    _write(path, yaml, data)
    return True


# Replace the whole correction list. The review page sends its edited list here.
# Empty "from", a no-op (from == to), and a repeated "from" are dropped. When
# the same heard word appears twice, the later row wins, matching the way
# add_replacement updates an existing rule instead of stacking a second one.
def save_replacements(items) -> list:
    cleaned = _clean_items(items)
    path = _settings_path()
    yaml = YAML()
    if path.exists():
        with open(path, encoding='utf-8') as f:
            data = yaml.load(f) or {}
    else:
        data = {}
    postprocess = data.setdefault('postprocess', {})
    postprocess['replacements'] = cleaned
    _write(path, yaml, data)
    return [dict(item) for item in cleaned]


def _clean_items(items) -> list:
    if not isinstance(items, list):
        raise ValueError('replacements must be a list')
    cleaned = []
    seen = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        frm = str(item.get('from', '')).strip()
        to = item.get('to', '')
        to = '' if to is None else str(to)
        if not frm or frm == to:
            continue
        entry = {'from': frm, 'to': to}
        if item.get('whole_word') is False:
            entry['whole_word'] = False
        if item.get('case_sensitive'):
            entry['case_sensitive'] = True
        if item.get('regex'):
            entry['regex'] = True
        key = frm.casefold()
        if key in seen:
            cleaned[seen[key]] = entry
            continue
        seen[key] = len(cleaned)
        cleaned.append(entry)
    return cleaned


# Pairs where one rule's output is another rule's input. Replacements run top
# to bottom, so a later rule can rewrite an earlier result. A swap is the
# send/save case: each rule undoes the other, and the lower one always wins.
# A chain is only reported when the second rule actually runs after the first.
# If the consumer already ran, it never sees this output.
def find_conflicts(items) -> list:
    rules = []
    for index, item in enumerate(items or []):
        if not isinstance(item, dict):
            continue
        frm = str(item.get('from', '')).strip()
        to = str(item.get('to') or '').strip()
        if frm:
            rules.append((index, frm, to))

    by_from = {}
    for index, frm, _to in rules:
        by_from.setdefault(frm.casefold(), []).append(index)

    conflicts = []
    reported = set()
    for index, frm, to in rules:
        if not to:
            continue
        for other_index in by_from.get(to.casefold(), []):
            if other_index == index:
                continue
            other_to = str(items[other_index].get('to') or '').strip()
            swap = other_to.casefold() == frm.casefold()
            if not swap and other_index < index:
                continue
            key = tuple(sorted((index, other_index)))
            if key in reported:
                continue
            reported.add(key)
            if swap:
                earlier, later = (index, other_index) if index < other_index else (other_index, index)
                kind = 'swap'
            else:
                earlier, later = index, other_index
                kind = 'chain'
            conflicts.append({
                'kind': kind,
                'earlier': earlier,
                'later': later,
                'later_from': str(items[later].get('from', '')).strip(),
                'later_to': str(items[later].get('to', '')).strip(),
                'message': _conflict_message(items, earlier, later, kind == 'swap'),
            })
    conflicts.sort(key=lambda item: (item['kind'] != 'swap', item['later']))
    return conflicts


def _conflict_message(items, earlier: int, later: int, swap: bool) -> str:
    first = items[earlier]
    second = items[later]
    heard = str(first.get('from', '')).strip()
    mid = str(first.get('to', '')).strip()
    final = str(second.get('to', '')).strip()
    if swap:
        return (
            f'"{heard}" is changed to "{mid}", and "{mid}" is changed to "{final}". '
            f'The second rule runs later, so "{mid}" is always pasted as "{final}".'
        )
    return (
        f'"{heard}" is changed to "{mid}", then that result is changed to "{final}".'
    )


def _write(path: Path, yaml: YAML, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    logger.info("Saved a post-transcription correction to user_settings.yaml")
