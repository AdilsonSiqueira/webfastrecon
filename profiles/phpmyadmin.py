"""phpMyAdmin indicators"""

PROFILE = "phpmyadmin"

INDICATORS = ["phpMyAdmin", "pma_"]

def matches(headers, body):
    return any(i in (body or "") for i in INDICATORS)
