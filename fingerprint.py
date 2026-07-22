"""Fingerprint detection focused on lightweight web stack identification.

Detection order:
1) Application/CMS/panel
2) Framework
3) Runtime/platform
4) Web server
"""
from urllib.parse import urljoin

from profiles_catalog import DETECTION_PRIORITY, PROFILE_CATEGORIES


def _header(headers, name):
    return headers.get(name) or headers.get(name.lower()) or ""


def _has_any(text, tokens):
    hay = (text or "").lower()
    return any(t in hay for t in tokens)


def _collect_text(headers, body):
    header_blob = " ".join(
        f"{k}:{v}" for k, v in (headers.items() if hasattr(headers, "items") else [])
    ).lower()
    return f"{header_blob}\n{(body or '').lower()}"


def _match_rules(headers, body):
    server = _header(headers, "Server").lower()
    powered = _header(headers, "X-Powered-By").lower()
    via = _header(headers, "Via").lower()
    set_cookie = _header(headers, "Set-Cookie").lower()
    blob = _collect_text(headers, body)

    rules = {
        # applications
        "wordpress": ["wp-content/", "wp-includes/", "wp-json", "wp-admin", "wp-login.php"],
        "drupal": ["drupalsettings", "drupal.settings", "sites/default/files", "is-drupal"],
        "joomla": ["/media/system/js/", "joomla!", "option=com_"],
        "magento": ["mage/cookies.js", "magento", "skin/frontend"],
        "ghost": ["ghost/content", "ghost.io", "content=\"ghost\""],
        "moodle": ["moodle", "moodle-session", "course/view.php"],
        "mediawiki": ["mediawiki", "mw.config", "w/index.php?title="],
        "jenkins": ["x-jenkins", "jenkins-agent-protocols", "/login?from=%2f"],
        "grafana": ["grafana", "x-grafana", "public/build/grafana"],
        "kibana": ["kbn-name", "kibana", "kbn-version"],
        "sonarqube": ["sonarqube", "js/sonar", "api/system/status"],
        "gitlab": ["gitlab", "_gitlab_session", "assets/gitlab"],
        "gitea": ["gitea", "_csrf", "content=\"gitea\""],
        "portainer": ["portainer", "x-portaineragent", "portainer.io"],
        "phpmyadmin": ["phpmyadmin", "pmahometext", "pma_"],
        "adminer": ["adminer", "Login - Adminer".lower(), "name=\"auth[server]\""],
        "webmin": ["webmin", "session_login.cgi", "x-webmin"],
        "cpanel": ["cpanel", "whm", "cpsess"],
        "plesk": ["plesk", "plesk-session-id", "x-plesk"],
        "directadmin": ["directadmin", "cmd=login", "x-directadmin"],
        "prestashop": ["prestashop", "modules/", "index.php?controller="],
        "opencart": ["route=common/home", "catalog/view/theme", "opencart"],
        "typo3": ["typo3", "typo3conf", "index.php?id="],
        "concrete5": ["concrete5", "/concrete/", "ccm.token"],
        "umbraco": ["umbraco", "umbraco_client", "x-umbraco"],
        "shopify": ["shopify", "cdn.shopify.com", "x-shopify"],
        "silverstripe": ["silverstripe", "x-powered-by: silverstripe"],
        "dotnetnuke": ["dotnetnuke", "dnn", "__requestverificationtoken"],
        "expressionengine": ["expressionengine", "exp_last_visit", "exp_tracker"],
        # frameworks
        "laravel": ["laravel", "xsrf-token", "laravel_session"],
        "symfony": ["symfony", "sf-toolbar", "x-debug-token"],
        "django": ["csrftoken", "django", "__admin_media_prefix__"],
        "flask": ["flask", "werkzeug", "session="],
        "fastapi": ["fastapi", "swagger-ui", "openapi.json"],
        "express": ["x-powered-by: express", "express"],
        "rails": ["ruby on rails", "_rails", "actiondispatch"],
        # runtimes/platform
        "php": ["php", "phpsessid", "x-powered-by: php"],
        "aspnet_core": ["asp.net core", "kestrel", "aspnetcore"],
        "aspnet": ["x-aspnet-version", "asp.net"],
        "jsp_servlet": ["jsessionid", "jsp", "servlet"],
        "java_ee": ["java ee", "jakarta", "jsessionid"],
        "python_wsgi": ["wsgi", "gunicorn", "uwsgi", "werkzeug"],
        "nodejs": ["node.js", "x-powered-by: express", "npm"],
        "ruby": ["passenger", "ruby", "rack"],
        "perl_cgi": ["perl", "cgi-bin"],
        "go_http": ["golang", "go-http-client", "x-go"],
        "coldfusion": ["coldfusion", "cfid", "cftoken"],
    }

    combined = "\n".join([server, powered, via, set_cookie, blob])

    matched = []
    for profile in DETECTION_PRIORITY:
        tokens = rules.get(profile, [])
        if tokens and _has_any(combined, [t.lower() for t in tokens]):
            matched.append(profile)

    # server-specific detection is more reliable from Server/Via headers.
    server_rules = {
        "apache": ["apache"],
        "nginx": ["nginx"],
        "iis": ["microsoft-iis"],
        "litespeed": ["litespeed"],
        "openlitespeed": ["openlitespeed"],
        "caddy": ["caddy"],
        "openresty": ["openresty"],
        "tomcat": ["tomcat"],
        "jetty": ["jetty"],
        "undertow": ["undertow"],
        "cherokee": ["cherokee"],
        "lighttpd": ["lighttpd"],
        "h2o": ["h2o"],
        "tengine": ["tengine"],
        "oracle_http_server": ["oracle-http-server", "oracle http server"],
        "ibm_http_server": ["ibm_http_server", "ibm http server"],
    }
    server_blob = " ".join([server, via])
    for profile, tokens in server_rules.items():
        if _has_any(server_blob, tokens) and profile not in matched:
            matched.append(profile)

    if not matched:
        return None, []
    return matched[0], matched


def detect_profile(session, url, timeout=5.0, follow=True):
    """Probe target URL and return detected primary profile and details."""
    try:
        r = session.get(url, timeout=timeout, allow_redirects=follow)
        headers = r.headers
        body = r.text
    except Exception:
        return None, {}

    primary, matched = _match_rules(headers, body)

    # lightweight fallback probe only for admin interfaces with strong signatures
    if not primary:
        probes = {
            "jenkins": ["/login", "/manage"],
            "grafana": ["/login", "/api/health"],
            "kibana": ["/login", "/api/status"],
            "phpmyadmin": ["/phpmyadmin/", "/pma/"],
        }
        for profile, paths in probes.items():
            for path in paths:
                try:
                    probe_url = urljoin(url.rstrip("/") + "/", path.lstrip("/"))
                    r2 = session.get(probe_url, timeout=timeout, allow_redirects=follow)
                    b2 = (r2.text or "").lower()
                    if r2.status_code in (200, 401, 403) and (profile in b2 or profile in str(r2.headers).lower()):
                        primary = profile
                        matched = [profile]
                        break
                except Exception:
                    continue
            if primary:
                break

    details = {
        "headers": dict(headers),
        "sample": (body or "")[:400],
        "matches": matched,
    }
    if primary:
        details["category"] = PROFILE_CATEGORIES.get(primary, "unknown")
    return primary, details
