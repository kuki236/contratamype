# Diccionario de datos — ContrataMYPE v1.1

Fuente: bulks OCDS 2024 y 2025 del OECE (Open Contracting Data Standard),
CC BY 4.0. El pipeline normaliza `compiledRelease` y conserva el OCID como clave
de proceso. El bulk 2024 es `data/raw/ocds/2024.jsonl.gz` y el 2025 es
`data/raw/ocds/2025.jsonl.gz`; ambos están gitignored.

## 1. Granos

| Tabla | Grano | Filas bulk 2024–2025 |
|---|---|---:|
| `tenders` | un proceso (`ocid`) | 232,989 |
| `buyers` | un comprador (`buyer_id`) | 3,080 |
| `suppliers` | un proveedor (`supplier_id`) | 91,879 |
| `awards` | un award por proveedor (`ocid`, `award_id`, `supplier_id`) | 201,299 |
| `contracts` | un contrato (`ocid`, `contract_id`) | 195,583 |

`tenders` incluye todos los registros deduplicados de ambos snapshots. La
**cohorte fusionada** filtra `segmentation_year IN cohort_years` (default
`(2024, 2025)`) después del dedupe = **123,931 procesos** (2024: 64,783; 2025:
59,148). La cohorte 2024 incluye 18,455 filas con `dataSegmentation` 2024 que
solo aparecen en el snapshot 2025; la cohorte 2025 incluye 7 filas con
`dataSegmentation` 2025 que solo aparecen en el snapshot 2024. Son datos válidos,
no ruido. `snapshot_year` no filtra la cohorte: solo decide qué fila gana cuando
un OCID se repite.

## 2. `tenders`

| Columna | Tipo | Regla |
|---|---|---|
| `ocid` | VARCHAR | Clave del proceso; único tras dedupe |
| `title` | VARCHAR | Título del `tender`; obligatorio |
| `description` | VARCHAR | Descripción oficial; puede faltar |
| `category` | VARCHAR | `goods`, `services`, `works`; otro valor falla el gate |
| `method` | VARCHAR | `procurementMethodDetails`, fallback `procurementMethod` |
| `amount_pen` | DECIMAL(18,2) | `amount_PEN`, fallback `amount`; se parsea como `Decimal` exacto (no float); 0 = no informado |
| `currency` | VARCHAR | Moneda original (usualmente `PEN`) |
| `published_date` | DATE | `tender.datePublished`, fallback `release.date` |
| `tender_start` | DATE | Inicio del plazo (`tenderPeriod.startDate`) |
| `tender_end` | DATE | Fin del plazo (`tenderPeriod.endDate`) |
| `status` | VARCHAR | Estado del `tender` |
| `buyer_id` | VARCHAR | `buyer.id`; el check exige `buyer_id` **o** `buyer_name` |
| `buyer_name` | VARCHAR | `buyer.name` |
| `department` | VARCHAR | Departamento del comprador, sin tildes y en mayúsculas |
| `department_code` | VARCHAR | Código INEI de 2 dígitos; nulo si el departamento no es válido |
| `segmentation_id` | VARCHAR | `dataSegmentation.id` (ej. `2024-11`, `2025-02`) |
| `segmentation_year` | INTEGER | Año de segmentación declarado por la fuente |
| `snapshot_year` | INTEGER | Año del archivo de entrada del que provino la fila ganadora |
| `mype_fit` | BOOLEAN | Heurística calculada por el pipeline (ver §6); nunca se recalcula en la web |
| `dates_valid` | BOOLEAN | `false` solo si una fecha presente no parsea; una fecha ausente no falla |
| `period_start_eq_end` | BOOLEAN | `true` si inicio = fin (dato observado, no error) |

**Dedupe entre snapshots:** cuando un OCID aparece en más de un archivo se
conserva una fila ordenando por `published_date DESC NULLS LAST`,
`snapshot_year DESC, title`. Así gana la actualización más reciente y, si la
fecha publicada empata, gana el snapshot más nuevo. `segmentation_year` sigue
siendo el año declarado por `dataSegmentation`, no el año del archivo.

## 3. `buyers` y `suppliers`

| Columna | Tipo | Regla |
|---|---|---|
| `buyer_id` / `supplier_id` | VARCHAR | Identificador de la parte en OCDS |
| `name` | VARCHAR | Nombre oficial |
| `ruc` | VARCHAR | RUC peruano cuando `additionalIdentifiers` trae `scheme = PE-RUC` |
| `department` | VARCHAR | Departamento declarado; en proveedores de ambos bulks está siempre nulo (ver nota) |

`suppliers` se deduplica por `supplier_id`; `buyers` por `buyer_id`.

**Limitación medida en proveedores:** los 91,879 proveedores de los bulks 2024 y
2025 tienen `department` nulo. Las partes con rol `supplier` suelen traer solo
`countryName`, no `address.department`. El check `supplier_address_present` lo
reporta como warning de fuente, no como bug del pipeline. El departamento del
comprador sí está completo (3,080/3,080).

## 4. `awards`

| Columna | Tipo | Regla |
|---|---|---|
| `ocid` | VARCHAR | Proceso |
| `award_id` | VARCHAR | ID del award |
| `supplier_id` | VARCHAR | Proveedor adjudicado; vacío si el award no trae proveedor |
| `supplier_name` | VARCHAR | Nombre del proveedor |
| `amount_pen` | DECIMAL(18,2) | Valor adjudicado |
| `award_date` | DATE | Fecha del award |
| `status` | VARCHAR | Estado del award |

Un award con varios proveedores genera una fila por proveedor. Un award sin
proveedor genera una fila con `supplier_id = ''` (warning de calidad). En la
cohorte fusionada hay 2,779 awards sin proveedor (2024: 2,717; 2025: 62).

## 5. `contracts`

| Columna | Tipo | Regla |
|---|---|---|
| `ocid` | VARCHAR | Proceso |
| `contract_id` | VARCHAR | ID del contrato |
| `award_id` | VARCHAR | Award referenciado; vacío si el contrato no lo trae |
| `amount_pen` | DECIMAL(18,2) | Valor contractual |
| `signed_date` | DATE | `dateSigned` |
| `status` | VARCHAR | Estado del contrato |

**Limitación medida:** 11,274 de 195,583 contratos (5.8%) referencian un
`award_id` ausente del `compiledRelease` (2025: 5,128 de 107,301). Es un warning,
no un fallo bloqueante; no se fabrican awards. Ver
`docs/data-profile-2025.md`.

## 6. Regla MYPE

```text
mype_fit = amount_pen IS NOT NULL
           AND amount_pen > 0
           AND amount_pen <= mype_threshold
           AND category IN ('goods', 'services')
           AND (target_departments vacío OR department IN target_departments)
```

- `mype_threshold` default: **S/ 200,000**, configurable con `--mype-threshold`.
- Un monto nulo o **0 no se marca compatible**: 0 significa “no informado”, no
  “costo cero”. Tampoco se asume compatibilidad por desconocer el monto.
- `target_departments` vacío por defecto (todas las regiones).
- La etiqueta visible es **“compatible”**; no es elegibilidad legal.
- La regla se calcula una sola vez en el pipeline; la web y el dashboard leen
  `mype_fit` y no la recalculan.
- Resultado cohorte 2024-2025: **58,380 oportunidades de 123,931 procesos
  (47.1%)**; por año: 2024 **28,458 de 64,783 (43.9%)**, 2025 **29,922 de
  59,148 (50.6%)**. Los 14,335 registros de la cohorte con monto 0 quedan fuera
  de la etiqueta.
- Los conteos usan todos los registros segmentados a 2024/2025 después del
  dedupe; `snapshot_year` solo resuelve duplicados de OCID.

## 7. Artefactos

| Archivo | Uso |
|---|---|
| `quality_report.json` | 12 checks con conteos, SQL, `failed_sample` (hasta 5 filas) y sección `audits` |
| `run_manifest.json` | `inputs` (path, SHA-256, bytes, records), `input_sha256`, conteos, `settings`, timings y hashes de payloads |
| `checksums.sha256` | SHA-256 de los payloads exportados |
| `tenders.parquet`, `awards.parquet`, `contracts.parquet`, `buyers.parquet`, `suppliers.parquet` | Power BI / análisis; `tenders` incluye `snapshot_year` |
| `mype_opportunities.csv` | Oportunidades de ambas cohortes con `mype_fit = true`, `segmentation_year` explícito |

`checksums.sha256` no cubre `run_manifest.json` ni a sí mismo para evitar una
dependencia circular; el manifest sí lista los hashes de los payloads.

`run_manifest.json` incluye un bloque `inputs` ordenado por año:

```json
{
  "path": "data/raw/ocds/2024.jsonl.gz",
  "sha256": "9f50c844…",
  "bytes": 125638249,
  "records": 108451
}
```

`input_sha256` se mantiene: con un solo archivo es su hash; con varios es el
SHA-256 de las líneas `nombre:hash` unidas por `\n`, en el mismo orden anual del
bloque `inputs`. El bloque `settings` agrega `cohort_years` (lista) y conserva
`cohort_year` como el año más reciente (`2025`), además de `mype_threshold`,
`target_categories`, `target_departments`, `pipeline_version` y `git_sha`.

## 8. Campos que no se usan

No se usan datos personales de postores, correos, teléfonos ni documentos de
identidad. El RUC de proveedores es público y se conserva para trazabilidad.
