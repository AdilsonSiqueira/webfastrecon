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
from urllib.parse import urljoin, urlparse


class Scanner:
    def __init__(self, args):
        self.url = args.url
        # normalize profile: accept only full canonical name or a single-letter shortcut
        raw_profile = (args.type or 'auto')
        p = raw_profile.lower()

        SUPPORTED = [
            'auto', 'wordpress', 'drupal', 'joomla', 'magento', 'prestashop',
            'shopify', 'opencart', 'ghost', 'typo3', 'concrete5', 'silverstripe',
            'umbraco', 'dotnetnuke', 'expressionengine', 'laravel', 'moodle'
        ]

        if p == 'auto':
            self.profile = 'auto'
        elif len(p) == 1:
            # resolve by first letter only if unique among supported
            candidates = [s for s in SUPPORTED if s.startswith(p) and s != 'auto']
            if len(candidates) == 1:
                self.profile = candidates[0]
            elif len(candidates) > 1:
                raise SystemExit(f"Perfil ambíguo para '{raw_profile}'. Possíveis correspondências: {', '.join(candidates)}. Use o nome completo.")
            else:
                raise SystemExit(f"Nenhum perfil suportado começa com '{raw_profile}'. Perfis válidos: {', '.join([s for s in SUPPORTED if s != 'auto'])}")
        else:
            if p in SUPPORTED:
                self.profile = p
            else:
                raise SystemExit(f"Perfil inválido: '{raw_profile}'. Perfis válidos: {', '.join([s for s in SUPPORTED if s != 'auto'])}")

        self.force = getattr(args, 'force', False)
        self.wordlist = args.wordlist
        self.rate_limit = (args.threads is None)
        self.threads = 1 if args.threads is None else max(1, args.threads)
        self.output = args.output
        self.outfmt = args.format
        self.agent = args.agent
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
            'phpmyadmin': ['phpmyadmin/', 'pma/', 'setup/']
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
        try:
            fname = f'wordlists/{self.profile}.txt'
            with open(fname, 'r', encoding='utf-8') as f:
                return [l.strip() for l in f if l.strip()]
        except Exception:
            return []

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

                # colored output based on status class
                RESET = '\x1b[0m'
                GREEN = '\x1b[32m'
                YELLOW = '\x1b[33m'
                RED = '\x1b[31m'
                CYAN = '\x1b[36m'

                if code is None:
                    color = RED
                    label = 'ERR'
                elif 200 <= code < 300:
                    color = GREEN
                    label = str(code)
                elif 300 <= code < 400:
                    color = YELLOW
                    label = str(code)
                elif 400 <= code < 600:
                    color = RED
                    label = str(code)
                else:
                    color = CYAN
                    label = str(code)

                print(f"{color}[{label}]{RESET} {path}")

            self.q.task_done()

    def save_report(self):
        outpath = self.output
        if not outpath:
            # build automatic report path
            try:
                host = urlparse(self.url).netloc.replace(':', '_')
            except Exception:
                host = 'target'
            ext = self.outfmt
            outpath = f'reports/{host}_{self.profile}.{ext}'

        # ensure reports directory exists
        try:
            import os
            os.makedirs(os.path.dirname(outpath), exist_ok=True)
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
                with open(outpath, 'w', encoding='utf-8') as f:
                    for r in self.results:
                        f.write(f"{r['status']}\t{r['url']}\n")
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
        RED = '\x1b[31m'

        if self.profile == 'auto':
            if detected:
                print(f"{GREEN}{detected.upper()}{RESET} - perfil detectado")
                self.profile = detected
                self.profile_matched = True
            else:
                print('Não foi possível detectar o perfil; prosseguindo com "auto".')

        else:
            if detected and detected == self.profile:
                print(f"{GREEN}{self.profile.upper()}{RESET} - corresponde ao perfil solicitado")
                self.profile_matched = True
            elif detected and detected != self.profile:
                # mismatch -> colored output and abort
                print(f"{RED}CMS NÃO CORRESPONDE AO ESCOLHIDO{RESET}")
                print(f"Detectado: {GREEN}{detected.upper()}{RESET} | Solicitado: {RED}{self.profile.upper()}{RESET}")
                print('Abortando: CMS NÃO CORRESPONDE AO ESCOLHIDO; nenhum relatório será criado.')
                return
            else:
                # no detection but specific requested -> abort unless --force
                if self.force:
                    print(f"Aviso: não foi possível detectar automaticamente; forçando perfil solicitado: {self.profile.upper()} (--force). Prosseguindo...")
                else:
                    print(f"{RED}NÃO FOI POSSÍVEL DETECTAR O SERVIDOR{RESET}")
                    print(f"Solicitado: {self.profile.upper()} — abortando. Use --force para forçar o scan se necessário.")
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

        if self.results:
            print('\nFound:')
            for r in sorted(self.results, key=lambda x: (x.get('status') or 0, x.get('path'))):
                print(f"[{r.get('status')}] {r.get('path')}")

    def scan_topfiles(self, elapsed=0):
        RESET = '\x1b[0m'
        GREEN = '\x1b[32m'
        YELLOW = '\x1b[33m'
        RED = '\x1b[31m'
        print('\n[TOP FILES] Verificando arquivos sensíveis...')
        for path in self.TOP_FILES:
            target = urljoin(self.url.rstrip('/') + '/', path)
            try:
                r = self.session.get(target, timeout=self.timeout, allow_redirects=self.follow)
                code = r.status_code
            except Exception:
                code = None

            # color selection
            if code is None:
                color = RED
                label = 'ERR'
            elif 200 <= code < 300:
                color = GREEN
                label = str(code)
            elif 300 <= code < 400:
                color = YELLOW
                label = str(code)
            elif 400 <= code < 600:
                color = RED
                label = str(code)
            else:
                color = RESET
                label = str(code)

            print(f"{color}[{label}]{RESET} {path} -> {target}")
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
