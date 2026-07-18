import re

PROFILE = "opencart"

PATTERNS = [re.compile(r'opencart', re.I), re.compile(r'catalog/', re.I), re.compile(r'index\.php\?route=', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'OpenCart', text, re.I):
        return True
    if re.search(r'index\.php\?route=', text, re.I):
        return True
    return False
