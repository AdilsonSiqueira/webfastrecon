# WebFastRecon

WebFastRecon is a lightweight web stack recon tool focused on identification first and targeted scanning second.

What it does
- Identifies one primary profile in this order: application -> framework -> runtime -> web server.
- Runs targeted path checks using profile-based wordlists (no broad brute-force).
- Optionally checks top files and default sensitive paths for the detected/selected profile.
- Saves reports in `txt`, `json`, or `html`.
- In `-t auto`, both Python and Rust fingerprint the full stack scope: CMS/app, framework, runtime, and web server.
- Auto examples covered by detection include: WordPress/Drupal/Joomla, Jenkins/Grafana/Kibana/phpMyAdmin, PHP/Node.js/Python WSGI/ASP.NET, Apache/Nginx/IIS/Tomcat/OpenResty/Caddy.

Profiles (high level)
- Web server: Apache, Nginx, IIS, LiteSpeed, OpenLiteSpeed, Caddy, OpenResty, Tomcat, Jetty, Undertow, Cherokee, Lighttpd, H2O, Tengine, Oracle HTTP Server, IBM HTTP Server.
- Runtime/platform: PHP, ASP.NET, ASP.NET Core, JSP/Servlet, Java EE, Python WSGI, Node.js, Ruby, Perl CGI, Go HTTP, ColdFusion.
- Framework: Laravel, Symfony, Django, Flask, FastAPI, Express, Rails.
- Application/CMS/panel: WordPress, Drupal, Joomla, Magento, Ghost, Moodle, MediaWiki, Jenkins, Grafana, Kibana, SonarQube, GitLab, Gitea, Portainer, phpMyAdmin, Adminer, Webmin, cPanel, Plesk, DirectAdmin and others already in the project.

Quick usage
```bash
python3 webfastrecon.py -u https://target.example -t auto
```

Targeted scan after identify
```bash
python3 webfastrecon.py -u https://target.example -t auto --scan --topfiles
```

Force a specific profile
```bash
python3 webfastrecon.py -u https://target.example -t jenkins -T 8
```

Save JSON report
```bash
python3 webfastrecon.py -u https://target.example -t wordpress -f json -o reports/wp.json
```

Compatibility command
```bash
python3 webfastrecon.py -u https://target.example -t auto
```

## Instalação

Requisitos mínimos:
- Python 3.8+
- `git` e acesso à internet

Instalação (Unix / WSL):

```bash
cd /mnt/c/Users/Adilson/Desktop/PROJETOS/webfastrecon
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Instalação (Windows PowerShell):

```powershell
cd C:\Users\Adilson\Desktop\PROJETOS\webfastrecon
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Uso

Comportamento do `-t auto` (Python e Rust):
- Faz identificação ampla de tecnologia (servidor + CMS/app + runtime/framework).
- Padrão: identifica e para (não inicia varredura).
- Para varrer depois da identificação, use `--scan`.

Exemplos rápidos:

- Detectar perfil automaticamente e parar após a identificação (Python):
```bash
python3 webfastrecon.py -u https://example.com -t auto
```
- Detectar perfil automaticamente e parar após a identificação (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t auto
```
- Forçar a varredura mesmo com `-t auto` (Python):
```bash
python3 webfastrecon.py -u https://example.com -t auto --scan
```
- Forçar a varredura mesmo com `-t auto` (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t auto --scan
```
- Scan Joomla com 8 threads e salvar JSON (Python):
```bash
python3 webfastrecon.py -u https://example.com -t joomla -T 8 -f json -o report.json
```
- Scan Joomla com 8 threads e salvar JSON (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t joomla -T 8 -f json -o report.json
```
- Verificar arquivos sensíveis (`--topfiles`) (Python):
```bash
python3 webfastrecon.py -u https://example.com -t wordpress --topfiles
```
- Verificar arquivos sensíveis (`--topfiles`) (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t wordpress --topfiles
```
- Apenas identificar tecnologia sem fazer varredura (Python):
```bash
python3 webfastrecon.py -u https://example.com -t auto --identify-only
```
- Apenas identificar tecnologia sem fazer varredura (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t auto --identify-only
```

### Python vs Rust

- A versão Python é a mais simples e está pronta para uso direto.
- A versão Rust é uma alternativa mais performática e mantêm o mesmo fluxo de uso, com comandos parecidos.
- Ambos aceitam as opções principais: `-u/--url`, `-t/--type`, `-w/--wordlist`, `-T/--threads`, `-o/--output`, `-f/--format`, `--topfiles` e `--identify-only`.


## Contato e Doações

GitHub: https://github.com/AdilsonSiqueira

Donate: https://ko-fi.com/adilsonsiqueira

by AdilsonSiqueira
