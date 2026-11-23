# Checks de calidad — ContrataMYPE v1.1

El pipeline ejecuta **12 checks**: los de nivel `fail` bloquean y los de nivel
`warn` solo se reportan. Escribe `quality_report.json` con conteos, SQL, muestra
de fallos y duración. Además, el reporte incluye una sección `audits` **no
bloqueante** para cobertura y consistencia.

## 1. Resultado de los bulks 2024 + 2025

Snapshots:

| Año | SHA-256 |
|---|---|
| 2024 | `9f50c84423c65605b4280d2d88b9da0853ebeb0b556d2dedf66add435cbde6e0` |
| 2025 | `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b` |

`input_sha256` combinado del manifest:
`1a7e3defdf6c5b0b3400966b74db27f4de7361c86b646661b3ca5094e9206cff`
(SHA-256 de las líneas `2024.jsonl.gz:<hash>` y `2025.jsonl.gz:<hash>`).

| # | Check | Capa | Nivel | Filas revisadas | Fallas | Estado |
|---|---|---|---|---|---:|---|
| 1 | `raw_schema_present` | raw | fail | 232,989 | 0 | pass |
| 2 | `ocid_unique` | tender | fail | 232,989 | 0 | pass |
| 3 | `buyer_present` | tender | fail | 232,989 | 0 | pass |
| 4 | `category_valid` | tender | fail | 232,989 | 0 | pass |
| 5 | `department_valid` | tender | fail | 232,989 | 0 | pass |
| 6 | `dates_valid` | tender | fail | 232,989 | 0 | pass |
| 7 | `period_quality` | tender | warn | 232,989 | 232,982 | warn |
| 8 | `amount_non_negative` | tender | fail | 232,989 | 0 | pass |
| 9 | `amount_zero` | tender | warn | 232,989 | 19,100 | warn |
| 10 | `award_complete` | award | warn | 201,299 | 3,866 | warn |
| 11 | `contract_award_linked` | contract | warn | 195,583 | 11,274 | warn |
| 12 | `supplier_address_present` | supplier | warn | 91,879 | 91,879 | warn |

Resumen: **7 pass, 5 warn, 0 fail**. Gate abierto.

Cohorte fusionada: **123,931 procesos** (2024: 64,783; 2025: 59,148) y
**58,380 oportunidades MYPE** (2024: 28,458; 2025: 29,922). `tenders` conserva
las 232,989 filas deduplicadas para búsqueda e historia.

**Composición de la cohorte:** la auditoría del archivo 2024 aislado da 46,328
filas con `dataSegmentation` 2024; el snapshot 2025 aporta 18,455 actualizaciones
más de procesos 2024, por lo que la cohorte 2024 fusionada es 64,783. La
auditoría del archivo 2025 da 59,141 filas con `dataSegmentation` 2025; el
snapshot 2024 aporta 7 más, por lo que la cohorte 2025 fusionada es 59,148. Todas
son cohorte válida después del dedupe por OCID. `snapshot_year` solo define qué
fila gana cuando un OCID se repite; no restringe la cohorte.

Tiempos observados en esta máquina: ingesta 47–80 s, calidad 0.7–1.1 s,
exports 0.7–1.2 s, total 49–83 s. La variación es I/O de disco. La calidad
materializa hasta 5 muestras reales por check y calcula las auditorías; la
ingesta domina porque procesa 274 MB comprimidos (232,989 registros) en un solo
paso.

## 2. Qué cuenta cada check

| Check | Regla |
|---|---|
| `raw_schema_present` | Sin errores de parseo JSON, OCID faltante, `tender` faltante ni título faltante/vacío |
| `ocid_unique` | `COUNT(*) - COUNT(DISTINCT ocid) = 0` sobre `tenders` (la tabla ya deduplicada) |
| `buyer_present` | `buyer_id` **o** `buyer_name` presente |
| `category_valid` | Categoría en `{goods, services, works}` |
| `department_valid` | `department_code` mapeado a uno de los 25 departamentos |
| `dates_valid` | `published_date`, inicio y fin parsean a fecha; fechas ausentes **no** fallan |
| `period_quality` | Inicio/fin presentes y distintos entre sí; ausente o inicio = fin pide confirmar cronograma |
| `amount_non_negative` | `amount_pen >= 0`; nulo se permite (no informado) |
| `amount_zero` | `amount_pen = 0` (no informado, no gratuito) |
| `award_complete` | Award con proveedor, o al menos monto o estado explícito |
| `contract_award_linked` | `award_id` del contrato no vacío y existente en `awards` del mismo OCID |
| `supplier_address_present` | `suppliers.department` no nulo (limitación de la fuente, ver §3) |

Cada check con `rows_failed > 0` incluye `failed_sample` con hasta **5 filas
reales** (`ocid`, `award_id`, `contract_id` o `supplier_id` según la capa). El
check raw guarda además hasta 5 números de línea de parseo en
`parse_error_lines` y en la muestra. Un check sin fallas devuelve
`failed_sample: []`.

Los checks corren sobre todos los inputs cargados. `ocid_unique` mide la tabla
final porque los snapshots pueden repetir un OCID: el dedupe por
`published_date DESC, snapshot_year DESC, title` deja una fila por proceso.

## 3. Decisiones de severidad

- **`period_quality` es warn:** 116,384 registros traen inicio = fin y 7,547 no
  traen período; en total 123,931 de 123,931 (100%) de la cohorte fusionada no
  tiene un cronograma utilizable (2024: 61,211 + 3,572; 2025: 55,173 + 3,975).
  Es una convención/ausencia del registro, no un error de normalización. La app
  muestra “fecha de referencia”.
- **`amount_zero` es warn:** 0 significa “no informado” en el bulk; no es un
  monto gratuito ni un error de negación. En la cohorte hay 14,335 (2024: 9,383;
  2025: 4,952).
- **`award_complete` es warn:** en la cohorte, 2,779 awards no traen proveedor
  (2024: 2,717; 2025: 62; 2.7% de los 103,216 awards de la cohorte). En el bulk
  completo el check marca 3,866 de 201,299 (1.9%). Se conservan para no perder
  el monto adjudicado.
- **`contract_award_linked` es warn:** 11,274 de 195,583 contratos (5.8%)
  referencian un award ausente del `compiledRelease` (2025: 5,128 de 107,301).
  El campo existe; el award no. Bloquear el producto por una limitación del
  snapshot sería incorrecto y fabricar el award violaría la fuente.
- **`supplier_address_present` es warn y es una limitación de la fuente:** los
  91,879 proveedores de ambos bulks tienen `department` nulo (100%). Las partes
  proveedoras suelen traer solo `countryName`, no `address.department`. No es un
  bug del pipeline; se reporta para no fingir cobertura geográfica de
  proveedores. El departamento del **comprador** sí está completo (checks 5 en 0
  fallas).

## 4. Auditorías no bloqueantes

`quality_report.json` incluye `audits`; no afectan el gate:

| Auditoría | Resultado bulk 2024–2025 |
|---|---|
| `month_coverage` | 24/24 meses: 2024-01→2024-12 y 2025-01→2025-12, 12 por año, por `segmentation_id` de la cohorte fusionada |
| `region_coverage` | 25/25 departamentos por `department_code` de la cohorte fusionada |
| `duplicate_parties` | 0 filas extra por RUC duplicado; 16,021 filas extra por nombre normalizado duplicado (`trim` + mayúsculas + espacios colapsados) en 91,879 proveedores |
| `api_vs_bulk_spot_check` | `not_run`: el pipeline corre offline y el spot-check de la API beta requiere red; no forma parte del gate |

`month_coverage` reporta `by_year` con los 12 meses esperados por año. Los
duplicados de nombre no se corrigen a ciegas: dos razones sociales iguales pueden
ser entidades distintas con RUC distinto. Se reportan con muestra.

## 5. Gate

```json
{
  "blocked": false,
  "blocking_checks": [],
  "rule": "any level=fail check with status=fail blocks app exports"
}
```

Si el gate se bloquea:

- No se escriben Parquet/CSV de la app (sí se escribe el reporte y el manifest).
- El CLI devuelve código 1.
- El digest de alertas se niega a ejecutarse.

## 6. Reproducción

```bash
python -m contratamype run \
  --input data/raw/ocds/2024.jsonl.gz \
  --input data/raw/ocds/2025.jsonl.gz \
  --artifacts artifacts/2024-2025 \
  --db data/processed/contratamype.duckdb
```

`--input` es repetible y se procesa en orden de año. Los tests lentos usan una
ruta temporal y no sobrescriben `artifacts/2025` ni la base compartida.
`python -m pytest -m slow` verifica ambos SHA-256, los conteos exactos por año,
las 123,931 filas de cohorte, las 58,380 oportunidades MYPE y el gate.
