"""Convierte las páginas del prototipo (artifacts) en un sitio estático.

- Saca las fotos embebidas (base64) a archivos WebP optimizados en site/img/
- Reemplaza los links entre artifacts por rutas reales del sitio
- Ordena el <head> (charset, viewport, título, fuentes) en cada página
Uso: python3 tools/convert.py <carpeta_artifacts> <carpeta_salida>
"""
import base64, hashlib, io, os, re, sys
from PIL import Image

SRC, OUT = sys.argv[1], sys.argv[2]
IMG_DIR = os.path.join(OUT, 'img')
os.makedirs(IMG_DIR, exist_ok=True)

# uuid del artifact -> ruta en el sitio
PAGES = {
    '85c793f8-4617-41aa-864c-a636c1e96245': '/',
    'c4492af2-31f0-4b23-bd86-c8a8ae17f0d6': '/espacio-exterior/',
    '2a08f61a-c3e3-4a28-a91c-be64efc63af0': '/espacio-interior/',
    'b851e4c0-f620-49ce-80b9-ac60eadb62c4': '/espacio-exterior/arquitectura-integral/',
    'ffc3a1f2-cf93-4353-926d-5264b36eca66': '/espacio-exterior/paisajismo/',
    'a183580a-7094-49c5-80b6-0346c8ebad42': '/espacio-exterior/diseno-de-interiores-holistico/',
    'dc32e7d3-85fd-48d9-843c-f88c1772d0ab': '/espacio-exterior/bienestar-empresarial/',
    'a7f33e8a-d98a-453e-84a8-4fd429bf8f14': '/espacio-exterior/limpieza-y-armonizacion-energetica/',
    '63201774-a520-446b-9b85-f8743c419de9': '/espacio-interior/reiki/',
    '87be60ef-b7e4-4301-8eed-5aa118562ff7': '/espacio-interior/registros-akashicos/',
    '1bac5e59-328f-48d7-8738-fce78b478d68': '/espacio-interior/pendulo-hebreo/',
    '14e337d2-92b3-4a49-acdb-2a88ad37bd8e': '/sobre-mi/',
    'ba06e3e3-caa5-4cbf-9479-4ad6539ac470': '/universo/',
    '3b3d7cd3-5e49-49c9-b76f-fea5e651269f': '/proyectos/ubc/',
    'dbef918f-f9d7-4345-a6f3-fe1e83c8849a': '/proyectos/co/',
    'a813802f-1639-43f3-96f0-69c019224471': '/proyectos/nl/',
    '5769aa9c-eb0b-4366-8f93-8a1c7ec89a4d': '/proyectos/mc/',
    'da12e6eb-6f74-4561-8f7d-acc8f8dfe59f': '/proyectos/jca-gm/',
    '5502fa68-71e9-44d7-b671-2da3a3ff9352': '/proyectos/paisajes-de-aprendizaje/',
    'a65223da-c554-4f2d-9666-5c70b5be32a3': '/proyectos/ingreso-parque-de-mayo/',
    'f341c68d-694c-4a08-ade7-c041f1bf4451': '/comenzar/',
    '0d0251c3-1924-4af6-9506-7f5399f72d36': '/comenzar/arquitectura-integral/',
    '00c24147-b27c-4cea-b364-3b3f49f36540': '/comenzar/paisajismo/',
    '00af1c15-e3b6-4c09-95ac-ffaf0452b8e3': '/comenzar/diseno-de-interiores/',
    '72c04d26-b97f-4b27-99d6-6a56bcc1c2e1': '/comenzar/limpieza-energetica/',
    '4924572a-4640-413c-b66b-49cddb6449e2': '/comenzar/bienestar-empresarial/',
    '4cd99e4d-60c8-40ac-b3f9-38b3da987abd': '/comenzar/bienestar-esencial/',
    'e74fb68b-7285-4a9f-96ff-2ab9310a9ddd': '/comenzar/bienestar-integral/',
    '4e820f4b-28e2-4e46-a7fd-0b122d3363f3': '/comenzar/bienestar-premium/',
    'b4a84de9-f378-464c-b8d2-c82c96a090a9': '/consultar/reiki/',
    'e3cb048b-14aa-4687-b6a6-6ae599f1414d': '/consultar/registros-akashicos/',
    'bd354899-43ab-4fb9-bcd6-031324aa4135': '/consultar/pendulo-hebreo/',
}
# id corto del link publicado -> ruta
SHORT = {
    'HX9Bw99kaTJZWU1Bj1REJQ': '/', '3abihd7TXGw39Ejn1uRBbs': '/sobre-mi/', 'PyLn7ojkBKmP3aNogusyzw': '/universo/',
    'REpLQBcvuQbHnchCvU1Cb7': '/espacio-exterior/', '6C4PNr2QRPTn2T8t3WNMef': '/espacio-interior/',
    'Pm7gV72361XWgYJ25WM9sZ': '/espacio-exterior/arquitectura-integral/',
    'YaoiXY2HRVwqk1pA7Kqdhf': '/espacio-exterior/paisajismo/',
    'LwmhTG9uqLTjTQEqyncVsw': '/espacio-exterior/diseno-de-interiores-holistico/',
    'UC5qVFhfGKPevP24muo3rS': '/espacio-exterior/bienestar-empresarial/',
    'MjsgT6wLD4yuojLbJnFSqH': '/espacio-exterior/limpieza-y-armonizacion-energetica/',
    'DEwnBCqPzYLBQi7Fay2Y8p': '/espacio-interior/reiki/', 'HmD4feFKvPAXGoJEda1Tgi': '/espacio-interior/registros-akashicos/',
    '4RCXQfuUqfuKN4JUrGoPi7': '/espacio-interior/pendulo-hebreo/',
    '8KHSJ7i2UkXbpsdV9dLbot': '/proyectos/ubc/', 'UACa7gsgrNYiAaSZ4xsXk5': '/proyectos/co/',
    'Mkn2EuhHvSv4xcCwNum58C': '/proyectos/nl/', 'Bo4MUv23ufL962RiWtmKnc': '/proyectos/mc/',
    'Tvs6ySBjkVAn36GNTeHkDC': '/proyectos/jca-gm/', 'BVrvXBHeSCWWitpHaqf2zu': '/proyectos/paisajes-de-aprendizaje/',
    'MYCryWhVVoFz6KAT3HTdw8': '/proyectos/ingreso-parque-de-mayo/',
    'X3EBz8ufGcyN2a4Wi1XWvk': '/comenzar/', '2cAygsmpwcT7w2BePT8LbX': '/comenzar/arquitectura-integral/',
    '16SDB6BNpx7aJSME2SE7uh': '/comenzar/paisajismo/', '15u9L36w4PgyE1CqZBeQD8': '/comenzar/diseno-de-interiores/',
    'FArm8SSy2tgtppAoA84n16': '/comenzar/limpieza-energetica/', 'A2rFFk3GHTpVMfkVLmmtpH': '/comenzar/bienestar-empresarial/',
    'AVQbt3oGZnzAeZ1Kh3zTek': '/comenzar/bienestar-esencial/', 'VZfzZaALA1xqxVbUYcVoSC': '/comenzar/bienestar-integral/',
    'AhHKtH1MGyHzeWW9hwfhxE': '/comenzar/bienestar-premium/',
    'PJtHvsPF8qvZbh4nTcSmdz': '/consultar/reiki/', 'V8UUFULpZHCEuVWLEQpkAG': '/consultar/registros-akashicos/',
    'QN8GBfwFmegRyhEZgaGMYQ': '/consultar/pendulo-hebreo/',
}
LINKMAP = {**PAGES, **SHORT}

DATA_RE = re.compile(r'data:image/(jpeg|jpg|png|webp|gif);base64,([A-Za-z0-9+/=]+)')
seen = {}
stats = {'in': 0, 'out': 0}

def save_image(mime, b64):
    raw = base64.b64decode(b64)
    h = hashlib.sha1(raw).hexdigest()[:12]
    if h in seen:
        return seen[h]
    im = Image.open(io.BytesIO(raw))
    im.load()
    has_alpha = im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info)
    im = im.convert('RGBA' if has_alpha else 'RGB')
    if max(im.size) > 2000:
        im.thumbnail((2000, 2000), Image.LANCZOS)
    path = os.path.join(IMG_DIR, h + '.webp')
    im.save(path, 'WEBP', quality=80, method=6)
    stats['in'] += len(raw); stats['out'] += os.path.getsize(path)
    seen[h] = f'/img/{h}.webp'
    return seen[h]

def fix_links(s):
    def rep(m):
        target = LINKMAP.get(m.group(1))
        if not target:
            print('  link sin destino:', m.group(1)); return m.group(0)
        return target
    return re.sub(r'https://claude\.ai/(?:code/)?artifact/([A-Za-z0-9-]+)', rep, s)

HEAD_TPL = '''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,600;1,500;1,600&family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{base}</style>
</head>
<body>
'''

for uuid, route in PAGES.items():
    s = open(os.path.join(SRC, uuid, 'index.html'), encoding='utf8').read()
    # quitar el envoltorio que agrega la publicación del artifact
    wrap = re.compile(r'<!doctype html><html><head><meta charset=utf8>.*?<style>(.*?)</style></head><body>', re.S | re.I)
    m = wrap.search(s)
    base = m.group(1) if m else ''
    body = wrap.sub('', s)  # puede estar repetido por publicaciones sucesivas
    body = body.replace('</body></html>', '')
    t = re.search(r'<title>(.*?)</title>', body, re.S)
    title = t.group(1).strip() if t else 'Punto Medio'
    body = re.sub(r'<title>.*?</title>\s*', '', body, count=1, flags=re.S)
    body = re.sub(r'<meta charset="UTF-8">\s*', '', body, count=1, flags=re.I)
    for pat in (r'<link rel="preconnect" href="https://fonts\.googleapis\.com">\s*',
                r'<link rel="preconnect" href="https://fonts\.gstatic\.com" crossorigin>\s*',
                r'<link href="https://fonts\.googleapis\.com/css2[^>]*>\s*'):
        body = re.sub(pat, '', body)
    body = DATA_RE.sub(lambda mm: save_image(mm.group(1), mm.group(2)), body)
    body = fix_links(body)
    html = HEAD_TPL.format(title=title, base=base) + body.lstrip() + '\n</body>\n</html>\n'
    out_dir = os.path.join(OUT, route.strip('/'))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf8') as f:
        f.write(html)
    print(f'{route:58s} {len(html)//1024:6d} KB  ({title})')

print(f'\nFotos: {len(seen)} únicas, {stats["in"]/1e6:.1f} MB -> {stats["out"]/1e6:.1f} MB')
