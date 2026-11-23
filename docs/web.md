# Web app y API de ContrataMYPE

> **Alcance:** v1.1 multi-cohorte (2024 + 2025): búsqueda, detalle, estados vacíos, checklist/PDF y E2E con datos sembrados, con filtro de año y agregados por defecto sobre todas las cohortes. Incluye la parte visible de Fase 5 (explicador por plantilla, citas de campos y disclaimer). El adaptador Gemini queda preparado como punto de extensión, no implementado.
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
- El explicador es una plantilla en español sobre campos oficiales. Cada punto cita la tabla/campo de origen e incluye secciones explícitas **“Qué revisar”** y **“Datos faltantes”**.
- La fuente y el disclaimer aparecen en la ficha, el checklist y el PDF: **heurística de compatibilidad MYPE, no elegibilidad legal**.
- La evaluación reproducible del explicador está en `docs/llm-evaluation-v1.0.0.md` (15 OCID reales).

## 2. Requisitos

- Python 3.13 con el entorno `.venv` del repo.
- Node.js 24 y npm.
- La base DuckDB generada por el pipeline con las cohortes 2024 y 2025 (`data/processed/contratamype.duckdb`).
- Navegadores de Playwright (`npx playwright install chromium`) para el E2E.

## 3. Puesta en marcha

Desde la raíz del repo:

```powershell
# Dependencias Python (incluye fastapi, uvicorn y python-dotenv; declaradas en pyproject.toml)
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Copia la configuración de ejemplo; api/config.py carga .env automáticamente
Copy-Item .env.example .env

# API en http://127.0.0.1:8000
.\.venv\Scripts\python.exe -m uvicorn api.app:app --port 8000
```

`api/config.py` ejecuta `load_dotenv(REPO_ROOT / ".env")` sin sobrescribir variables
ya definidas en el entorno. La alternativa explícita sigue disponible:

```powershell
.\.venv\Scripts\python.exe -m uvicorn api.app:app --port 8000 --env-file .env
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

No hay secretos en el repo. El API carga `.env` con `python-dotenv`; Next.js lee `.env.local` en `web/`. Ambos están ignorados por Git y `.env.example` documenta las variables.

## 5. API

Base: `http://127.0.0.1:8000`. Todo es `GET`, sin autenticación y sin escritura.

| Endpoint | Parámetros | Respuesta |
|---|---|---|
| `/health` | — | `{ "status": "ok" }`; ejecuta `SELECT 1 FROM tenders LIMIT 1` y devuelve 503 genérico si la tabla o la DuckDB no están disponibles. |
| `/meta` | `year` (opcional, 2000–2100; sin valor = todas las cohortes) | `years` (todas las cohortes presentes, ordenadas), departamentos, categorías, métodos, estados y rango de montos positivos del filtro pedido. |
| `/opportunities` | `q` (máx. 200), `department`, `category`, `method`, `min_amount`, `max_amount`, `status`, `year` (opcional; sin valor = todas), `mype_only` (false), `page` (1–100000), `page_size` (20, máx. 100) | `items`, `total`, `page`, `page_size`, `pages`. Búsqueda por título, descripción, entidad u OCID. Orden: publicación descendente, OCID. |
| `/opportunities/{ocid}` | — | Ficha con `buyer`, `awards`, `contracts` (cada contrato trae `award_linked`) y `data_quality` (descripción faltante, monto 0, inicio=fin, awards/contratos ausentes, proveedor o adjudicación sin vínculo). 404 si no existe. |
| `/stats` | `year` (opcional; sin valor = todas) | `year` (`null` si agrega todas), totales, MYPE, monto 0, descripción faltante, inicio=fin, mediana, y agregados por departamento, categoría y método. |
| `/checklist/{ocid}` | — | Checklist JSON generado solo con campos oficiales: proceso, fuente, 9 pasos, advertencias y disclaimer. 404 si no existe. |

Decisiones de contrato:

- **Año:** `year` es un entero opcional entre 2000 y 2100. Omitirlo significa **todas las cohortes** (2024 + 2025); un valor explícito filtra `tenders.segmentation_year`. Aplica a `/meta`, `/opportunities` y `/stats`; detalle, checklist y PDF no filtran por año porque el OCID es único.
- **`Meta.years`** reemplaza a `cohort_year`: siempre lista las cohortes presentes en la base, ordenadas ascendente, incluso cuando la consulta pide un año. La web deriva de ahí las opciones del selector.
- **`Stats.year`** repite el filtro aplicado y es `null` cuando se agregaron todas las cohortes.
- Conteos esperados de la base real v1.1 (ambas cohortes son disjuntas): 2024 = **46,328**, 2025 = **59,141**, todas = **105,469**. Las cohortes se suman; no hay solapamiento por OCID.
- `mype_only` en la API es `false` por defecto para permitir explorar toda la cohorte. La UI arranca con **Solo compatibles MYPE**; el valor viaja explícito en la URL (`mype_only=1|0`).
- Los montos viajan como números JSON para presentación. En DuckDB son `DECIMAL(18,2)`; a esta escala (máximo ~S/ 1,134 millones) los centavos se representan sin pérdida en un double.
- La API no reimplementa el umbral, las categorías objetivo ni los departamentos objetivo de la regla MYPE. Solo expone `tenders.mype_fit`.
- `amount_pen = 0` se conserva y se marca como no informado; no se convierte en “gratis” ni se descarta.
- `tender_start = tender_end` se conserva y se explica; no se corrige.
- Si falta una descripción, un comprador, un proveedor o un vínculo contrato–adjudicación, el JSON devuelve `null` y la UI lo dice.
- `contracts[].award_linked` es la fuente de verdad del vínculo contrato–adjudicación; la web no recalcula la lista de awards.
- Un `page` fuera del rango permitido devuelve 422, nunca 500. La web lo acota a `MAX_PAGE` antes de llamar a la API.
- Los 503 no exponen la ruta absoluta de la DuckDB: el detalle queda en el log del servidor y el cliente recibe un mensaje genérico.
- La web corta cada `fetch` a 5 s (`AbortSignal.timeout(5000)`). Solo un 404 con `Content-Type: application/json` se traduce a “OCID no existe”; un 404 HTML de un proxy o URL incorrecta se muestra como error de servicio.

## 6. UI

- **Inicio (`/`)**: hero, formulario GET accesible, tarjetas de resultados con etiqueta MYPE, paginación, estado vacío y sección “Cómo leer una oportunidad”.
  - **Año**: selector con **Todos** (default), **2025** y **2024**, generado desde `meta.years` en orden descendente. El valor viaja como `year=YYYY`; **Todos** omite el parámetro. Se conserva en paginación, en “Ver todas las oportunidades”, en “Ir a la página 1” y en el envío del formulario.
  - El hero muestra el conteo del filtro activo: **Procesos 2024–2025** en Todos, **Procesos 2025** o **Procesos 2024** con año explícito. La etiqueta de cohorte y el pie del formulario también se derivan de `meta.years`; no hay un año fijo en el copy.
  - `q` se limita a 200 caracteres en el input y en `parseFilters`; no se propaga a la API un valor que provoque 422.
  - Los montos inválidos (`?min_amount=abc`) se ignoran al construir la query y no se copian a los enlaces de paginación.
  - Una página fuera de rango muestra “Página fuera de rango” con enlace a la página 1, en lugar del estado vacío genérico.
  - Si el filtro MYPE oculta resultados que sí existen en toda la cohorte, el estado vacío ofrece **Ver todas las oportunidades** (`mype_only=0`) conservando los demás filtros, incluido el año.
  - Conteos y paginación usan `toLocaleString("es-PE")`.
- **Detalle (`/opportunities/[ocid]`)**: resumen, datos oficiales, alertas de vacíos (incluye adjudicación sin proveedor y contrato sin adjudicación vinculada), adjudicaciones, contratos, explicador con citas, panel MYPE y accesos al checklist/PDF.
  - Estados OCDS conocidos se traducen (`active` → Vigente, `cancelled` → Cancelado, `terminated` → Terminado); un valor no reconocido se muestra como `<valor> (fuente)`.
  - La etiqueta negativa dice **No marcada compatible** y mantiene el disclaimer de heurística al lado.
  - El explicador renderiza “Qué revisar” y “Datos faltantes” con `Fuente:` y disclaimer.
- **Checklist (`/opportunities/[ocid]/checklist`)**: hoja imprimible, 9 pasos, advertencias, fuente, disclaimer y botón de impresión.
  - Monto 0 se muestra como `S/ 0.00 (no informado útil)`, igual que en el PDF.
- **PDF (`/opportunities/[ocid]/checklist/pdf`)**: `application/pdf` real, `Content-Disposition: attachment`, generado con `pdf-lib`.
  - Categoría y estado MYPE se imprimen con etiquetas en español; no se filtran códigos como `goods` ni “no compatible”.
- **No encontrado**: 404 propio para OCIDs inexistentes y rutas desconocidas. Si la API no responde o devuelve un 404 que no es JSON, la app muestra un error accionable con “Reintentar”.

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
- una fila 2024 (`ocds-test-0010`) que aparece con **Todos** y con `year=2024`, pero no con `year=2025`;
- 25 filas no-MYPE deterministas (`ocds-test-bulk-01..25`) que solo existen para probar paginación y normalización de montos sin alterar los conteos de los demás tests;
- casos que producen estado vacío.

El fixture tiene **37 filas**: 36 de 2025 y 1 de 2024. Conteos exactos que usan los tests: **Todos = 37**, **2025 = 36**, **2024 = 1**; compatibles MYPE = **8** (7 de 2025 + 1 de 2024).

Cobertura actual (23 tests, 1 worker):

- búsqueda por texto y badge MYPE (8 resultados MYPE por defecto, con la fila 2024 incluida);
- filtro de año: “Todos” por defecto, opciones 2025/2024, conteos exactos y fila 2024 visible solo con Todos o `year=2024`;
- filtros por departamento, categoría y rango de monto, con la fila 2024 incluida en Todos y excluida en `year=2025`;
- estado vacío con enlace para limpiar;
- estado vacío MYPE con enlace “Ver todas las oportunidades” que conserva los filtros y el año;
- `q` de 201 caracteres truncado a 200 sin 422;
- `min_amount=abc` ignorado y no propagado al paginar a la página 2, también con `year=2025`;
- `page` gigante acotado en la web y rechazado con 422 (no 500) en la API;
- página fuera de rango con enlace a la página 1 que conserva el año;
- traducción de estados OCDS (`active` → Vigente) y fallback `(fuente)`;
- detalle con datos incompletos (descripción, monto 0, inicio=fin, award sin proveedor, contrato sin award);
- detalle, checklist y PDF de la fila 2024;
- departamento desconocido y entidad ausente;
- 404 para OCID inexistente;
- alertas de adjudicación sin proveedor y contrato sin vínculo;
- checklist con 9 pasos, una cita por paso y disclaimer;
- checklist de monto cero con `S/ 0.00 (no informado útil)`;
- PDF del caso incompleto: monto, categoría traducida, fuentes y disclaimer verificados sobre el contenido real del PDF;
- explicador con “Qué revisar”, “Datos faltantes”, citas y disclaimer;
- PDF: `%PDF`, `application/pdf`, `attachment` y tamaño;
- contrato de la API por año: `/meta` expone `years` y filtros por cohorte; `/stats` y `/opportunities` devuelven 37/36/1 para Todos/2025/2024 y `Stats.year = null` en Todos.

Para sembrar manualmente:

```powershell
cd web
..\.venv\Scripts\python.exe tests\seed_db.py --output "$env:TEMP\contratamype-manual.duckdb"
$env:CONTRATAMYPE_DB="$env:TEMP\contratamype-manual.duckdb"
..\.venv\Scripts\python.exe -m uvicorn api.app:app --port 8000
```

## 8. Evaluación del explicador

La evaluación reproducible del camino `template` con los 15 OCID reales de
`docs/llm-eval-sample-2025.json` está en `docs/llm-evaluation-v1.0.0.md`.
Resultado de la última ejecución: **15/15 casos** con citas, sección “Datos
faltantes”, disclaimer y sin afirmaciones de elegibilidad legal.

```powershell
cd web
npx tsx scripts/evaluate-explainer.ts
```

El script consulta la API real (`CONTRATAMYPE_API_URL`, default
`http://127.0.0.1:8000`), ejecuta el mismo explicador de la ficha y falla con
código distinto de cero si un caso incumple un criterio.

## 9. Calidad

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

Resultados de la verificación local (2026-11-22):

- `npx playwright test`: **23 passed** (1 worker).
- `npm run lint`: sin errores ni warnings.
- `npm run build`: compila; rutas dinámicas `/`, detalle, checklist y PDF.
- `npm run format:check`: OK (incluye `next-env.d.ts` en `.prettierignore` porque Next lo regenera con CRLF en Windows).
- `ruff format` / `ruff check` sobre `api/` y `web/tests/*.py`: OK.
- Fixture determinista: 37 filas (36 de 2025 + 1 de 2024); `/stats` y `/opportunities` devuelven 37 en Todos, 36 con `year=2025` y 1 con `year=2024`; `mype_opportunities` = 8 en Todos.
- La base real multi-cohorte no se usó para esta verificación: el pipeline de la rama estaba en reconstrucción durante la corrida. Los conteos esperados son 46,328 (2024) + 59,141 (2025) = 105,469; quedan pendientes de validar sobre la base fusionada. El contrato HTTP está verificado con el fixture.
- Sin DuckDB, `/opportunities` y `/health` responden 503 con mensaje genérico; la ruta absoluta solo queda en el log del servidor.

## 10. Límites conocidos

- **Base real multi-cohorte:** el fixture E2E ya cubre 2024/2025, pero la validación contra la DuckDB real de 105,469 procesos depende de la corrida del pipeline multi-input. La API expone en `years` las cohortes que encuentre y la UI genera el selector desde ahí; si una cohorte no está cargada, no aparece como opción, sin código específico por año.
- **PostgreSQL diferido:** el adaptador PostgreSQL 17 queda fuera de v1.0 local porque el daemon de Docker no está disponible. La ruta implementada y verificada es la API read-only sobre DuckDB. El contrato HTTP permite sustituir la capa de datos sin tocar la web.
- **Sin escritura ni cuentas:** no hay login, favoritos, alertas ni backoffice. La API es de solo lectura.
- **`status` vacío en el bulk real:** la cohorte 2025 no trae estados de proceso en `tenders.status`. La API acepta `status`, pero la UI deshabilita el filtro y explica que la fuente no informa ese campo. El fixture sí trae estados para probar el contrato.
- **Checklist no específico:** los 9 pasos son genéricos y citan campos oficiales; no inventan requisitos del proceso. Los documentos deben confirmarse en las bases.
- **Explicador Gemini diferido:** `CONTRATAMYPE_EXPLAINER` selecciona un proveedor, pero solo `template` está implementado. Agregar Gemini requiere un adaptador, API key y evaluación; no es requisito para correr la app ni los tests.
- **Búsqueda por subcadena:** `ILIKE` sin ranking ni sinónimos. Para volumen mayor conviene un índice de texto completo o PostgreSQL.
- **Una conexión DuckDB por request:** suficiente para uso local y pruebas. Para concurrencia real, el adaptador PostgreSQL es el camino previsto.
- **Datos de la fuente:** montos 0, fechas inicio=fin, awards sin proveedor y contratos sin award se muestran como tales; no se completan con supuestos.
- **Atribución:** datos OECE/OCDS bajo CC BY 4.0. ContrataMYPE no está afiliado al OECE. Enlaces oficiales en la UI y en el PDF.
