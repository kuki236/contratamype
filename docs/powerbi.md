# Power BI — ContrataMYPE

Dashboard local del mercado de compras públicas del Perú para las cohortes
`dataSegmentation` **2024 y 2025**. Se construye como PBIP (reporte PBIR + modelo
TMDL), lee los Parquet exportados por el pipeline y no consulta la base de la web.

## 1. Archivos

| Archivo | Rol |
|---|---|
| `dashboard/ContrataMYPE.pbip` | Proyecto Power BI; se abre en Desktop. |
| `dashboard/ContrataMYPE.Report/` | Reporte PBIR: dos páginas, tema y recursos. |
| `dashboard/ContrataMYPE.SemanticModel/` | Modelo TMDL: tablas, relaciones y medidas. |
| `dashboard/build_report.mjs` | Genera las páginas y visuales PBIR. |
| `dashboard/screenshots/mercado.png` | Captura de la página 1. |
| `dashboard/screenshots/oportunidades.png` | Captura de la página 2. |
| `docs/powerbi.md` | Este documento. |

El detalle de layout se edita en `dashboard/build_report.mjs` y se materializa
con:

```bash
node dashboard/build_report.mjs
```

El modelo se edita directamente en los `.tmdl`; el reporte no contiene DAX de
negocio.

## 2. Fuente y ventana

- Fuente: OECE — Portal de Contrataciones Abiertas, estándar OCDS.
- Licencia: datos abiertos **CC BY 4.0**.
- Bulk: `https://data.open-contracting.org/es/publication/135/download?name=2025.jsonl.gz`.
- Los exports de `artifacts/2025/` incorporan los snapshots 2024 y 2025; el
  `run_manifest.json` del pipeline conserva la procedencia y checksums.
- Ventana v1.1: cohortes `dataSegmentation` **2024 y 2025**.
- El modelo carga **232,989** registros. Las cohortes del reporte suman
  **123,931** procesos: **64,783** de 2024 y **59,148** de 2025.
- Las filas históricas 2013–2023 existen en el modelo para trazabilidad, pero
  las dos páginas las excluyen con el filtro de cohorte `2024–2025`.
- Los Parquet de entrada son los del pipeline:

```text
artifacts/2025/tenders.parquet
artifacts/2025/awards.parquet
artifacts/2025/contracts.parquet
artifacts/2025/buyers.parquet
artifacts/2025/suppliers.parquet
```

`data/processed/contratamype.duckdb` no se usa desde Power BI. El dashboard lee
solo los exports Parquet; la regla `mype_fit` se calcula una sola vez en el
pipeline y aquí se lee, no se recalcula.

### Parámetro de ruta

El TMDL versionado usa el parámetro de Power Query `DataFolder` con una ruta
sanitizada:

```text
C:\Users\Public\contratamype\artifacts\2025
```

Está en
`dashboard/ContrataMYPE.SemanticModel/definition/expressions.tmdl`. En esta
máquina, `C:\Users\Public\contratamype` es un **junction** al repositorio, así
el PBIP abre y refresca sin exponer la ruta del usuario. En otro clon hay que
crear el junction o editar `DataFolder`:

```powershell
New-Item -ItemType Junction `
  -Path "C:\Users\Public\contratamype" `
  -Target "C:\ruta\a\contratamype"
```

## 3. Modelo

### Tablas

| Tabla | Tipo | Filas | Uso |
|---|---|---:|---|
| `Tenders` | Hecho | 232,989 | Procesos, montos, categoría, método, fechas, MYPE. |
| `Awards` | Hecho | 201,299 | Adjudicaciones; medidas de contexto. |
| `Contracts` | Hecho | 195,583 | Contratos; medidas de contexto. |
| `Buyers` | Dimensión | 3,080 | Nombre de la entidad compradora. |
| `Suppliers` | Dimensión | 91,879 | Proveedor adjudicado. |

`Tenders` conserva las columnas técnicas en inglés (`ocid`, `buyer_id`,
`department_code`) y expone nombres en español para el reporte (`Proceso`,
`Monto (S/)`, `Departamento`, `Año de cohorte`, `Compatible MYPE`, etc.).

Columnas calculadas de presentación:

- `Categoría`: `goods` → Bienes, `services` → Servicios, `works` → Obras.
- `Compatibilidad MYPE`: etiqueta legible de `mype_fit`.
- `Rango de monto`: tramos de monto referencial, con orden oculto.
- `Mes`: mes de publicación en español, ordenado por `month_order`.
- `Año de publicación`: año calendario de publicación.

Ninguna de estas columnas vuelve a evaluar la regla MYPE. La regla corregida del
pipeline exige `amount_pen > 0`, además del umbral de monto y las categorías
`goods`/`services`; el dashboard solo lee el campo `mype_fit` exportado.

### Relaciones

```text
Tenders.buyer_id      → Buyers.buyer_id
Awards.ocid           → Tenders.ocid
Awards.supplier_id    → Suppliers.supplier_id
Contracts.ocid        → Tenders.ocid
```

Cardinalidad muchos-a-uno; filtro en una dirección. No se creó una relación
`Contracts.award_id → Awards.award_id` porque `award_id` no es único entre
OCIDs y requeriría una clave compuesta.

### Medidas

Obligatorias:

```dax
Procesos =
COUNTROWS ( 'Tenders' )

Monto total =
SUM ( 'Tenders'[Monto (S/)] )

Monto mediano =
MEDIAN ( 'Tenders'[Monto (S/)] )

Oportunidades MYPE =
CALCULATE ( [Procesos], 'Tenders'[Compatible MYPE] = TRUE () )

% MYPE =
DIVIDE ( COALESCE ( [Oportunidades MYPE], 0 ), [Procesos] )

Ticket promedio =
DIVIDE ( [Monto total], [Procesos] )
```

De apoyo:

```dax
Monto MYPE =
CALCULATE ( [Monto total], 'Tenders'[Compatible MYPE] = TRUE () )

% monto MYPE =
DIVIDE ( COALESCE ( [Monto MYPE], 0 ), [Monto total] )

Monto (miles de millones S/) =
DIVIDE ( [Monto total], 1000000000 )

Procesos con monto 0 =
CALCULATE ( [Procesos], 'Tenders'[Monto (S/)] = 0 )

Entidades compradoras =
DISTINCTCOUNT ( 'Tenders'[buyer_id] )

Monto adjudicado =
SUM ( 'Awards'[Monto adjudicado (S/)] )

Procesos con adjudicación =
DISTINCTCOUNT ( 'Awards'[ocid] )

Proveedores con adjudicación =
DISTINCTCOUNT ( 'Awards'[supplier_id] )

Contratos =
COUNTROWS ( 'Contracts' )

Monto contratado =
SUM ( 'Contracts'[Monto contratado (S/)] )
```

`MEDIAN` ignora vacíos; los montos `0` se conservan porque la fuente los
reporta como “no informado”. `DIVIDE` evita división por cero y
`COALESCE` evita un `% MYPE` en blanco en categorías sin procesos compatibles
(por ejemplo, Obras).

## 4. Páginas

### Selector de año

Ambas páginas tienen un selector de cohorte con los valores **2024, 2025** y la
opción de todos los años. En Power BI Desktop en español, la opción sin año
seleccionado se rotula **“Todas”**; equivale a “Todos” y deja ambos años en el
contexto. No hay selección por defecto: al abrir, el selector muestra “Todas” y
los visuales agregan 2024 + 2025.

El filtro de página común es:

```text
Tenders[Año de cohorte] IN {2024, 2025}
```

Ese filtro es el que impide que las filas 2013–2023 entren al reporte, incluso
cuando el selector está en “Todas”.

### Página 1 — Mercado

- Seis tarjetas: Procesos, Monto convocado, Monto mediano, Oportunidades MYPE,
  % MYPE y Ticket promedio.
- “Monto convocado por departamento”: top 10 por monto, en miles de millones
  de soles.
- “Procesos y monto por categoría”: tabla con procesos, monto y % MYPE.
- “Evolución mensual por cohorte”: línea por mes de publicación, con una serie
  para 2024 y otra para 2025.
- “Procesos por rango de monto”: distribución con tramo “Sin monto” para los
  montos 0.
- “Participación MYPE por monto”: dona con etiquetas de categoría y porcentaje.
  La heurística solo aplica a bienes y servicios.

### Página 2 — Oportunidades

Filtros de página: `Año de cohorte IN {2024, 2025}` y `Compatible MYPE = TRUE`.

- Selectores: Año de cohorte, Departamento, Categoría, Método y Rango de monto.
- Tarjetas: oportunidades en vista, monto en vista y ticket promedio.
- Tabla explorable: proceso, entidad, departamento, categoría, año de cohorte,
  método, monto, fecha de publicación y fin del período. Ordenada por fecha de
  publicación descendente.
- La tabla es una vista histórica de las cohortes, no una lista de oportunidades
  vigentes. La búsqueda por texto sigue en la web app.

## 5. Validación y verificación

Validación PBIR:

```bash
powerbi-report-author validate "dashboard/ContrataMYPE.Report" --pretty
```

Resultado del último run:

```json
{
  "data": {
    "result": "succeeded",
    "errorCount": 0,
    "warningCount": 0,
    "reportPath": "dashboard/ContrataMYPE.Report"
  }
}
```

El modelo se abrió y refrescó en Power BI Desktop desde los Parquet locales el
**22/11/2026**. Se verificaron las medidas con DAX:

| Comprobación | Valor observado |
|---|---:|
| Procesos cargados (todos los años) | 232,989 |
| Procesos cohorte 2024 | 64,783 |
| Procesos cohorte 2025 | 59,148 |
| Procesos cohorte total | 123,931 |
| Oportunidades MYPE 2024 | 28,458 |
| Oportunidades MYPE 2025 | 29,922 |
| Oportunidades MYPE total | 58,380 |
| % MYPE 2024 | 43.9% |
| % MYPE 2025 | 50.6% |
| % MYPE total | 47.1% |
| Monto total cohorte | S/ 158,343,983,740.46 |
| Monto mediano cohorte | S/ 145,600.00 |
| Ticket promedio cohorte | S/ 1,277,678.58 |
| Monto MYPE cohorte | S/ 5,773,289,671.05 |
| % monto MYPE cohorte | 3.65% |
| Procesos con monto 0 | 14,335 |
| Procesos con adjudicación | 94,570 |
| Contratos | 92,033 |

Estas cifras **no están hardcodeadas en el PBIR ni en el modelo**: salen de las
medidas y **se actualizan al refrescar**. El refresco del 22/11/2026 se hizo con
los Parquet de ambos snapshots y la regla MYPE corregida (`amount_pen > 0`). Las
capturas se rehicieron después de ese refresco.

## 6. Capturas

| Página | Archivo |
|---|---|
| Mercado | `dashboard/screenshots/mercado.png` |
| Oportunidades | `dashboard/screenshots/oportunidades.png` |

Se capturaron con `powerbi-report-author preview --host desktop` y se
recortaron para excluir el panel de filtros de Desktop. Ambas son 1872×1052 y
muestran el selector en “Todas” (ambos años).

## 7. Refresco

1. Regenerar los exports Parquet con el pipeline (fuera de este dashboard).
2. Abrir `dashboard/ContrataMYPE.pbip` en Power BI Desktop.
3. Ajustar temporalmente `DataFolder` a la ruta local de `artifacts/2025`.
4. **Inicio → Actualizar**. Power BI vuelve a leer los cinco Parquet y recalcula
   las columnas calculadas.
5. Verificar los totales con DAX o con las tarjetas de la página 1.
6. Volver a dejar `DataFolder` en `C:\Users\Public\contratamype\artifacts\2025` y no
   commitear la ruta local.
7. Repetir `powerbi-report-author validate` si se tocó el PBIR.
8. Si se editaron páginas o el modelo, recargar el reporte en Desktop antes de
   capturar. Las capturas deben rehacerse cuando cambien los datos.

No se publica en Power BI Service en v1.1. El PBIP es local.

### PBIX pendiente (manual)

En esta build de Power BI Desktop, `Archivo → Guardar una copia` solo ofreció
el formato de proyecto `.pbip`; no se generó un `.pbix`. Si se necesita el
binario para el release:

1. Abrir `dashboard/ContrataMYPE.pbip` en Desktop.
2. `Archivo → Guardar una copia`.
3. Elegir una ubicación fuera de `dashboard/` o confirmar que el nombre no
   sobrescriba el PBIP.
4. Si la build ofrece `Power BI file (*.pbix)`, guardarlo como
   `dashboard/ContrataMYPE.pbix`; si no, exportar desde una build que lo
   soporte.

El gate de release acepta el `.pbip` como artefacto de dashboard.

## 8. Límites conocidos

- **No es elegibilidad legal.** `mype_fit` es una heurística de compatibilidad
  por monto, rubro y monto informado (`amount_pen > 0`), calculada en el
  pipeline. No evalúa requisitos, RUC, experiencia ni capacidad legal.
- **Montos en moneda mixta.** `amount_pen` usa `amount_PEN` y cae a `amount`
  cuando no existe el campo PEN. Una minoría de registros es USD/EUR/GBP/BRL;
  el dashboard no filtra por moneda y suma el campo tal como lo exporta el
  pipeline. Para un análisis monetario estricto hay que filtrar `currency` o
  convertir con una tasa documentada.
- **Montos 0.** En el total 2024–2025 hay 14,335 procesos con monto 0 (9,383 en
  2024 y 4,952 en 2025). Se incluyen en `Monto total`, `Monto mediano` y
  `Ticket promedio`; el tramo “Sin monto” los hace visibles.
- **Estado del proceso vacío.** `tenders.status` viene nulo en todos los
  registros de este snapshot; no se usa en el reporte.
- **Fechas de plazo incompletas.** La mayoría de procesos tiene
  `tender_start = tender_end`; no se calcula duración ni se usa como alerta.
- **Adjudicaciones y contratos no visualizados.** `Awards`, `Contracts` y
  `Suppliers` están en el modelo con medidas de contexto, pero las páginas v1.1
  se centran en la demanda (tenders). La cobertura es parcial: 3,866 awards no
  tienen proveedor y 11,274 contratos no enlazan a un award.
- **Ventana 2024–2025.** Las filas 2013–2023 existen en el modelo pero quedan
  fuera del reporte por el filtro de cohorte. No se promete una serie histórica
  2013–2025 ni una comparación con años anteriores.
- **Sin búsqueda por texto.** El explorador filtra por cohorte, departamento,
  categoría, método y rango; la búsqueda libre y el detalle están en la web app.
- **Etiqueta “Todas”.** Power BI Desktop en español rotula la opción de todos
  los valores como “Todas”; en este reporte significa “Todos” (2024 + 2025).
- **Capturas y cifras.** Las capturas se rehicieron el 22/11/2026 después del
  refresco. Cualquier nuevo run del pipeline exige refrescar y recapturar; las
  cifras no están hardcodeadas en el reporte.

## 9. Atribución

Fuente: OECE — Portal de Contrataciones Abiertas (OCDS), datos abiertos
**CC BY 4.0**. Elaboración: ContrataMYPE. No hay afiliación con el OECE.

El reporte muestra la atribución en el pie de ambas páginas y el disclaimer
“MYPE = heurística de compatibilidad, no elegibilidad legal”.
