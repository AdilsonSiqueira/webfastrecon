import re

PROFILE = "concrete5"

PATTERNS = [re.compile(r'concrete5', re.I), re.compile(r'Concrete5', re.I), re.compile(r'concrete/', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'concrete5', text, re.I):
        return True
    if re.search(r'concrete/', text, re.I):
        return True
    return False
