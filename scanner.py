"""Scanner core: threaded path enumeration and simple reporting

Features added: colored console output by HTTP status class, counters,
simple summary and automatic report path when not provided.
"""
import threading
import queue
import requests
import json
import fingerprint
import time
import os
from urllib.parse import urljoin, urlparse
from profiles_catalog import (
    SUPPORTED_PROFILES,
    PROFILE_CATEGORIES,
    normalize_profile_name,
    resolve_wordlist_profile,
)


class Scanner:
    def __init__(self, args):
        self.url = args.url
        # normalize profile: accept only full canonical name or a single-letter shortcut
        raw_profile = (args.type or 'auto')
        p = normalize_profile_name(raw_profile)

        if p == 'auto':
            self.profile = 'auto'
        elif len(p) == 1:
            # resolve by first letter only if unique among supported
            candidates = [s for s in SUPPORTED_PROFILES if s.startswith(p) and s != 'auto']
            if len(candidates) == 1:
                self.profile = candidates[0]
            elif len(candidates) > 1:
                raise SystemExit(f"Perfil ambíguo para '{raw_profile}'. Possíveis correspondências: {', '.join(candidates)}. Use o nome completo.")
            else:
                raise SystemExit(f"Nenhum perfil suportado começa com '{raw_profile}'. Perfis válidos: {', '.join([s for s in SUPPORTED_PROFILES if s != 'auto'])}")
        else:
            if p in SUPPORTED_PROFILES:
                self.profile = p
            else:
                raise SystemExit(f"Tipo inválido: '{raw_profile}'. Tipos válidos: {', '.join([s for s in SUPPORTED_PROFILES if s != 'auto'])}")

        self.force = getattr(args, 'force', False)
        self.wordlist = args.wordlist
        self.rate_limit = (args.threads is None)
        self.identify_only = getattr(args, 'identify_only', False) or (p == 'auto' and not getattr(args, 'scan', False))
        self.threads = 1 if args.threads is None else max(1, args.threads)
        self.output = args.output
        self.outfmt = args.format
        self.agent = args.agent
        self.username = getattr(args, 'username', None)
        self.password = getattr(args, 'password', None)
        self.timeout = args.timeout
        self.proxy = args.proxy
        self.follow = args.follow
        self.topfiles = getattr(args, 'topfiles', False)
        self.status_filter = None
        if args.status:
            self.status_filter = set(int(s.strip()) for s in args.status.split(','))

        self.session = requests.Session()
        if self.agent:
            self.session.headers.update({'User-Agent': self.agent})
        if self.username and self.password:
            self.session.auth = (self.username, self.password)
        self.session.max_redirects = 10
        if self.proxy:
            self.session.proxies.update({'http': self.proxy, 'https': self.proxy})

        self.q = queue.Queue()
        self.results = []
        self.lock = threading.Lock()
        self.requests_count = 0
        self.errors_count = 0
        self.found_count = 0
        self.profile_matched = False
        self.detected_profile = None
        self.detected_details = {}
        self.top_results = []

        # default list of common sensitive/top files to check when --topfiles is used
        self.TOP_FILES = [
            '.env', '.env.example', 'wp-config.php', 'config.php', 'configuration.php',
            '.htpasswd', '.htaccess', 'adminer.php', 'phpinfo.php', 'phpmyadmin/', 'pma/',
            '.git/', '.git/config', '.gitignore', 'backup.zip', 'backup.tar.gz', 'backup.sql',
            'db.sql', 'dump.sql', 'dump.zip', 'site.zip', 'wp-login.php', 'wp-admin/',
            'administrator/', 'config.bak', 'config.php.bak', 'old/', 'old.zip'
        ]

        # per-CMS top files / paths
        self.TOP_FILES_MAP = {
            'apache': ['server-status', 'server-info', 'icons/', 'cgi-bin/'],
            'nginx': ['nginx_status', 'stub_status', '.well-known/'],
            'iis': ['iisstart.htm', 'aspnet_client/', 'web.config'],
            'tomcat': ['manager/html', 'host-manager/html', 'docs/', 'examples/'],
            'jetty': ['jmx/', 'test/', 'favicon.ico'],
            'undertow': ['management', 'health', 'metrics'],
            'caddy': ['.well-known/', 'metrics', 'debug/pprof/'],
            'php': ['index.php', 'phpinfo.php', '.env', 'vendor/'],
            'nodejs': ['package.json', 'node_modules/', 'api/', 'health'],
            'python_wsgi': ['wsgi.py', 'manage.py', 'static/', 'admin/'],
            'aspnet': ['web.config', 'bin/', 'App_Data/', 'trace.axd'],
            'aspnet_core': ['appsettings.json', 'appsettings.Production.json', 'swagger/index.html'],
            'jsp_servlet': ['WEB-INF/', 'META-INF/', 'jsp/'],
            'wordpress': ['wp-admin/', 'wp-login.php', 'wp-config.php', 'wp-content/', 'wp-includes/'],
            'joomla': ['administrator/', 'configuration.php', 'templates/', 'components/', 'modules/'],
            'drupal': ['sites/default/', 'core/', 'profiles/', 'modules/', 'themes/'],
            'magento': ['app/etc/env.php', 'downloader/', 'pub/', 'skin/', 'media/'],
            'prestashop': ['install/', 'admin/', 'config/settings.inc.php', 'modules/', 'themes/'],
            'opencart': ['admin/', 'install/', 'system/', 'catalog/'],
            'ghost': ['ghost/', 'content/', 'config.production.json', 'core/'],
            'typo3': ['typo3/', 'typo3conf/', 'fileadmin/'],
            'concrete5': ['concrete/', 'application/config/', 'updates/'],
            'umbraco': ['Umbraco/', 'Umbraco_Client/', 'App_Plugins/'],
            'silverstripe': ['assets/', 'public/', 'silverstripe-cache/', 'framework/'],
            'dotnetnuke': ['DesktopModules/', 'Portals/', 'Admin/', 'Providers/', 'Install/'],
            'expressionengine': ['system/', 'themes/', 'images/', 'admin.php', 'index.php'],
            'laravel': ['vendor/', '.env', 'storage/', 'bootstrap/cache/'],
            'moodle': ['moodle/', 'config.php', 'admin/', 'login/index.php', 'course/view.php'],
            'phpmyadmin': ['phpmyadmin/', 'pma/', 'setup/'],
            'jenkins': ['login', 'manage', 'script', 'whoAmI/'],
            'grafana': ['login', 'api/health', 'public/build/'],
            'kibana': ['login', 'api/status', 'app/home'],
            'sonarqube': ['api/system/status', 'sessions/new', 'admin'],
            'gitlab': ['users/sign_in', 'explore', 'help'],
            'gitea': ['user/login', 'explore/repos', 'api/v1/version'],
            'portainer': ['#!/auth', 'api/status', 'api/endpoints'],
            'adminer': ['adminer.php', 'adminer/', 'login'],
            'webmin': ['session_login.cgi', 'unauthenticated/', 'sysinfo.cgi'],
            'cpanel': ['cpanel', 'whm', 'webmail'],
            'plesk': ['login_up.php', 'smb/web/login', 'enterprise/control/agent.php'],
            'directadmin': ['CMD_LOGIN', 'CMD_API_SHOW_USERS', 'CMD_ADMIN_SHOW_ALL_USERS']
        }

        # build effective topfiles list for this profile
        self.topfile_list = list(self.TOP_FILES)
        if self.profile in self.TOP_FILES_MAP:
            self.topfile_list.extend(self.TOP_FILES_MAP[self.profile])

        # try to load custom wordlist file: wordlists/topfiles/<profile>.txt
        try:
            custom_path = f'wordlists/topfiles/{self.profile}.txt'
            with open(custom_path, 'r', encoding='utf-8') as f:
                for l in f:
                    l = l.strip()
                    if l:
                        self.topfile_list.append(l)
        except Exception:
            pass

    def load_wordlist(self):
        if self.wordlist:
            try:
                with open(self.wordlist, 'r', encoding='utf-8') as f:
                    return [l.strip() for l in f if l.strip()]
            except Exception:
                return []

        # fallback to profile wordlists folder
        wl_profile = resolve_wordlist_profile(self.profile)
        candidates = [
            f'wordlists/{self.profile}.txt',
            f'wordlists/{wl_profile}.txt',
        ]
        cat = PROFILE_CATEGORIES.get(self.profile)
        if cat == 'web_server':
            candidates.append('wordlists/generic_webserver.txt')
        elif cat == 'runtime':
            candidates.append('wordlists/generic_runtime.txt')
        elif cat == 'framework':
            candidates.append('wordlists/generic_framework.txt')
        elif cat == 'application':
            candidates.append('wordlists/generic_application.txt')

        for fname in candidates:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    return [l.strip() for l in f if l.strip()]
            except Exception:
                continue

        return []

    def _refresh_topfile_list(self):
        self.topfile_list = list(self.TOP_FILES)
        if self.profile in self.TOP_FILES_MAP:
            self.topfile_list.extend(self.TOP_FILES_MAP[self.profile])

        try:
            custom_path = f'wordlists/topfiles/{self.profile}.txt'
            with open(custom_path, 'r', encoding='utf-8') as f:
                for l in f:
                    l = l.strip()
                    if l:
                        self.topfile_list.append(l)
        except Exception:
            pass

    @staticmethod
    def _status_tag(code):
        reset = '\x1b[0m'
        green = '\x1b[32m'
        yellow = '\x1b[33m'
        red = '\x1b[31m'
        cyan = '\x1b[36m'

        if code is None:
            return f"{red}[ERR]{reset}"
        if 200 <= code < 300:
            return f"{green}[{code}]{reset}"
        if 300 <= code < 400:
            return f"{yellow}[{code}]{reset}"
        if 400 <= code < 600:
            return f"{red}[{code}]{reset}"
        return f"{cyan}[{code}]{reset}"

    def worker(self):
        while True:
            try:
                path = self.q.get_nowait()
            except queue.Empty:
                return
            target = urljoin(self.url.rstrip('/') + '/', path)
            try:
                r = self.session.get(target, timeout=self.timeout, allow_redirects=self.follow)
                code = r.status_code
            except Exception as e:
                code = None
                with self.lock:
                    self.errors_count += 1

            entry = {'path': path, 'url': target, 'status': code}

            if self.rate_limit:
                time.sleep(1)

            do_append = (self.status_filter is None) or (code in self.status_filter)
            if do_append:
                with self.lock:
                    self.results.append(entry)
                    self.requests_count += 1
                    if code and 200 <= code < 300:
                        self.found_count += 1

                print(f"{self._status_tag(code)} {path}")

            self.q.task_done()

    def save_report(self):
        outpath = self.output
        if not outpath:
            parsed = urlparse(self.url)
            host = (parsed.netloc or parsed.path or 'target').replace(':', '_').replace('/', '_')
            outpath = f'reports/{host}_{self.profile}.{self.outfmt}'

        # ensure reports directory exists
        try:
            os.makedirs(os.path.dirname(outpath) or '.', exist_ok=True)
        except Exception:
            pass

        try:
            if self.outfmt == 'json':
                with open(outpath, 'w', encoding='utf-8') as f:
                    json.dump(self.results, f, indent=2, ensure_ascii=False)
            elif self.outfmt == 'html':
                rows = ''.join(f'<tr><td>{r["status"]}</td><td><a href="{r["url"]}">{r["url"]}</a></td></tr>' for r in self.results)
                html = f"<html><body><table>{rows}</table></body></html>"
                with open(outpath, 'w', encoding='utf-8') as f:
                    f.write(html)
            else:
                grouped = {}
                for r in self.results:
                    status = r.get('status')
                    if status is None:
                        bucket = 'ERR'
                    elif 200 <= status < 300:
                        bucket = '200'
                    elif 300 <= status < 400:
                        bucket = '300'
                    elif 400 <= status < 500:
                        bucket = '400'
                    elif 500 <= status < 600:
                        bucket = '500'
                    else:
                        bucket = str(status)
                    grouped.setdefault(bucket, []).append(r)

                order = ['200', '300', '400', '500', 'ERR']
                with open(outpath, 'w', encoding='utf-8') as f:
                    for bucket in order:
                        if bucket not in grouped:
                            continue
                        f.write(f"[{bucket}]\n")
                        for r in sorted(grouped[bucket], key=lambda x: (x.get('status') or 0, x.get('path'))):
                            f.write(f"{r.get('status')}\t{r.get('url')}\n")
                        f.write('\n')
        except Exception as e:
            print('Failed to save report:', e)
            return None

        print(f"Report saved: {outpath}")
        return outpath

    def run(self):
        # initial probe to detect profile
        detected, details = None, {}
        try:
            # always follow redirects during profile fingerprinting so we inspect the real target page
            detected, details = fingerprint.detect_profile(self.session, self.url, timeout=self.timeout, follow=True)
        except Exception:
            detected = None

        # color codes
        RESET = '\x1b[0m'
        GREEN = '\x1b[32m'
        YELLOW = '\x1b[33m'
        RED = '\x1b[31m'

        if self.profile == 'auto':
            if detected:
                self.detected_profile = detected
                self.detected_details = details or {}
                cat = PROFILE_CATEGORIES.get(detected, 'unknown')
                print(f"Identified - {GREEN}{detected.upper()}{RESET} ({cat})")
                self.profile = detected
                self._refresh_topfile_list()
                self.profile_matched = True
            else:
                print(f"{RED}Nenhuma tecnologia suportada foi identificada no alvo.{RESET}")
                print('Cancelando a varredura porque nenhum perfil suportado foi detectado.')
                return

        else:
            if detected and detected == self.profile:
                self.detected_profile = detected
                self.detected_details = details or {}
                print(f"{GREEN}{self.profile.upper()}{RESET} - perfil confirmado")
                self.profile_matched = True
            elif detected and detected != self.profile:
                self.detected_profile = detected
                self.detected_details = details or {}
                # keep going because a host can expose multiple stack layers.
                print(f"{RED}Perfil detectado diferente do solicitado.{RESET}")
                print(f"Detectado: {GREEN}{detected.upper()}{RESET} | Solicitado: {YELLOW}{self.profile.upper()}{RESET}")
                print('Prosseguindo com o perfil solicitado. Use --force se quiser ignorar este aviso no fluxo de automação.')
            else:
                # no detection but specific requested -> abort unless --force
                if self.force:
                    print(f"Aviso: não foi possível detectar automaticamente; forçando perfil solicitado: {self.profile.upper()} (--force). Prosseguindo...")
                else:
                    print(f"{RED}Não foi possível confirmar o perfil no alvo.{RESET}")
                    print('Prosseguindo com o perfil solicitado. Se preferir exigir confirmação, use -t auto sem --scan.')

        if self.identify_only:
            print('\n[INFO] Identificação concluída.')
            return

        paths = self.load_wordlist()
        if not paths:
            print('Nenhuma wordlist encontrada para o perfil ou arquivo fornecido.')
            return

        for p in paths:
            self.q.put(p)

        start = time.time()
        threads = []
        for i in range(self.threads):
            t = threading.Thread(target=self.worker, daemon=True)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

        # calculate elapsed time for the main scan
        elapsed = time.time() - start

        # optional top files check (pass elapsed so scan_topfiles can include statistics)
        if self.topfiles:
            self.scan_topfiles(elapsed)

        # print summary
        print('\n================ Scan Summary ================')
        print(f"Target        : {self.url}")
        # print only the profile short name; color it green if matched
        prof_display = (self.profile or '').upper()
        if self.profile_matched:
            print(f"Profile       : {GREEN}{prof_display}{RESET}")
        else:
            print(f"Profile       : {prof_display}")
        print(f"Category      : {PROFILE_CATEGORIES.get(self.profile, 'unknown')}")
        if self.detected_profile:
            print(f"Detected      : {self.detected_profile.upper()} ({PROFILE_CATEGORIES.get(self.detected_profile, 'unknown')})")

        if self.results:
            print('\nFound:')
            grouped = {}
            for r in self.results:
                status = r.get('status')
                if status is None:
                    bucket = 'ERR'
                elif 200 <= status < 300:
                    bucket = '200'
                elif 300 <= status < 400:
                    bucket = '300'
                elif 400 <= status < 500:
                    bucket = '400'
                elif 500 <= status < 600:
                    bucket = '500'
                else:
                    bucket = str(status)
                grouped.setdefault(bucket, []).append(r)

            for bucket in ['200', '300', '400', '500', 'ERR']:
                if bucket in grouped:
                    if bucket == 'ERR':
                        print(f"\n{self._status_tag(None)}")
                    else:
                        print(f"\n{self._status_tag(int(bucket))}")
                    for r in sorted(grouped[bucket], key=lambda x: (x.get('status') or 0, x.get('path'))):
                        print(f"{self._status_tag(r.get('status'))} {r.get('path')}")

        if not self.topfiles:
            self.save_report()

    def scan_topfiles(self, elapsed=0):
        print('\n[TOP FILES] Verificando arquivos sensíveis...')
        for path in self.topfile_list:
            target = urljoin(self.url.rstrip('/') + '/', path)
            try:
                r = self.session.get(target, timeout=self.timeout, allow_redirects=self.follow)
                code = r.status_code
            except Exception:
                code = None

            print(f"{self._status_tag(code)} {path} -> {target}")
            entry = {'path': path, 'url': target, 'status': code, 'type': 'topfile'}
            self.top_results.append(entry)
            self.results.append(entry)

        print('\nStatistics')
        print('----------------------------------------------')
        print(f"Requests........: {self.requests_count}")
        print(f"Found...........: {self.found_count}")
        print(f"Errors..........: {self.errors_count}")
        m, s = divmod(int(elapsed), 60)
        h, m = divmod(m, 60)
        print(f"Time............: {h:02d}:{m:02d}:{s:02d}")

        outpath = self.save_report()
        if outpath:
            print(f"\nReport saved: {outpath}")
