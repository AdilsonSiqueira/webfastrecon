# CMSPathFinder

CMSPathFinder is a lightweight scanner for standard CMS paths and files only.

Features
- CMS fingerprinting (WordPress, Drupal, Joomla, Magento, PrestaShop, OpenCart, Ghost, TYPO3, Concrete5, Umbraco, Shopify, SilverStripe, DotNetNuke, ExpressionEngine, Laravel, Moodle)
- Scans only CMS default paths and files, not generic directory brute-force
- Multi-threaded CMS path enumeration with optional 1 req/s rate limiting
- Per-CMS wordlists and top-files checks
- Report output in `txt`, `json` and `html` formats

Quick usage
```bash
python3 cmspathfinder.py -u https://target.example/ -t drupal -T 10 --topfiles
```

Examples
- Scan Joomla with default settings:
```bash
python3 cmspathfinder.py -u http://site.com -t joomla
```
- Scan WordPress with 8 threads and save JSON report:
```bash
python3 cmspathfinder.py -u http://site.com -t wordpress -T 8 -f json -o report.json
```
- Auto-detect CMS and stop after identification (no scan):
```bash
python3 cmspathfinder.py -u http://site.com -t auto
```
- Force the scan even with `-t auto`:
```bash
python3 cmspathfinder.py -u http://site.com -t auto --scan
```

Example
- Detects CMS automatically: `-t auto`
- Force a profile: `--force`

Wordlists
- Stored in `wordlists/` per CMS. Each list includes `robots.txt` and `sitemap.xml`.

## Instalação

Requisitos mínimos:
- Python 3.8+
- `git` e acesso à internet

Instalação (Unix / WSL):

```bash
cd /mnt/c/Users/Adilson/Desktop/PROJETOS/cmspathfinder
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Instalação (Windows PowerShell):

```powershell
cd C:\Users\Adilson\Desktop\PROJETOS\cmspathfinder
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Uso

Exemplos rápidos:

- Detectar CMS automaticamente e parar após a identificação (Python):
```bash
python3 cmspathfinder.py -u https://example.com -t auto
```
- Detectar CMS automaticamente e parar após a identificação (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t auto
```
- Forçar a varredura mesmo com `-t auto` (Python):
```bash
python3 cmspathfinder.py -u https://example.com -t auto --scan
```
- Forçar a varredura mesmo com `-t auto` (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t auto --scan
```
- Scan Joomla com 8 threads e salvar JSON (Python):
```bash
python3 cmspathfinder.py -u https://example.com -t joomla -T 8 -f json -o report.json
```
- Scan Joomla com 8 threads e salvar JSON (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t joomla -T 8 -f json -o report.json
```
- Verificar arquivos sensíveis (`--topfiles`) (Python):
```bash
python3 cmspathfinder.py -u https://example.com -t wordpress --topfiles
```
- Verificar arquivos sensíveis (`--topfiles`) (Rust):
```bash
cd rust
cargo run -- -u https://example.com -t wordpress --topfiles
```
- Apenas identificar o CMS sem fazer varredura (Python):
```bash
python3 cmspathfinder.py -u https://example.com -t auto --identify-only
```
- Apenas identificar o CMS sem fazer varredura (Rust):
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
