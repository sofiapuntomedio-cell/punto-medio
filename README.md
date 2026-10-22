# Punto Medio — sitio web

Sitio de Sofía Leonhardt: arquitectura + bienestar. *Diseñar espacios para habitar(se).*

Es un sitio estático (HTML, CSS y JavaScript, sin dependencias), publicado en Netlify.

## Estructura

- `site/` — lo que se publica. Cada página es `site/<ruta>/index.html`.
  - `/` Inicio · `/espacio-exterior/` y sus 5 servicios · `/espacio-interior/` y sus 3 prácticas
  - `/sobre-mi/` · `/universo/` · `/proyectos/<proyecto>/`
  - `/comenzar/...` y `/consultar/...` — formularios
- `site/img/` — fotos en WebP, nombradas por su contenido (no renombrar).
- `tools/` — scripts usados para pasar el prototipo al sitio.
- `netlify.toml` — configuración de Netlify.

## Formularios

Todos usan Netlify Forms (`data-netlify="true"`). Cada uno tiene un nombre propio
(por ejemplo `consultar-reiki`). Los avisos por mail se configuran en Netlify:
*Project configuration → Notifications → Form submission notifications*, destino
sofia.puntomedio@gmail.com.

## Probar en la compu

```
python3 -m http.server 8000 --directory site
```
y abrir http://localhost:8000 (los formularios solo envían una vez publicados en Netlify).

## Versión en inglés

Las páginas en inglés (`site/en/...`) se generan a partir de las de español, no se editan a mano:

1. Las traducciones están en `i18n/en/*.json` (`"texto en español": "English text"`).
   Cambios de código puntuales (formato de fechas del calendario, etc.) en `i18n/en/_patches.json`.
2. `python3 tools/i18n.py extract` lista en `i18n/pendientes/` los textos que todavía no tienen traducción.
3. `python3 tools/i18n.py build` regenera todo `site/en/`, el selector ES / EN y el sitemap.

Cuando cambia un texto en español, hay que agregar su traducción y volver a correr `build`.
