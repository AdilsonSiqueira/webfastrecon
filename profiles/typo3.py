import re

PROFILE = "typo3"

PATTERNS = [re.compile(r'typo3', re.I), re.compile(r'typo3conf', re.I), re.compile(r'fileadmin/', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'typo3', text, re.I):
        return True
    return False
