import sys
sys.path.append(r"C:\Users\Adilson\Desktop\PROJETOS\WebPathScan")
import requests
from fingerprint import _find_generator

url = 'https://www.unesco.org/'
r = requests.get(url, timeout=20, allow_redirects=True)
print('status', r.status_code)
print('server:', r.headers.get('Server'))
print('x-powered-by:', r.headers.get('X-Powered-By'))
print('generator:', r.headers.get('Generator'))
print('detected:', _find_generator(r.headers, r.text))
text = r.text.lower()
idx = text.find('is-drupal')
print('is-drupal index:', idx)
if idx != -1:
    start = max(0, idx-40)
    end = min(len(text), idx+60)
    print('context:', text[start:end])
print('drupalsettings in text:', 'drupalsettings' in text)
print('drupal.settings in text:', 'drupal.settings' in text)
print('body contains drupal:', 'drupal' in text)
