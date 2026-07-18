"""Joomla indicators (improved)

Look for admin path, option=com patterns, or generator meta.
"""

import re

PROFILE = "joomla"

PATTERNS = [re.compile(r'index\.php\?option=com_'), re.compile(r'/administrator/'), re.compile(r'component/'), re.compile(r'Joomla', re.I)]


def matches(headers, body):
    body_text = (body or "")
    if re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\'][^"\']*joomla', body_text, re.I):
        return True

    for p in PATTERNS:
        if p.search(body_text):
            return True

    svr = headers.get('Server', '')
    if 'joomla' in svr.lower():
        return True

    return False
