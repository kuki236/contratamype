# Web app y API de ContrataMYPE

> **Alcance:** Fase 4 completa (búsqueda, detalle, estados vacíos, checklist/PDF y E2E con datos sembrados) y la parte visible de Fase 5 (explicador por plantilla, citas de campos y disclaimer). El adaptador Gemini queda preparado como punto de extensión, no implementado.
>
> **Ruta local del producto:** Next.js en `web/` → API FastAPI read-only en `api/` → DuckDB del pipeline en `data/processed/contratamype.duckdb`.

## 1. Arquitectura

```text
Navegador
   │  HTML/RSC
   ▼
web/  Next.js 16 (App Router, TypeScript, Tailwind 4)
   │  fetch server-side, cache: "no-store"
   ▼
api/  FastAPI + uvicorn (solo lectura)
   │  duckdb.connect(..., read_only=True), una conexión por request
   ▼
data/processed/contratamype.duckdb  (tenders, awards, contracts, buyers, suppliers)
```

- La web es Server Components por defecto. Solo `PrintButton` es cliente.
- La API no escribe ni recalcula reglas de negocio. `mype_fit` se lee tal como lo dejó el pipeline.
- El PDF se genera en el servidor con `pdf-lib`; no usa servicios externos ni requiere API key.
- El explicador es una plantilla en español sobre campos oficiales. Cada punto cita la tabla/campo de origen.
- La fuente y el disclaimer aparecen en la ficha, el checklist y el PDF: **heurística de compatibilidad MYPE, no elegibilidad legal**.

## 2. Requisitos

- Python 3.13 con el entorno `.venv` del repo.
- Node.js 24 y npm.
- La base DuckDB generada por el pipeline (`python -m contratamype run --year 2025`).
- Navegadores de Playwright (`npx playwright install chromium`) para el E2E.

## 3. Puesta en marcha

Desde la raíz del repo:

```powershell
# Dependencias Python (incluye fastapi y uvicorn; ya declaradas en pyproject.toml)
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# API en http://127.0.0.1:8000
.\.venv\Scripts\python.exe -m uvicorn api.app:app --port 8000
```

En otra terminal:

```powershell
cd web
npm install
Copy-Item .env.example .env.local
npm run dev
```

Abrir `http://localhost:3000`. Documentación interactiva de la API: `http://127.0.0.1:8000/docs`.

Producción local:

```powershell
cd web
npm run build
npm run start
```

La build no necesita la API encendida: las páginas que consultan datos son dinámicas (`force-dynamic`).

## 4. Variables de entorno

| Variable | Proceso | Default | Uso |
|---|---|---|---|
| `CONTRATAMYPE_DB` | API | `data/processed/contratamype.duckdb` | Ruta de la DuckDB. Se abre en modo `read_only`. Los tests la apuntan al fixture sembrado. |
| `CONTRATAMYPE_API_URL` | Web | `http://127.0.0.1:8000` | Base URL que usan los Server Components y la ruta del PDF. |
| `CONTRATAMYPE_EXPLAINER` | Web | `template` | Selección de explicador. Solo `template` existe; un valor desconocido (por ejemplo `gemini`) cae a la plantilla. No hay llamada de red ni API key. |
| `CONTRATAMYPE_API_PORT` | Playwright | `8010` | Puerto del `webServer` de la API en tests. |
| `CONTRATAMYPE_WEB_PORT` | Playwright | `3100` | Puerto del `webServer` de Next.js en tests. |
| `CONTRATAMYPE_TEST_DB` | Playwright | `%TEMP%\contratamype-e2e\contratamype-test.duckdb` | Ruta alternativa del fixture determinista. |

No hay secretos en el repo. `.env.local` está ignorado por Git; `.env.example` documenta las variables.

## 5. API

Base: `http://127.0.0.1:8000`. Todo es `GET`, sin autenticación y sin escritura.

| Endpoint | Parámetros | Respuesta |
|---|---|---|
| `/health` | — | `{ "status": "ok" }`; 503 si la DuckDB no está disponible. |
| `/meta` | `year` (default 2025) | Departamentos, categorías, métodos, estados y rango de montos positivos de la cohorte. |
| `/opportunities` | `q`, `department`, `category`, `method`, `min_amount`, `max_amount`, `status`, `year` (2025), `mype_only` (false), `page` (1), `page_size` (20, máx. 100) | `items`, `total`, `page`, `page_size`, `pages`. Búsqueda por título, descripción, entidad u OCID. Orden: publicación descendente, OCID. |
| `/opportunities/{ocid}` | — | Ficha con `buyer`, `awards`, `contracts` y `data_quality` (descripción faltante, monto 0, inicio=fin, awards/contratos ausentes, proveedor o adjudicación sin vínculo). 404 si no existe. |
| `/stats` | `year` (2025) | Totales, MYPE, monto 0, descripción faltante, inicio=fin, mediana, y agregados por departamento, categoría y método. |
| `/checklist/{ocid}` | — | Checklist JSON generado solo con campos oficiales: proceso, fuente, 9 pasos, advertencias y disclaimer. 404 si no existe. |

Decisiones de contrato:

- `mype_only` en la API es `false` por defecto para permitir explorar toda la cohorte. La UI arranca con **Solo compatibles MYPE**; el valor viaja explícito en la URL (`mype_only=1|0`).
- Los montos viajan como números JSON para presentación. En DuckDB son `DECIMAL(18,2)`; a esta escala (máximo ~S/ 1,134 millones) los centavos se representan sin pérdida en un double.
- La API no reimplementa el umbral, las categorías objetivo ni los departamentos objetivo de la regla MYPE. Solo expone `tenders.mype_fit`.
- `amount_pen = 0` se conserva y se marca como no informado; no se convierte en “gratis” ni se descarta.
- `tender_start = tender_end` se conserva y se explica; no se corrige.
- Si falta una descripción, un comprador, un proveedor o un vínculo contrato–adjudicación, el JSON devuelve `null` y la UI lo dice.

## 6. UI

- **Inicio (`/`)**: hero, formulario GET accesible, tarjetas de resultados con etiqueta MYPE, paginación, estado vacío y sección “Cómo leer una oportunidad”.
- **Detalle (`/opportunities/[ocid]`)**: resumen, datos oficiales, alertas de vacíos, adjudicaciones, contratos, explicador con citas, panel MYPE y accesos al checklist/PDF.
- **Checklist (`/opportunities/[ocid]/checklist`)**: hoja imprimible, 9 pasos, advertencias, fuente, disclaimer y botón de impresión.
- **PDF (`/opportunities/[ocid]/checklist/pdf`)**: `application/pdf` real, `Content-Disposition: attachment`, generado con `pdf-lib`.
- **No encontrado**: 404 propio para OCIDs inexistentes y rutas desconocidas. Si la API no responde, la app muestra un error accionable con “Reintentar”.

Formato: PEN con `Intl.NumberFormat("es-PE")`, fechas largas/cortas en español y `timeZone: "UTC"` para no desplazar días.

## 7. Tests E2E con datos sembrados

El fixture es explícito y determinista (`web/tests/seed_db.py`). No depende del bulk real.

```powershell
cd web
npx playwright test
```

Playwright levanta dos `webServer`:

1. API con `web/tests/serve_api.py`: Playwright le pasa `CONTRATAMYPE_DB` apuntando al archivo temporal; el script lo siembra y ejecuta uvicorn en `127.0.0.1:8010`.
2. Next.js en modo dev en `127.0.0.1:3100` con `CONTRATAMYPE_API_URL=http://127.0.0.1:8010`.

El seed incluye:

- oportunidad completa con award, proveedor y contrato;
- descripción faltante;
- monto 0;
- fecha de inicio igual a fin;
- adjudicación sin proveedor;
- contrato sin adjudicación vinculada;
- departamento desconocido y entidad ausente;
- filas suficientes para filtros por departamento, categoría, monto, texto, estado y MYPE;
- una fila 2024 que no debe aparecer en la cohorte 2025;
- casos que producen estado vacío.

Cobertura actual (8 tests, 1 worker):

- búsqueda por texto y badge MYPE;
- filtros por departamento, categoría y rango de monto;
- estado vacío con enlace para limpiar;
- detalle con datos incompletos (descripción, monto 0, inicio=fin, award sin proveedor, contrato sin award);
- departamento desconocido y entidad ausente;
- 404 para OCID inexistente;
- checklist con cita y disclaimer;
- PDF: `%PDF`, `application/pdf`, `attachment` y tamaño.

Para sembrar manualmente:

```powershell
cd web
..\.venv\Scripts\python.exe tests\seed_db.py --output "$env:TEMP\contratamype-manual.duckdb"
$env:CONTRATAMYPE_DB="$env:TEMP\contratamype-manual.duckdb"
..\.venv\Scripts\python.exe -m uvicorn api.app:app --port 8000
```

## 8. Calidad

Desde `web/`:

```powershell
npm run lint
npm run format:check
npm run build
```

Desde la raíz:

```powershell
.\.venv\Scripts\ruff format api web\tests\seed_db.py web\tests\serve_api.py
.\.venv\Scripts\ruff check api web\tests\seed_db.py web\tests\serve_api.py
```

Resultados de la verificación local (2026-11-20):

- `npx playwright test`: **8 passed**.
- `npm run lint`: sin errores ni warnings.
- `npm run build`: compila; rutas dinámicas `/`, detalle, checklist y PDF.
- `npm run format:check`: OK.
- `ruff format` / `ruff check`: OK.
- Base real: `59,141` procesos de la cohorte 2025; `29,921` con `mype_fit`; búsqueda, detalle, checklist y PDF responden 200.

## 9. Límites conocidos

- **PostgreSQL diferido:** el adaptador PostgreSQL 17 queda fuera de v1.0 local porque el daemon de Docker no está disponible. La ruta implementada y verificada es la API read-only sobre DuckDB. El contrato HTTP permite sustituir la capa de datos sin tocar la web.
- **Sin escritura ni cuentas:** no hay login, favoritos, alertas ni backoffice. La API es de solo lectura.
- **`status` vacío en el bulk real:** la cohorte 2025 no trae estados de proceso en `tenders.status`. La API acepta `status`, pero la UI deshabilita el filtro y explica que la fuente no informa ese campo. El fixture sí trae estados para probar el contrato.
- **Checklist no específico:** los 9 pasos son genéricos y citan campos oficiales; no inventan requisitos del proceso. Los documentos deben confirmarse en las bases.
- **Explicador Gemini diferido:** `CONTRATAMYPE_EXPLAINER` selecciona un proveedor, pero solo `template` está implementado. Agregar Gemini requiere un adaptador, API key y evaluación; no es requisito para correr la app ni los tests.
- **Búsqueda por subcadena:** `ILIKE` sin ranking ni sinónimos. Para volumen mayor conviene un índice de texto completo o PostgreSQL.
- **Una conexión DuckDB por request:** suficiente para uso local y pruebas. Para concurrencia real, el adaptador PostgreSQL es el camino previsto.
- **Datos de la fuente:** montos 0, fechas inicio=fin, awards sin proveedor y contratos sin award se muestran como tales; no se completan con supuestos.
- **Atribución:** datos OECE/OCDS bajo CC BY 4.0. ContrataMYPE no está afiliado al OECE. Enlaces oficiales en la UI y en el PDF.
