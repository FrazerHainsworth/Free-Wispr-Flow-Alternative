# platform/windows/focused_text.py
# Reads the text of the control the user is typing in, via UI Automation.
# Edit learning uses this to see a word they fixed after a dictation landed.
# macOS has no equivalent here; the watcher simply does nothing off Windows.

import logging
import re

logger = logging.getLogger(__name__)

_MAX_CHARS = 4000


def _clean(text) -> str:
    if not isinstance(text, str):
        return ""
    text = text.replace("\ufffc", " ").replace("\u00a0", " ")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def _paragraph_around_caret(element, mod) -> str:
    # The caret sits in the sentence just dictated. Expanding to that paragraph
    # avoids diffing against the rest of a long page or document.
    raw = element.GetCurrentPattern(mod.UIA_TextPatternId)
    if not raw:
        return ""
    pattern = raw.QueryInterface(mod.IUIAutomationTextPattern)
    ranges = pattern.GetSelection()
    if ranges and ranges.Length > 0:
        span = ranges.GetElement(0)
        span.ExpandToEnclosingUnit(mod.TextUnit_Paragraph)
        text = _clean(span.GetText(_MAX_CHARS))
        if text:
            return text
    return _clean(pattern.DocumentRange.GetText(_MAX_CHARS))


class FocusedTextReader:
    # One UI Automation client per watcher thread. COM objects are apartment-bound,
    # so this must be created and used on the same thread.
    def __init__(self):
        self._mod = None
        self._uia = None

    def _client(self):
        if self._uia is not None:
            return self._uia
        import comtypes
        import comtypes.client
        try:
            comtypes.CoInitialize()
        except OSError:
            pass
        self._mod = comtypes.client.GetModule("UIAutomationCore.dll")
        self._uia = comtypes.client.CreateObject(
            "{ff48dba4-60ef-4201-aa87-54103eef594e}",
            interface=self._mod.IUIAutomation,
        )
        return self._uia

    def read(self) -> str:
        try:
            element = self._client().GetFocusedElement()
            if element is None:
                return ""
            text = _paragraph_around_caret(element, self._mod)
            if text:
                return text
            value = _clean(element.GetCurrentPropertyValue(self._mod.UIA_ValueValuePropertyId))
            return value
        except Exception as e:
            logger.debug(f"Could not read the focused text: {e}")
            return ""
