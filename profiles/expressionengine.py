import re

PROFILE = "expressionengine"

PATTERNS = [re.compile(r'expressionengine', re.I), re.compile(r'ExpressionEngine', re.I), re.compile(r'EE', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'expressionengine', text, re.I):
        return True
    return False
