"""Apache fingerprints"""

PROFILE = "apache"

INDICATORS = ["Apache", "mod_", "Server: Apache"]

def matches(headers, body):
    return any(i in headers.get('Server', '') for i in INDICATORS)
