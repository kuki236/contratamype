# Checks de calidad — ContrataMYPE v1.0.0

El pipeline ejecuta **12 checks**: los de nivel `fail` bloquean y los de nivel
`warn` solo se reportan. Escribe `quality_report.json` con conteos, SQL, muestra
de fallos y duración. Además, el reporte incluye una sección `audits` **no
bloqueante** para cobertura y consistencia.

## 1. Resultado del bulk 2025

Snapshot SHA-256 `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b`.

| # | Check | Capa | Nivel | Filas revisadas | Fallas | Estado |
|---|---|---|---|---:|---:|---|
| 1 | `raw_schema_present` | raw | fail | 124,538 | 0 | pass |
| 2 | `ocid_unique` | tender | fail | 124,538 | 0 | pass |
| 3 | `buyer_present` | tender | fail | 124,538 | 0 | pass |
| 4 | `category_valid` | tender | fail | 124,538 | 0 | pass |
| 5 | `department_valid` | tender | fail | 124,538 | 0 | pass |
| 6 | `dates_valid` | tender | fail | 124,538 | 0 | pass |
| 7 | `period_quality` | tender | warn | 124,538 | 124,535 | warn |
| 8 | `amount_non_negative` | tender | fail | 124,538 | 0 | pass |
| 9 | `amount_zero` | tender | warn | 124,538 | 8,586 | warn |
| 10 | `award_complete` | award | warn | 107,750 | 1,741 | warn |
| 11 | `contract_award_linked` | contract | warn | 107,301 | 5,128 | warn |
| 12 | `supplier_address_present` | supplier | warn | 56,734 | 56,734 | warn |

Resumen: **7 pass, 5 warn, 0 fail**. Gate abierto.

Tiempos de esta corrida: ingesta 27.0 s, calidad 688 ms, exports 584 ms,
total 28.3 s. La calidad es más lenta que antes porque ahora materializa hasta
5 muestras reales por check y calcula las auditorías.

## 2. Qué cuenta cada check

| Check | Regla |
|---|---|
| `raw_schema_present` | Sin errores de parseo JSON, OCID faltante, `tender` faltante ni título faltante/vacío |
| `ocid_unique` | `COUNT(*) - COUNT(DISTINCT ocid) = 0` sobre `raw_tenders` |
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

## 3. Decisiones de severidad

- **`period_quality` es warn:** 116,832 registros traen inicio = fin y 7,703 no
  traen período; en total 124,535 de 124,538 (99.998%) no tienen un cronograma
  utilizable. Es una convención/ausencia del registro, no un error de
  normalización. La app muestra “fecha de referencia”.
- **`amount_zero` es warn:** 0 significa “no informado” en el bulk; no es un
  monto gratuito ni un error de negación.
- **`award_complete` es warn:** 1,741 awards no traen proveedor (1.6% de las
  filas de award). Se conservan para no perder el monto adjudicado.
- **`contract_award_linked` es warn:** 4.8% de contratos referencia un award
  ausente del `compiledRelease`. El campo existe; el award no. Bloquear el
  producto por una limitación del snapshot sería incorrecto y fabricar el
  award violaría la fuente.
- **`supplier_address_present` es warn y es una limitación de la fuente:** los
  56,734 proveedores del bulk tienen `department` nulo (100%). Las partes
  proveedoras suelen traer solo `countryName`, no `address.department`. No es
  un bug del pipeline; se reporta para no fingir cobertura geográfica de
  proveedores. El departamento del **comprador** sí está completo (check 5 en
  0 fallas).

## 4. Auditorías no bloqueantes

`quality_report.json` incluye `audits`; no afectan el gate:

| Auditoría | Resultado bulk 2025 |
|---|---|
| `month_coverage` | 12/12 meses (`2025-01` a `2025-12`) por `segmentation_id` de la cohorte |
| `region_coverage` | 25/25 departamentos por `department_code` de la cohorte |
| `duplicate_parties` | 0 filas extra por RUC duplicado; 7,567 filas extra por nombre normalizado duplicado (`trim` + mayúsculas + espacios colapsados) |
| `api_vs_bulk_spot_check` | `not_run`: el pipeline corre offline y el spot-check de la API beta requiere red; no forma parte del gate |

Los duplicados de nombre no se corrigen a ciegas: dos razones sociales iguales
pueden ser entidades distintas con RUC distinto. Se reportan con muestra.

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
  --input data/raw/ocds/2025.jsonl.gz \
  --artifacts artifacts/2025 \
  --db data/processed/contratamype.duckdb
```

Los tests lentos usan una ruta temporal y no sobrescriben `artifacts/2025` ni la
base compartida. `python -m pytest -m slow` verifica el SHA-256 del bulk, los
conteos exactos y el gate.
