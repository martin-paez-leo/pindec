# pindec

API no oficial del INDEC para la extracción, filtrado y consulta de indicadores económicos y sociales de Argentina.

100% estática: cada request es un archivo JSON servido desde la CDN de Cloudflare Pages. Gratis, sin API key y sin cuotas de consumo por usuario.

## Endpoints

La API está desplegada en `https://pindec.dev` (base: `/v1`).

| Indicador | Descripción |
|---|---|
| `ipc` | Índice de Precios al Consumidor por región y clasificación (COICOP, categorías, bienes/servicios) |
| `cba-cbt` | Canasta Básica Alimentaria y Total para adulto equivalente y hogares |
| `emae` | Estimador Mensual de Actividad Económica: nivel general, desestacionalizado y por sector |
| `ica` | Intercambio Comercial Argentino: exportaciones, importaciones y saldo |

### Ejemplos

```bash
# Índices
curl https://pindec.dev/v1/ipc/
curl https://pindec.dev/v1/ipc/index.json

# Metadatos de vigencia (última publicación y período de cada indicador)
curl https://pindec.dev/v1/meta.json

# Datos
curl https://pindec.dev/v1/ipc/Nacional/2026/
curl https://pindec.dev/v1/cba-cbt/2026/
curl https://pindec.dev/v1/emae/2026/
curl https://pindec.dev/v1/ica/2026/

# Series específicas
curl https://pindec.dev/v1/ipc/Nacional/COICOP/0/2026/
```

Toda ruta admite el sufijo `index.json`. Las URLs limpias (`/v1/ipc/Nacional/2026/`) se resuelven por rewrites en el edge, y las variantes sin barra final (ej. `/v1/ipc/2020`) redirigen automáticamente (308) a la URL canónica.

Las rutas inexistentes bajo `/v1/` devuelven `404` con un cuerpo JSON en formato [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) (Problem Details):

```json
{
  "type": "https://pindec.dev/probs/not-found",
  "title": "Recurso no encontrado",
  "status": 404,
  "detail": "La ruta solicitada no existe en esta API. Los índices disponibles están en /v1/index.json.",
  "indice": "https://pindec.dev/v1/index.json"
}
```

El campo `type` es dereferenceable: apunta a la página de documentación del error (<https://pindec.dev/probs/not-found/>). Fuera de `/v1/` el `404` devuelve la página HTML de error del sitio.

## Uso local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -q
```

Para extraer los datos desde las fuentes del INDEC y regenerar `api/`:

```bash
cd src
python main.py
```

Solo descarga y procesa los indicadores cuyos archivos fuente cambiaron (comparando el `Last-Modified` del servidor con `config/metadata.json`). Luego regenera los índices y filtros de la API.

Para ver la landing localmente:

```bash
python3 scripts/serve_local.py 8090
```

El servidor emula los rewrites de Cloudflare Pages (`/v1/*/` → `index.json`), así que las URLs limpias funcionan igual que en producción. Con `python3 -m http.server` solo se sirve `index.json` de forma literal.

## Estructura

```
api/                  # Salida estática desplegada a Cloudflare Pages
  assets/             # Landing: HTML, CSS, JS, favicon y og-image
  v1/                 # Datos JSON generados (base /v1)
  404.html            # Página de error 404
  _headers            # Seguridad, CORS y control de caché
  _redirects          # Rewrites de URLs limpias (/v1/*/ → index.json) y redirects 308 sin barra final
.github/
  workflows/          # update.yml (semanal) + ci.yml (tests en PRs) + dependabot-auto-merge.yml
  dependabot.yml      # Actualizaciones automáticas de dependencias
config/
  config.json         # URLs y configuración de cada fuente
  metadata.json       # Último Last-Modified visto por indicador
scripts/
  serve_local.py       # Servidor local que emula los rewrites de Cloudflare Pages
  warm_cache.py       # Pre-calienta la caché del edge tras el deploy
src/
  main.py             # Orquestador: detecta cambios, extrae, guarda, genera API
  api.py              # Genera índices, filtros y metadatos de vigencia de la API
  checker.py          # Lógica de "needs_update" por Last-Modified
  utils.py            # Helpers (IO, merge, agrupación por año)
  extractors/         # Un módulo por indicador (ipc, cba-cbt, emae, ica)
tests/                # Suite de tests (pytest)
```

## Actualización automática

Un workflow de GitHub Actions (`Update indicators`) corre semanalmente (lunes 12:00 UTC) y se puede disparar manualmente:

1. Descarga las fuentes del INDEC si cambiaron.
2. Actualiza `api/v1/` y commitea los cambios en `main`.
3. Despliega a Cloudflare Pages.
4. Pre-calienta la caché del edge para los endpoints principales.

Además, un workflow de CI (`ci.yml`) corre los tests en cada pull request, y Dependabot abre PRs para mantener al día las dependencias (`pip` y GitHub Actions) — validados por ese mismo CI y auto-mergeados por `dependabot-auto-merge.yml`.

## Legal

- Datos extraídos del [INDEC](https://www.indec.gob.ar) (fuente oficial). Proyecto sin afiliación oficial con el INDEC.
- Basado en: Ley 17.622 y su Decreto Reglamentario 3110/70 (secreto estadístico protege solo microdatos individuales), Ley 27.275 (acceso a la información pública / reutilización), Ley 11.723 (los hechos y datos no son protegibles por derecho de autor) y Resolución INDEC 130/2025.
- Obligaciones al reutilizar: citar la fuente, no desnaturalizar los datos e indicar la fecha de actualización.

## Licencia

[Apache 2.0](LICENSE)
