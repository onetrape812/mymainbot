import re

SUPPORTED_TAGS = frozenset({
    "b", "i", "u", "s", "code", "pre", "a",
    "blockquote", "tg-spoiler", "tg-emoji", "strong", "em",
})

TAG_RE = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>")


def sanitize_html(text: str) -> str:
    def _replace(m: re.Match) -> str:
        tag = m.group(1).lower()
        if tag in SUPPORTED_TAGS:
            return m.group(0)
        return ""
    return TAG_RE.sub(_replace, text)
