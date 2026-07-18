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

- Detectar CMS automaticamente e parar após a identificação:
```bash
python3 cmspathfinder.py -u https://example.com -t auto
```
- Forçar a varredura mesmo com `-t auto`:
```bash
python3 cmspathfinder.py -u https://example.com -t auto --scan
```
- Scan Joomla com 8 threads e salvar JSON:
```bash
python3 cmspathfinder.py -u https://example.com -t joomla -T 8 -f json -o report.json
```
- Verificar arquivos sensíveis (`--topfiles`):
```bash
python3 cmspathfinder.py -u https://example.com -t wordpress --topfiles
```
- Apenas identificar o CMS sem fazer varredura:
```bash
python3 cmspathfinder.py -u https://example.com -t auto --identify-only
```

## Como publicar no GitHub (tutorial rápido)

1. Crie o repositório no GitHub: https://github.com/new — nome sugerido: `cmspathfinder`.
2. No seu repositório local, confirme as mudanças e adicione o remote:

```bash
git add .
git commit -m "Initial CMSPathFinder project"
git remote add origin https://github.com/AdilsonSiqueira/cmspathfinder.git
git branch -M main
git push -u origin main
```

Se o Git pedir usuário/senha ao `push`, gere um Personal Access Token (PAT) no GitHub e use-o como senha.

### Usando `gh` (GitHub CLI) — recomendado

```bash
gh auth login
gh repo create AdilsonSiqueira/cmspathfinder --public --source=. --remote=origin --push
```

## Gerar token (PAT)

1. No GitHub: Settings → Developer settings → Personal access tokens → Fine‑grained tokens → Generate new token.
2. Dê permissão `Contents: Read & write` para o repositório e copie o token (apenas mostrado uma vez).
3. Use o token como senha no `git push` quando solicitado.

## Contribuição

- Abra issues e pull requests no GitHub.
- Atualize as wordlists em `wordlists/` e adicione `wordlists/topfiles/<cms>.txt` quando pertinente.

## Contato e Doações

GitHub: https://github.com/AdilsonSiqueira

Donate: https://ko-fi.com/adilsonsiqueira

by AdilsonSiqueira