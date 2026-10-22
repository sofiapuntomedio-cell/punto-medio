"""Conecta los formularios del sitio a Netlify Forms (envío real, aviso por mail).

Cada formulario recibe un nombre propio, así los avisos llegan separados
("comenzar-reiki", "voto-talleres", etc.). Uso: python3 tools/netlify_forms.py site
"""
import glob, os, re, sys

SITE = sys.argv[1]
FETCH_OLD = re.compile(
    r"fetch\('https://formsubmit\.co/ajax/[^']+',\s*\{\s*method:\s*'POST',\s*headers:\s*\{\s*'Accept':\s*'application/json'\s*\},\s*body:\s*data\s*\}\)",
    re.S)
FETCH_NEW = ("fetch('/', { method: 'POST', "
             "headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, "
             "body: new URLSearchParams(data).toString() })")

def form_name(path):
    rel = os.path.relpath(os.path.dirname(path), SITE).replace(os.sep, '-')
    return {'universo': 'voto-talleres', 'comenzar': 'comenzar-un-proceso'}.get(rel, rel)

changed = 0
for path in glob.glob(os.path.join(SITE, '**', 'index.html'), recursive=True):
    s = open(path, encoding='utf8').read()
    if 'formsubmit.co' not in s:
        continue
    name = form_name(path)
    m = re.search(r'<form class="(proceso-form|voto-form)" id="(procesoForm|votoForm)"([^>]*)>', s)
    assert m, path
    new_tag = (f'<form class="{m.group(1)}" id="{m.group(2)}" name="{name}" method="POST" '
               f'data-netlify="true" netlify-honeypot="_honey"{m.group(3)}>'
               f'\n      <input type="hidden" name="form-name" value="{name}">')
    s = s[:m.start()] + new_tag + s[m.end():]
    s, n = FETCH_OLD.subn(FETCH_NEW, s)
    assert n == 1, (path, n)
    # Netlify responde con una página, no con JSON
    s = s.replace("if(!res.ok) throw new Error('bad response');\n        return res.json();",
                  "if(!res.ok) throw new Error('bad response');\n        return res;")
    assert 'res.json()' not in s, path
    open(path, 'w', encoding='utf8').write(s)
    changed += 1
    print(f'{name:40s} {os.path.relpath(path, SITE)}')
print(changed, 'formularios conectados')
