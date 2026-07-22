# WebFastRecon

WebFastRecon e uma ferramenta de varredura rapida para servidor web, focada em identificar tecnologias e executar scan direcionado de caminhos padrao.

Objetivo do projeto:
- Identificar rapidamente servicos e stack web: CMS/aplicacao, framework, runtime e web server.
- Evitar brute force amplo, usando wordlists por perfil.
- Entregar resposta pratica para recon inicial com saida colorida por status HTTP.

## O que ele faz

- Identifica tecnologias por fingerprint (headers + conteudo).
- Em modo auto, detecta multiplos perfis (exemplo: WordPress + Nginx).
- Faz scan de diretorios/arquivos por perfil detectado.
- No Rust, em auto + scan, separa a varredura por categoria e por perfil.
- Salva relatorio em txt, json ou html quando output e informado.

Perfis de alto nivel:
- Web server: Apache, Nginx, IIS, LiteSpeed, OpenLiteSpeed, Caddy, OpenResty, Tomcat, Jetty, Undertow e outros.
- Runtime/plataforma: PHP, ASP.NET, ASP.NET Core, JSP/Servlet, Java EE, Python WSGI, Node.js, Ruby, Perl CGI, Go HTTP, ColdFusion.
- Framework: Laravel, Symfony, Django, Flask, FastAPI, Express, Rails.
- Aplicacao/CMS/painel: WordPress, Drupal, Joomla, Magento, Ghost, Moodle, MediaWiki, Jenkins, Grafana, Kibana, SonarQube, GitLab, Gitea, Portainer, phpMyAdmin, Adminer, Webmin, cPanel, Plesk, DirectAdmin e outros.

## Instalacao (Python)

Requisitos:
- Python 3.8+

Unix/WSL:

```bash
cd /mnt/c/Users/Adilson/Desktop/PROJETOS/webfastrecon
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
cd C:\Users\Adilson\Desktop\PROJETOS\webfastrecon
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Instalacao (Rust)

Requisitos:
- Rust toolchain com Cargo

Build/check:

```bash
cd rust
cargo check
```

## Como usar

### Fluxo recomendado rapido

1. Identificar stack
2. Rodar scan direcionado
3. Salvar relatorio quando necessario

### Comportamento de -t auto

Python e Rust:
- Faz identificacao ampla (aplicacao/CMS + framework + runtime + servidor web).
- Sem --scan: identifica e encerra.
- Com --scan: executa varredura direcionada.

### Exemplos Python

Identificar somente:

```bash
python3 webfastrecon.py -u https://example.com -t auto
```

Identificar e varrer:

```bash
python3 webfastrecon.py -u https://example.com -t auto --scan
```

Varrer e incluir top files sensiveis:

```bash
python3 webfastrecon.py -u https://example.com -t wordpress --topfiles
```

Salvar JSON:

```bash
python3 webfastrecon.py -u https://example.com -t joomla -T 8 -f json -o report.json
```

### Exemplos Rust

Identificar somente:

```bash
cd rust
cargo run -- --url https://example.com -t auto
```

Identificar e varrer (scan por categoria/perfil detectado):

```bash
cd rust
cargo run -- --url https://example.com -t auto --scan
```

Varrer perfil especifico:

```bash
cd rust
cargo run -- --url https://example.com -t joomla -T 8
```

Salvar JSON:

```bash
cd rust
cargo run -- --url https://example.com -t joomla -f json -o report.json
```

### Porta e alvo

- Nao faz port scan.
- A porta vem da URL informada.
- Se nao informar porta, usa padrao do protocolo (http 80, https 443).
- Para porta customizada, informe na URL: https://example.com:8443

### Cores da saida

- 2xx: verde
- 3xx: amarelo
- 4xx/5xx: vermelho
- ERR: vermelho

## Diferencas atuais Python x Rust

- Python:
	- Ja possui fluxo completo com top files.
	- Exibe resumo final com agrupamento por status.
- Rust:
	- Ja identifica multiplos perfis e escaneia por categoria/perfil no modo auto + scan.
	- Exibe possivel falso positivo quando um perfil e detectado sem hits nos caminhos de validacao.
	- Top files no Rust ainda nao esta no mesmo nivel de cobertura do Python.

## Objetivo de performance

WebFastRecon foi pensado para recon inicial rapida, com foco em:
- baixo ruido
- alta utilidade pratica
- identificacao orientada a tecnologia real do alvo

## Contato e Doacoes

GitHub: https://github.com/AdilsonSiqueira

Donate: https://ko-fi.com/adilsonsiqueira

by AdilsonSiqueira
