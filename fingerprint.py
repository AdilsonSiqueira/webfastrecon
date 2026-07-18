"""Fingerprint detection using profile modules.

Strategy:
- Check for explicit generator metadata (`<meta name="generator">`, `X-Powered-By`) and map to known CMS.
- If generator not found, delegate to profile modules' `matches()` functions.
"""
import re
from importlib import import_module
from urllib.parse import urljoin

PROFILE_MODULES = [
    'profiles.wordpress', 'profiles.drupal', 'profiles.joomla',
    'profiles.magento', 'profiles.laravel', 'profiles.moodle',
    'profiles.prestashop', 'profiles.opencart', 'profiles.ghost',
    'profiles.typo3', 'profiles.concrete5', 'profiles.umbraco',
    'profiles.shopify', 'profiles.silverstripe', 'profiles.dotnetnuke',
    'profiles.expressionengine', 'profiles.auto'
]

# common generator mappings (lowercased)
GENERATOR_MAP = {
    'wordpress': 'wordpress',
    'joomla': 'joomla',
    'drupal': 'drupal',
    'magento': 'magento',
    'prestashop': 'prestashop',
    'shopify': 'shopify',
    'ghost': 'ghost',
    'typo3': 'typo3',
    'concrete5': 'concrete5',
    'umbraco': 'umbraco',
}


def _find_generator(headers, body):
    # check headers first
    for h in ('x-powered-by', 'server'):
        v = headers.get(h)
        if v:
            v_lower = v.lower()
            for k in GENERATOR_MAP:
                if k in v_lower:
                    return GENERATOR_MAP[k]

    # check meta generator in body
    m = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']', body, re.I)
    if m:
        g = m.group(1).lower()
        for k in GENERATOR_MAP:
            if k in g:
                return GENERATOR_MAP[k]

    # direct Drupal page markers
    if re.search(r'class=["\']is-drupal["\']', body, re.I) or re.search(r'drupalsettings', body, re.I) or re.search(r'drupal\.settings', body, re.I):
        return 'drupal'

    return None


def detect_profile(session, url, timeout=5.0, follow=True):
    """Probe `url` and return detected profile name or None.

    Returns a tuple (profile_name, details) where details is a dict with
    headers and body for debugging.
    """
    try:
        r = session.get(url, timeout=timeout, allow_redirects=follow)
        headers = r.headers
        body = r.text
    except Exception:
        return None, {}

    gen = _find_generator(headers, body)
    if gen:
        return gen, {'headers': dict(headers), 'sample': body[:400], 'generator': gen}

    # Try probing common admin paths for common CMS as a fallback (non-invasive)
    ADMIN_PATHS = {
        'joomla': ['/administrator/', '/administrator/index.php'],
        'wordpress': ['/wp-admin/', '/wp-login.php'],
        'drupal': ['/user/', '/node/']
    }

    for cms, paths in ADMIN_PATHS.items():
        for p in paths:
            try:
                probe_url = urljoin(url.rstrip('/') + '/', p.lstrip('/'))
                r2 = session.get(probe_url, timeout=timeout, allow_redirects=follow)
                if r2.status_code and r2.status_code < 500:
                    body2 = r2.text or ''
                    # quick heuristics: presence of cms name or admin keywords
                    if cms in body2.lower() or 'administrator' in body2.lower() or 'wp-' in body2.lower() or 'drupal' in body2.lower():
                        return cms, {'probe': probe_url, 'status': r2.status_code, 'sample': body2[:400]}
                    # allow 403 on admin paths as indicator
                    if r2.status_code in (401, 403):
                        return cms, {'probe': probe_url, 'status': r2.status_code, 'sample': body2[:200]}
            except Exception:
                continue

    # delegate to profile modules
    for modname in PROFILE_MODULES:
        try:
            mod = import_module(modname)
            matches = getattr(mod, 'matches', None)
            profile = getattr(mod, 'PROFILE', None)
            if callable(matches) and profile:
                try:
                    if matches(headers, body):
                        return profile, {'headers': dict(headers), 'sample': body[:400]}
                except Exception:
                    continue
        except Exception:
            continue

    return None, {'headers': dict(headers), 'sample': body[:400]}
