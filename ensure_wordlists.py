import os
p = os.path.join(os.path.dirname(__file__), 'wordlists')
changed = []
for fname in sorted(os.listdir(p)):
    if not fname.endswith('.txt'):
        continue
    path = os.path.join(p, fname)
    with open(path, 'r', encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f]
    lower = [l.lower().strip('/') for l in lines if l.strip()]
    to_add = []
    for need in ('robots.txt','sitemap.xml'):
        if need not in lower:
            to_add.append(need)
    if to_add:
        with open(path, 'a', encoding='utf-8') as f:
            for t in to_add:
                f.write('\n' + t)
        changed.append((fname, to_add))

if changed:
    print('Updated wordlists:')
    for fn, adds in changed:
        print(f" - {fn}: added {', '.join(adds)}")
else:
    print('All wordlists already contain robots.txt and sitemap.xml')
