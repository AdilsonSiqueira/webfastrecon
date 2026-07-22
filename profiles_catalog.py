"""Catalog of supported profiles, categories and wordlist aliases."""

SUPPORTED_PROFILES = [
    # mode
    "auto",
    # web servers
    "apache", "nginx", "iis", "litespeed", "openlitespeed", "caddy",
    "openresty", "tomcat", "jetty", "undertow", "cherokee", "lighttpd",
    "h2o", "tengine", "oracle_http_server", "ibm_http_server",
    # runtimes/platform
    "php", "aspnet", "aspnet_core", "jsp_servlet", "java_ee", "python_wsgi",
    "nodejs", "ruby", "perl_cgi", "go_http", "coldfusion",
    # frameworks
    "laravel", "symfony", "django", "flask", "fastapi", "express", "rails",
    # apps/cms/panels
    "wordpress", "drupal", "joomla", "magento", "ghost", "moodle", "mediawiki",
    "jenkins", "grafana", "kibana", "sonarqube", "gitlab", "gitea", "portainer",
    "phpmyadmin", "adminer", "webmin", "cpanel", "plesk", "directadmin",
    "prestashop", "opencart", "typo3", "concrete5", "umbraco", "shopify",
    "silverstripe", "dotnetnuke", "expressionengine",
]

PROFILE_CATEGORIES = {
    # web servers
    "apache": "web_server",
    "nginx": "web_server",
    "iis": "web_server",
    "litespeed": "web_server",
    "openlitespeed": "web_server",
    "caddy": "web_server",
    "openresty": "web_server",
    "tomcat": "web_server",
    "jetty": "web_server",
    "undertow": "web_server",
    "cherokee": "web_server",
    "lighttpd": "web_server",
    "h2o": "web_server",
    "tengine": "web_server",
    "oracle_http_server": "web_server",
    "ibm_http_server": "web_server",
    # runtimes
    "php": "runtime",
    "aspnet": "runtime",
    "aspnet_core": "runtime",
    "jsp_servlet": "runtime",
    "java_ee": "runtime",
    "python_wsgi": "runtime",
    "nodejs": "runtime",
    "ruby": "runtime",
    "perl_cgi": "runtime",
    "go_http": "runtime",
    "coldfusion": "runtime",
    # frameworks
    "laravel": "framework",
    "symfony": "framework",
    "django": "framework",
    "flask": "framework",
    "fastapi": "framework",
    "express": "framework",
    "rails": "framework",
    # apps
    "wordpress": "application",
    "drupal": "application",
    "joomla": "application",
    "magento": "application",
    "ghost": "application",
    "moodle": "application",
    "mediawiki": "application",
    "jenkins": "application",
    "grafana": "application",
    "kibana": "application",
    "sonarqube": "application",
    "gitlab": "application",
    "gitea": "application",
    "portainer": "application",
    "phpmyadmin": "application",
    "adminer": "application",
    "webmin": "application",
    "cpanel": "application",
    "plesk": "application",
    "directadmin": "application",
    "prestashop": "application",
    "opencart": "application",
    "typo3": "application",
    "concrete5": "application",
    "umbraco": "application",
    "shopify": "application",
    "silverstripe": "application",
    "dotnetnuke": "application",
    "expressionengine": "application",
}

# First match by priority: app > framework > runtime > web server.
DETECTION_PRIORITY = [
    "wordpress", "drupal", "joomla", "magento", "ghost", "moodle", "mediawiki",
    "jenkins", "grafana", "kibana", "sonarqube", "gitlab", "gitea", "portainer",
    "phpmyadmin", "adminer", "webmin", "cpanel", "plesk", "directadmin",
    "prestashop", "opencart", "typo3", "concrete5", "umbraco", "shopify",
    "silverstripe", "dotnetnuke", "expressionengine",
    "laravel", "symfony", "django", "flask", "fastapi", "express", "rails",
    "php", "aspnet_core", "aspnet", "jsp_servlet", "java_ee", "python_wsgi",
    "nodejs", "ruby", "perl_cgi", "go_http", "coldfusion",
    "openresty", "openlitespeed", "litespeed", "nginx", "apache", "iis",
    "caddy", "tomcat", "jetty", "undertow", "cherokee", "lighttpd", "h2o",
    "tengine", "oracle_http_server", "ibm_http_server",
]

# Reuse existing CMS lists when possible and fallback by category for the new scope.
WORDLIST_ALIASES = {
    "openlitespeed": "litespeed",
    "openresty": "nginx",
    "tengine": "nginx",
    "oracle_http_server": "apache",
    "ibm_http_server": "apache",
    "aspnet_core": "aspnet",
    "java_ee": "jsp_servlet",
    "rails": "ruby",
    "fastapi": "python_wsgi",
    "flask": "python_wsgi",
    "django": "python_wsgi",
    "express": "nodejs",
    "symfony": "php",
    "mediawiki": "php",
    "adminer": "php",
    "webmin": "linux_webadmin",
    "cpanel": "linux_webadmin",
    "plesk": "linux_webadmin",
    "directadmin": "linux_webadmin",
}


def normalize_profile_name(raw_profile):
    if not raw_profile:
        return "auto"
    p = raw_profile.lower().strip()
    aliases = {
        "asp.net": "aspnet",
        "asp.net core": "aspnet_core",
        "jsp": "jsp_servlet",
        "servlet": "jsp_servlet",
        "java ee": "java_ee",
        "python": "python_wsgi",
        "node": "nodejs",
        "go": "go_http",
        "ruby on rails": "rails",
        "rubyonrails": "rails",
        "iis": "iis",
    }
    return aliases.get(p, p)


def display_category(profile_name):
    return PROFILE_CATEGORIES.get(profile_name, "unknown")


def resolve_wordlist_profile(profile_name):
    return WORDLIST_ALIASES.get(profile_name, profile_name)
