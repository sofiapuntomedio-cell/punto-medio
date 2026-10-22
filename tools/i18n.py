"""Versión en inglés del sitio.

  python3 tools/i18n.py extract   -> i18n/pendientes/*.txt con los textos aún sin traducir, por página
  python3 tools/i18n.py build     -> genera site/en/... a partir de site/ (español) + i18n/en/*.json

Las traducciones viven en i18n/en/*.json como {"texto en español": "English text"}.
Solo se reemplaza lo que está en el diccionario: un texto sin traducción queda igual
(y el build avisa). Los nombres de campos de formularios no se traducen, así las
consultas siguen llegando con los mismos campos.
"""
import glob, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
I18N = os.path.join(ROOT, 'i18n')
DOMAIN = 'https://sofia-puntomedio.com.ar'
ATTRS = ('alt', 'aria-label', 'title', 'placeholder', 'content', 'data-label', 'data-caption', 'data-title', 'data-desc')

# orden de las páginas para la extracción (las primeras definen el contexto)
ORDER = ['', 'espacio-exterior', 'espacio-interior', 'sobre-mi', 'universo']

TOKEN = re.compile(r'(<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->|<[^>]+>)', re.S | re.I)
ATTR_RE = re.compile(r'(\s(?:' + '|'.join(ATTRS) + r')=")([^"]*)(")')
JS_STR = re.compile(r"""(')((?:[^'\\\n]|\\.)*)(')|(")((?:[^"\\\n]|\\.)*)(")""")
LETTERS = re.compile(r'[A-Za-zÁÉÍÓÚáéíóúñÑ]{2}')


def es_pages():
    pages = []
    for p in glob.glob(os.path.join(SITE, '**', 'index.html'), recursive=True):
        rel = os.path.relpath(os.path.dirname(p), SITE)
        rel = '' if rel == '.' else rel
        if rel == 'en' or rel.startswith('en' + os.sep):
            continue
        pages.append(rel.replace(os.sep, '/'))
    key = lambda r: (ORDER.index(r) if r in ORDER else len(ORDER), r)
    return sorted(pages, key=key)


def norm(t):
    return ' '.join(html.unescape(t).split())


def looks_like_text(t):
    return bool(LETTERS.search(t)) and not t.startswith(('http', '/', '#', 'data:'))


def js_candidates(code):
    out = []
    for m in JS_STR.finditer(code):
        s = m.group(2) if m.group(1) else m.group(5)
        if s is None:
            continue
        if (' ' in s or re.search('[áéíóúñ¿¡…]', s)) and looks_like_text(s) and not re.search(r'[{};<>]|querySelector|\[name', s):
            out.append(s)
    return out


def collect(page_html):
    """Textos traducibles de una página, en orden."""
    found = []
    for part in TOKEN.split(page_html):
        if not part:
            continue
        low = part[:7].lower()
        if low.startswith('<script'):
            found += [('js', s) for s in js_candidates(part)]
        elif low.startswith('<style') or part.startswith('<!--'):
            continue
        elif part.startswith('<'):
            for m in ATTR_RE.finditer(part):
                v = norm(m.group(2))
                if v and looks_like_text(v):
                    found.append(('attr', v))
        else:
            v = norm(part)
            if v and LETTERS.search(v):
                found.append(('text', v))
    return found


PATTERNS = [
    (r'^Ver (.+) en tamaño grande$', 'View {0} at full size'),
    (r'^Ver foto: (.+)$', 'View photo: {0}'),
    (r'^Ver foto de antes (\d+) en tamaño grande$', 'View before photo {0} at full size'),
    (r'^Antes de la intervención, vista (\d+)$', 'Before the intervention, view {0}'),
]


def lookup(v, d):
    """Traducción exacta o, si no hay, por patrón ("Ver X en tamaño grande", etc.)."""
    if v in d:
        return d[v]
    for pat, tpl in PATTERNS:
        m = re.match(pat, v)
        if m:
            parts = [d.get(g, g if g.isdigit() else None) for g in m.groups()]
            if None not in parts:
                t = tpl.format(*parts)
                return t[0].upper() + t[1:]
    return None


def load_dict():
    d = {}
    for f in sorted(glob.glob(os.path.join(I18N, 'en', '*.json'))):
        if os.path.basename(f).startswith('_'):
            continue
        d.update(json.load(open(f, encoding='utf8')))
    return d


def extract():
    done = load_dict()
    seen = set(done)
    out_dir = os.path.join(I18N, 'pendientes')
    os.makedirs(out_dir, exist_ok=True)
    for f in glob.glob(os.path.join(out_dir, '*.txt')):
        os.remove(f)
    total = 0
    for rel in es_pages():
        src = open(os.path.join(SITE, rel, 'index.html'), encoding='utf8').read()
        new = []
        for kind, t in collect(src):
            if t not in seen and lookup(t, done) is None:
                seen.add(t)
                new.append(f'[{kind}] {t}')
        if new:
            name = rel.replace('/', '__') or 'inicio'
            open(os.path.join(out_dir, name + '.txt'), 'w', encoding='utf8').write('\n'.join(new) + '\n')
            total += len(new)
            print(f'{name:55s} {len(new)}')
    print('pendientes:', total)


def localize_links(s):
    pages = set('/' + p + '/' if p else '/' for p in es_pages())
    def rep(m):
        url, frag = m.group(2), m.group(3) or ''
        if url in pages:
            return f'{m.group(1)}/en{url}{frag}"'
        return m.group(0)
    return re.sub(r'(href=")(/[^"#?]*)(#[^"]*)?"', rep, s)


def translate_page(src, d, missing):
    # valores de formularios: el JavaScript los compara, así que no se traducen en el código
    form_values = set(html.unescape(v) for v in re.findall(r'\svalue="([^"]*)"', src))
    parts = TOKEN.split(src)
    out = []
    for part in parts:
        low = part[:7].lower()
        if low.startswith('<script'):
            def jrep(m):
                q = m.group(1) or m.group(4)
                s = m.group(2) if m.group(1) else m.group(5)
                t = d.get(s)
                if t is None or s in form_values:
                    return m.group(0)
                # la traducción ya viene como contenido de literal JS (\n, \" se respetan)
                return q + re.sub(r"(?<!\\)" + re.escape(q), '\\\\' + q, t) + q
            out.append(JS_STR.sub(jrep, part))
        elif low.startswith('<style') or part.startswith('<!--'):
            out.append(part)
        elif part.startswith('<'):
            def arep(m):
                v = norm(m.group(2))
                t = lookup(v, d) if v else None
                if t is not None:
                    return m.group(1) + html.escape(t, quote=True) + m.group(3)
                if v and looks_like_text(v) and m.group(1).strip().startswith(('alt', 'aria', 'title', 'placeholder')):
                    missing.add(v)
                return m.group(0)
            out.append(ATTR_RE.sub(arep, part))
        else:
            v = norm(part)
            if v and LETTERS.search(v):
                t = lookup(v, d)
                if t is not None:
                    lead = part[:len(part) - len(part.lstrip())]
                    trail = part[len(part.rstrip()):]
                    out.append(lead + html.escape(t, quote=False) + trail)
                    continue
                missing.add(v)
            out.append(part)
    return ''.join(out)


SWITCH_CSS = '''<style id="lang-switch-css">
  .lang-switch{display:inline-flex;align-items:center;gap:.35em;font-family:var(--font-body,inherit);font-size:.74rem;font-weight:600;letter-spacing:.08em;white-space:nowrap;}
  .lang-switch a,.lang-switch span{text-decoration:none;color:var(--ink-soft,#5B6259);border:none!important;padding:0!important;}
  .lang-switch a:hover{color:var(--terracota,#C96342);}
  .lang-switch .on{color:var(--ink,#252A28);}
  .lang-switch i{font-style:normal;opacity:.45;}
  @media (max-width:900px){.lang-switch{font-size:.95rem;margin-top:.4rem;}}
</style>
'''


def switch_html(route, lang):
    es, en = route, '/en' + route
    if lang == 'es':
        return f'<span class="lang-switch" aria-label="Idioma"><span class="on" aria-current="true">ES</span><i>/</i><a href="{en}" hreflang="en" lang="en">EN</a></span>'
    return f'<span class="lang-switch" aria-label="Language"><a href="{es}" hreflang="es" lang="es">ES</a><i>/</i><span class="on" aria-current="true">EN</span></span>'


def add_switch(s, route, lang):
    s = re.sub(r'<span class="lang-switch".*?</(?:a|span)></span>', '', s, flags=re.S)
    s = s.replace(SWITCH_CSS, '')
    sw = switch_html(route, lang)
    if '<nav class="main-nav"' in s or re.search(r'<nav\b[^>]*class="[^"]*main-nav', s):
        s = re.sub(r'(<nav\b[^>]*main-nav[^>]*>.*?)(</nav>)', lambda m: m.group(1) + sw + m.group(2), s, count=1, flags=re.S)
    else:
        # páginas sin menú (formularios): arriba a la derecha
        s = s.replace('<body>\n', '<body>\n<div style="position:absolute;top:14px;right:16px;z-index:50">' + sw + '</div>\n', 1)
    return s.replace('</head>', SWITCH_CSS + '</head>', 1)


def add_alternates(s, route):
    s = re.sub(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n', '', s)
    alt = (f'<link rel="alternate" hreflang="es" href="{DOMAIN}{route}">\n'
           f'<link rel="alternate" hreflang="en" href="{DOMAIN}/en{route}">\n'
           f'<link rel="alternate" hreflang="x-default" href="{DOMAIN}{route}">\n')
    return s.replace('<link rel="icon"', alt + '<link rel="icon"', 1)


def apply_patches(s, route, patches):
    """Cambios de código puntuales para el inglés (formato de fechas, etc.)."""
    for old, new in patches.get(route, []) + patches.get('*', []):
        if old in s:
            s = s.replace(old, new)
        elif route in patches:
            print(f'  ! parche no encontrado en {route}: {old[:70]}')
    return s


def build():
    d = load_dict()
    pf = os.path.join(I18N, 'en', '_patches.json')
    patches = json.load(open(pf, encoding='utf8')) if os.path.exists(pf) else {}
    missing = set()
    for rel in es_pages():
        route = '/' + rel + '/' if rel else '/'
        path = os.path.join(SITE, rel, 'index.html')
        es = open(path, encoding='utf8').read()
        es = add_alternates(add_switch(es, route, 'es'), route)
        open(path, 'w', encoding='utf8').write(es)

        en = translate_page(es, d, missing)
        en = apply_patches(en, route, patches)
        en = add_switch(en, route, 'en')
        en = en.replace('<html lang="es">', '<html lang="en">', 1)
        en = re.sub(r'(rel="canonical" href="' + re.escape(DOMAIN) + r')(/[^"]*)"', lambda m: f'{m.group(1)}/en{m.group(2)}"', en, count=1)
        en = re.sub(r'(property="og:url" content="' + re.escape(DOMAIN) + r')(/[^"]*)"', lambda m: f'{m.group(1)}/en{m.group(2)}"', en, count=1)
        en = en.replace('<meta property="og:type"', '<meta property="og:locale" content="en_US">\n<meta property="og:type"', 1)
        en = localize_links(en)
        out = os.path.join(SITE, 'en', rel)
        os.makedirs(out, exist_ok=True)
        open(os.path.join(out, 'index.html'), 'w', encoding='utf8').write(en)
    # sitemap con ambos idiomas
    urls = [('/' + r + '/' if r else '/') for r in es_pages() if not r.startswith(('comenzar', 'consultar'))]
    body = ''.join(f'  <url><loc>{DOMAIN}{p}{u}</loc></url>\n' for p in ('', '/en') for u in urls)
    open(os.path.join(SITE, 'sitemap.xml'), 'w', encoding='utf8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + body + '</urlset>\n')
    print('páginas en inglés:', len(es_pages()))
    if missing:
        print(f'\nSIN TRADUCIR ({len(missing)}):')
        for m in sorted(missing):
            print('  ', m[:120])


if __name__ == '__main__':
    {'extract': extract, 'build': build}[sys.argv[1]]()
