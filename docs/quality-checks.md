# Checks de calidad — ContrataMYPE v1.0.0

El pipeline ejecuta **12 checks** y escribe `quality_report.json` con conteos,
SQL y duración. Un check `fail` con `status = fail` bloquea los exports; un
`warn` se reporta pero no bloquea.

## 1. Resultado del bulk 2025

Snapshot SHA-256 `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b`.

| # | Check | Capa | Nivel | Filas revisadas | Fallas | Estado |
|---|---|---|---:|---:|---:|---|
| 1 | `raw_schema_present` | raw | fail | 124,538 | 0 | pass |
| 2 | `ocid_unique` | tender | fail | 124,538 | 0 | pass |
| 3 | `tender_title_present` | tender | fail | 124,538 | 0 | pass |
| 4 | `category_valid` | tender | fail | 124,538 | 0 | pass |
| 5 | `department_valid` | tender | fail | 124,538 | 0 | pass |
| 6 | `buyer_present` | tender | fail | 124,538 | 0 | pass |
| 7 | `amount_non_negative` | tender | fail | 124,538 | 0 | pass |
| 8 | `amount_zero` | tender | warn | 124,538 | 8,586 | warn |
| 9 | `dates_parseable` | tender | fail | 124,538 | 0 | pass |
| 10 | `period_start_eq_end` | tender | warn | 124,538 | 116,832 | warn |
| 11 | `award_supplier_present` | award | warn | 107,750 | 1,741 | warn |
| 12 | `contract_award_linked` | contract | warn | 107,301 | 5,128 | warn |

Resumen: **8 pass, 4 warn, 0 fail**. Gate abierto.

## 2. Qué cuenta cada check

| Check | Regla |
|---|---|
| `raw_schema_present` | Sin errores de parseo, OCID faltante ni `tender` faltante |
| `ocid_unique` | `COUNT(*) - COUNT(DISTINCT ocid) = 0` |
| `tender_title_present` | Título no nulo ni vacío |
| `category_valid` | Categoría en `{goods, services, works}` |
| `department_valid` | `department_code` mapeado a uno de los 25 departamentos |
| `buyer_present` | `buyer_id` no vacío |
| `amount_non_negative` | `amount_pen >= 0`; nulo se permite y se reporta |
| `amount_zero` | `amount_pen = 0` (no informado, no gratuito) |
| `dates_parseable` | `published_date`, inicio y fin parsean a fecha |
| `period_start_eq_end` | Inicio y fin del plazo son el mismo día |
| `award_supplier_present` | Award con `supplier_id` no vacío |
| `contract_award_linked` | `award_id` del contrato existe en `awards` del mismo OCID |

## 3. Decisiones de severidad

- **`contract_award_linked` es warn:** 4.8% de contratos referencia un award
  ausente del `compiledRelease`. El campo existe; el award no. Bloquear el
  producto por una limitación del snapshot sería incorrecto y fabricar el
  award violaría la fuente. Ver `docs/data-profile-2025.md`.
- **`amount_zero` es warn:** 0 significa “no informado” en el bulk; no es un
  monto gratuito ni un error de negación.
- **`period_start_eq_end` es warn:** 93.8% del bulk trae inicio = fin; es una
  convención del registro, no un plazo real de un día.
- **`award_supplier_present` es warn:** 1,741 awards sin proveedor (1.6% de las
  filas de award). Se conservan para no perder el monto adjudicado.

## 4. Gate

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

## 5. Reproducción

```bash
python -m contratamype run \
  --input data/raw/ocds/2025.jsonl.gz \
  --artifacts artifacts/2025 \
  --db data/processed/contratamype.duckdb
```

El reporte incluye `duration_ms` por check; en el bulk 2025 el total de calidad
fue **126 ms**, muy por debajo de la ingesta (~21.5 s).
