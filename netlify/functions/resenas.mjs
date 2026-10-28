// Testimonios del sitio: se publican apenas la persona los envía y Sofía puede eliminarlos
// desde el link que le llega por mail.
//
//   GET  /api/resenas                 -> lista de testimonios publicados (JSON)
//   POST /api/resenas                 -> publica un testimonio nuevo (JSON)
//   GET  /api/resenas/borrar?id&t     -> página para confirmar la eliminación
//   POST /api/resenas/borrar?id&t     -> elimina el testimonio
//
// Los testimonios se guardan en Netlify Blobs (almacenamiento incluido en Netlify, sin costo extra).
import { getStore } from '@netlify/blobs';
import { createHmac, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';

const SERVICIOS = [
  'Sesión de Reiki', 'Registros Akáshicos', 'Péndulo Hebreo', 'Limpieza energética',
  'Diseño de Interiores Holístico', 'Paisajismo', 'Arquitectura Integral', 'Bienestar Empresarial', 'Otro',
  // versión en inglés
  'Reiki session', 'Akashic Records', 'Hebrew Pendulum', 'Energy cleansing',
  'Holistic Interior Design', 'Landscape Design', 'Integral Architecture', 'Corporate Wellbeing', 'Other',
];
const MAX_RESENAS = 300;

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const limpiar = (s, max) => String(s ?? '').replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '').trim().slice(0, max);

async function clave(store) {
  if (process.env.RESENAS_CLAVE) return process.env.RESENAS_CLAVE;
  let k = await store.get('_clave');
  if (!k) {
    k = randomBytes(32).toString('hex');
    await store.set('_clave', k);
  }
  return k;
}

const firma = (k, id) => createHmac('sha256', k).update(id).digest('hex').slice(0, 40);
function firmaOk(k, id, t) {
  const a = Buffer.from(firma(k, id));
  const b = Buffer.from(String(t || ''));
  return a.length === b.length && timingSafeEqual(a, b);
}

async function leer(store) {
  return (await store.get('lista', { type: 'json' })) || [];
}

function pagina(titulo, cuerpo) {
  return new Response(
    `<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>${esc(titulo)} — Punto Medio</title>
<style>
  body{margin:0;background:#F9F9F6;color:#252A28;font:16px/1.6 "Jost",-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;}
  main{max-width:560px;margin:8vh auto;padding:0 20px;}
  h1{font-family:"Playfair Display",Georgia,serif;font-weight:600;font-size:1.8rem;line-height:1.2;margin:0 0 1rem;}
  blockquote{margin:1.2rem 0;padding:1.2rem 1.4rem;background:#fff;border:1px solid #D9CFBC;border-radius:12px;font-family:Georgia,serif;font-style:italic;}
  .autor{display:block;margin-top:.7rem;font-style:normal;font-family:inherit;font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;color:#5B6259;}
  button,a.btn{display:inline-block;font:600 .8rem/1.2 inherit;letter-spacing:.06em;text-transform:uppercase;padding:.95em 2em;border-radius:999px;border:0;cursor:pointer;text-decoration:none;}
  button{background:#C96342;color:#fff;} a.btn{background:#596447;color:#fff;}
  p.nota{color:#5B6259;font-size:.9rem;}
</style></head><body><main>${cuerpo}</main></body></html>`,
    { headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' } }
  );
}

const citar = (r) =>
  `<blockquote>“${esc(r.texto)}”<span class="autor">${esc(r.nombre)}${r.servicio ? ' · ' + esc(r.servicio) : ''}</span></blockquote>`;

async function borrar(req, store, url) {
  const id = url.searchParams.get('id') || '';
  const t = url.searchParams.get('t') || '';
  const k = await clave(store);
  if (!id || !firmaOk(k, id, t)) {
    return pagina('Link no válido', '<h1>Este link no es válido.</h1><p class="nota">Revisá que hayas abierto el link completo que llegó por mail.</p>');
  }
  const lista = await leer(store);
  const r = lista.find((x) => x.id === id);
  if (!r) {
    return pagina('Ya no está publicado', '<h1>Este testimonio ya no está publicado.</h1><p class="nota">Puede que ya lo hayas eliminado antes.</p><p><a class="btn" href="/#experiencias-huella">Ver testimonios</a></p>');
  }
  if (req.method === 'POST') {
    await store.setJSON('lista', lista.filter((x) => x.id !== id));
    return pagina('Testimonio eliminado', `<h1>Listo, el testimonio fue eliminado.</h1>${citar(r)}<p class="nota">Ya no aparece en el sitio.</p><p><a class="btn" href="/#experiencias-huella">Ver testimonios</a></p>`);
  }
  return pagina(
    'Eliminar testimonio',
    `<h1>¿Eliminar este testimonio del sitio?</h1>${citar(r)}
     <form method="POST"><button type="submit">Sí, eliminarlo</button></form>
     <p class="nota">Si no querés eliminarlo, simplemente cerrá esta página.</p>`
  );
}

async function publicar(req, store, url) {
  let d;
  try {
    d = await req.json();
  } catch {
    return json({ ok: false, error: 'datos' }, 400);
  }
  // campo trampa: las personas no lo ven, los robots lo completan
  if (d._honey) return json({ ok: true, resena: null });
  const nombre = limpiar(d.nombre, 60);
  const texto = limpiar(d.texto, 1500);
  let servicio = limpiar(d.servicio, 60);
  if (servicio && !SERVICIOS.includes(servicio)) servicio = '';
  if (!nombre || texto.length < 10 || d.autorizo !== true) return json({ ok: false, error: 'datos' }, 400);
  if (/https?:\/\/|www\./i.test(texto + ' ' + nombre)) return json({ ok: false, error: 'links' }, 400);

  const lista = await leer(store);
  if (lista.some((x) => x.texto === texto)) return json({ ok: false, error: 'repetido' }, 409);
  const r = { id: randomUUID(), nombre, servicio, texto, fecha: new Date().toISOString() };
  lista.unshift(r);
  await store.setJSON('lista', lista.slice(0, MAX_RESENAS));

  const k = await clave(store);
  const link = `${url.origin}/api/resenas/borrar?id=${r.id}&t=${firma(k, r.id)}`;
  return json({ ok: true, resena: r, eliminar: link });
}

export default async (req) => {
  const url = new URL(req.url);
  const store = getStore({ name: 'resenas', consistency: 'strong' });
  if (url.pathname.endsWith('/borrar')) return borrar(req, store, url);
  if (req.method === 'POST') return publicar(req, store, url);
  if (req.method === 'GET') {
    const lista = await leer(store);
    return json({ resenas: lista.map(({ id, nombre, servicio, texto, fecha }) => ({ id, nombre, servicio, texto, fecha })) });
  }
  return json({ ok: false }, 405);
};

export const config = { path: ['/api/resenas', '/api/resenas/borrar'] };
