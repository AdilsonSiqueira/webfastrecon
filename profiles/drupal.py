"""Drupal indicators (improved)

Check sites/default, Drupal settings, core paths and generator meta.
"""

import re

PROFILE = "drupal"

PATTERNS = [re.compile(r'sites/default'), re.compile(r'Drupal', re.I), re.compile(r'/core/'), re.compile(r'Drupal\.settings')]


def matches(headers, body):
    body_text = (body or "")
    if re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\'][^"\']*drupal', body_text, re.I):
        return True
    if re.search(r'class=["\']is-drupal["\']', body_text, re.I):
        return True
    for p in PATTERNS:
        if p.search(body_text):
            return True

    svr = headers.get('Server', '')
    if 'drupal' in svr.lower():
        return True

    return False
