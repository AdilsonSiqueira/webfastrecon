#!/usr/bin/env python3
"""CMSPathFinder - entry point and CLI"""
import argparse
from scanner import Scanner
from banner import get_banner

VERSION = "0.1"


def build_parser():
    p = argparse.ArgumentParser(description="CMSPathFinder - simple CMS path scanner")
    p.add_argument('-u', '--url', required=True, help='URL do alvo')
    p.add_argument('-t', '--type', default='auto', help='Perfil (auto, tomcat, wordpress...)')
    p.add_argument('-w', '--wordlist', help='Wordlist personalizada (arquivo)')
    p.add_argument('-T', '--threads', type=int, default=None, help='Número de threads (omitido = 1 req/s)')
    p.add_argument('-o', '--output', help='Salvar relatório (caminho). Se omitido, o arquivo é salvo automaticamente em reports/.')
    p.add_argument('-f', '--format', choices=['txt', 'json', 'html'], default='txt', help='Formato do relatório')
    p.add_argument('-a', '--agent', help='User-Agent personalizado')
    p.add_argument('--timeout', type=float, default=5.0, help='Timeout das requisições')
    p.add_argument('--proxy', help='Proxy HTTP/SOCKS (ex: http://127.0.0.1:8080)')
    p.add_argument('--follow', action='store_true', help='Seguir redirecionamentos')
    p.add_argument('--status', help='Filtrar códigos HTTP (ex: 200,301,302)')
    p.add_argument('--version', action='store_true', help='Exibir versão')
    p.add_argument('--force', action='store_true', help='Ignorar validação de perfil e forçar scan')
    p.add_argument('--topfiles', action='store_true', help='Verificar arquivos sensíveis/padrão (top files)')
    p.add_argument('--identify-only', action='store_true', help='Apenas identificar o CMS e não executar a varredura')
    p.add_argument('--scan', action='store_true', help='Executar a varredura mesmo quando -t auto for usado')
    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.version:
        print(VERSION)
        return

    # print banner and settings
    try:
        print(get_banner(colored=True))
    except Exception:
        try:
            print(get_banner(colored=False))
        except Exception:
            pass

    print(f"[*] Target.............: {args.url}")
    print(f"[*] CMS................: {args.type}")
    print(f"[*] Threads............: {'1 req/s' if args.threads is None else args.threads}")
    wl = args.wordlist or f'wordlists/{args.type}.txt'
    print(f"[*] Wordlist...........: {wl}")
    print(f"[*] Timeout............: {args.timeout}s")
    if args.output:
        print(f"[*] Report............: {args.output}\n")
    else:
        print('[*] Report............: nenhum (use -o/--output para salvar)\n')

    is_auto_profile = (args.type or 'auto').lower() == 'auto'
    if args.identify_only or (is_auto_profile and not args.scan):
        print('[INFO] Modo identificação apenas: não será feita varredura.\n')
    else:
        print('[INFO] Starting scan...\n')

    scanner = Scanner(args)
    scanner.run()


if __name__ == '__main__':
    main()
