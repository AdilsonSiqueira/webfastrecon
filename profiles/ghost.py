import re

PROFILE = "ghost"

PATTERNS = [re.compile(r'ghost', re.I), re.compile(r'content="Ghost', re.I), re.compile(r'ghost/content', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'ghost', text, re.I):
        return True
    return False
