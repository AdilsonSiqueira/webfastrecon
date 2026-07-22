import sys
sys.path.append(r"C:\Users\Adilson\Desktop\PROJETOS\webfastrecon")
from fingerprint import _find_generator
import requests
r = requests.get('https://www.unesco.org/', timeout=20, allow_redirects=True)
print(_find_generator(r.headers, r.text))
