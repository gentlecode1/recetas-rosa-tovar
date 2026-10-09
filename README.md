# Archivo de recetasrosatovar.com

Reconstrucción de **La cocina de Rosa Tovar** (`recetasrosatovar.com`), sitio desaparecido,
a partir de las capturas de Internet Archive.

## Estado del rescate

| | |
|---|---|
| Recetas recuperadas íntegras | **573** |
| Recetas conocidas pero perdidas | **148** (título + categorías + extracto) |
| Cobertura estimada | ~79 % de las ~670 originales |
| Imágenes recuperadas | 175 de ~692 referenciadas |
| Categorías | 34 |

Las 148 perdidas **no tienen ningún snapshot en Wayback**: el crawler nunca visitó esas URLs.
No es un fallo del scraping, es que no existen en el archivo. Vías ya descartadas:
feeds RSS históricos (solo contenían entradas de blog), `/recipes/feed/` y la API
`/wp-json/wp/v2/recipe` (nunca archivadas), archive.today (devuelve HTTP 451).

## Historia del dominio

- Contenido real archivado hasta **finales de 2022**
- Dominio **re-registrado el 2024-01-09 vía DropCatch.com** por un tercero
- Hoy apunta a Cloudflare sin web
- Conclusión: el dominio se perdió por caducidad, no por un fallo técnico.
  Publicar bajo `recetasrosatovar.com` exigiría comprárselo al nuevo titular.

## Estructura

```
raw/          573 páginas de receta originales de Wayback (materia prima, no tocar)
raw_idx/      387 páginas de índice archivadas (categorías, etiquetas, paginación)
raw_feed/     25 capturas del feed RSS
data/
  recipes.json       FUENTE DE VERDAD: 573 recetas estructuradas
  missing_meta.json  las 148 pendientes (título, categorías, extracto, miniatura)
  cdx_*.json         inventarios de Internet Archive
  img_map.json       referencia de imagen -> mejor variante archivada
downloads/images/    175 imágenes recuperadas (fuera de la web publicable)
site/                SITIO GENERADO, listo para publicar (47 MB)
```

## Pipeline

```
fetch.py           descarga el mejor snapshot de cada receta -> raw/
parse.py           raw/*.html -> data/recipes.json
fetch_images.py    recupera imágenes (con fallback a otra variante de tamaño) -> downloads/
extract_missing.py rescata metadatos de las 148 perdidas desde los índices
generate.py        data/*.json -> site/   (~2 segundos)
```

Regenerar la web entera:

```bash
python3 generate.py
```

Ver en local:

```bash
cd site && python3 -m http.server 8787   # http://localhost:8787
```

Publicar: subir la carpeta `site/` a Netlify, Cloudflare Pages o GitHub Pages.
Es HTML estático puro, sin base de datos ni backend.

## El sitio generado

759 páginas: 722 de receta (573 completas + 148 fichas pendientes), 35 de categoría,
portada, índice buscable y `/pendientes.html`. Búsqueda instantánea en el navegador,
filtro "ver solo las completas", y las pendientes marcadas con aviso y etiqueta naranja.

## Si algún día aparece contenido nuevo

Lo más probable es que el texto de las 148 esté en el ordenador de la autora, en sus
libros publicados (*3000 años de cocina española*, *Arroces*, *Masas*,
*100 recetas infalibles*) o en manos de quien le llevaba la web.
Para incorporarlo basta con editar `data/recipes.json` o `data/missing_meta.json`
y volver a lanzar `generate.py`.

## Derechos

El contenido es obra de Rosa Tovar. Este archivo es una reconstrucción para
preservación; publicarlo requiere su permiso o el de sus herederos.
