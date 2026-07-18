"""Laravel indicators"""

PROFILE = "laravel"

INDICATORS = ["X-Powered-By: PHP", "laravel"]

def matches(headers, body):
    return "laravel" in (body or "").lower()
