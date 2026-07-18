import re

PROFILE = "umbraco"

PATTERNS = [re.compile(r'umbraco', re.I), re.compile(r'Umbraco/', re.I), re.compile(r'App_Plugins/', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'umbraco', text, re.I):
        return True
    return False
