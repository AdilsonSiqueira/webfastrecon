"""Tomcat fingerprints"""

PROFILE = "tomcat"

INDICATORS = ["Apache Tomcat", "Tomcat"]

def matches(headers, body):
    return any(i in headers.get('Server', '') for i in INDICATORS)
