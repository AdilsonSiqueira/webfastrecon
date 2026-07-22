import sys
sys.path.append(r"C:\Users\Adilson\Desktop\PROJETOS\webfastrecon")
import requests
import argparse
from scanner import Scanner

class Args:
    url = 'https://www.unesco.org/'
    type = 'drupal'
    wordlist = None
    threads = None
    output = None
    format = 'txt'
    agent = None
    timeout = 5.0
    proxy = None
    follow = False
    force = False
    topfiles = False
    status = None

args = Args()
scanner = Scanner(args)
print('profile', scanner.profile)
print('threads', scanner.threads)
print('rate_limit', scanner.rate_limit)
print('follow', scanner.follow)
print('profile matched', scanner.profile_matched)
print('detect profile result:')
print(scanner.session.headers)
detected, details = None, {}
try:
    detected, details = __import__('fingerprint').detect_profile(scanner.session, scanner.url, timeout=scanner.timeout, follow=True)
except Exception as e:
    print('exception', e)
print('detected', detected)
print('details', details)
