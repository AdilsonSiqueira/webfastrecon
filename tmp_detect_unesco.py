import sys
sys.path.append(r"C:\Users\Adilson\Desktop\PROJETOS\cmspathfinder")
from fingerprint import _find_generator
import requests
r = requests.get('https://www.unesco.org/', timeout=20, allow_redirects=True)
print(_find_generator(r.headers, r.text))
