import re

PROFILE = "prestashop"

PATTERNS = [re.compile(r'prestashop', re.I), re.compile(r'PrestaShop', re.I), re.compile(r'config/settings.inc.php', re.I), re.compile(r'/modules/', re.I)]


def matches(headers, body):
    text = body or ""
    if re.search(r'Prestashop', text, re.I):
        return True
    if re.search(r'config/settings\.inc\.php', text, re.I):
        return True
    if re.search(r'content="PrestaShop', text, re.I):
        return True
    return False
