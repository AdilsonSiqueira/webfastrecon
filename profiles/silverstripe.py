import re

PROFILE = "silverstripe"

PATTERNS = [re.compile(r'silverstripe', re.I), re.compile(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']SilverStripe', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'silverstripe', text, re.I):
        return True
    return False
