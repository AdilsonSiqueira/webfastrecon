"""Magento indicators"""

PROFILE = "magento"

INDICATORS = ["Mage.Cookies", "/magento/"]

def matches(headers, body):
    return any(i in (body or "") for i in INDICATORS)
