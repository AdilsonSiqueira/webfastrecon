import re

PROFILE = "dotnetnuke"

PATTERNS = [re.compile(r'dotnetnuke', re.I), re.compile(r'DotNetNuke', re.I), re.compile(r'DNN/', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'dotnetnuke', text, re.I):
        return True
    if re.search(r'dnn/', text, re.I):
        return True
    return False
