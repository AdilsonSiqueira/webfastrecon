"""Nginx fingerprints"""

PROFILE = "nginx"

INDICATORS = ["nginx"]

def matches(headers, body):
    return "nginx" in headers.get('Server', '').lower()
