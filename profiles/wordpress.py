"""WordPress indicators (more strict)

Look for path patterns and meta generator rather than loose 'WordPress' mentions.
"""

import re

PROFILE = "wordpress"

PATTERNS = [re.compile(r'/wp-content/'), re.compile(r'/wp-includes/'), re.compile(r'wp-login\.php'), re.compile(r'/wp-admin'), re.compile(r'wp-json')]


def matches(headers, body):
    body_text = (body or "")
    # meta generator check
    if re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\'][^"\']*wordpress', body_text, re.I):
        return True

    for p in PATTERNS:
        if p.search(body_text):
            return True

    # also check headers
    svr = headers.get('Server', '')
    if 'wordpress' in svr.lower():
        return True

    return False
