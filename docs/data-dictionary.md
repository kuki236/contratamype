# Diccionario de datos — ContrataMYPE v1.0.0

Fuente: bulk OCDS 2025 del OECE (Open Contracting Data Standard), CC BY 4.0.
El pipeline normaliza `compiledRelease` y conserva el OCID como clave de proceso.

## 1. Granos

| Tabla | Grano | Filas bulk 2025 |
|---|---|---|
| `tenders` | un proceso (`ocid`) | 124,538 |
| `buyers` | un comprador (`buyer_id`) | 2,994 |
| `suppliers` | un proveedor (`supplier_id`) | 56,734 |
| `awards` | un award por proveedor (`ocid`, `award_id`, `supplier_id`) | 107,750 |
| `contracts` | un contrato (`ocid`, `contract_id`) | 107,301 |

`tenders` incluye todo el bulk; la cohorte 2025 se filtra con
`segmentation_year = 2025` (59,141 procesos). Los exports de la app y el
dashboard usan esa cohorte por defecto.

## 2. `tenders`

| Columna | Tipo | Regla |
|---|---|---|
| `ocid` | VARCHAR | Clave del proceso; único tras dedupe |
| `title` | VARCHAR | Título del `tender`; obligatorio |
| `description` | VARCHAR | Descripción oficial; puede faltar |
| `category` | VARCHAR | `goods`, `services`, `works`; otro valor falla el gate |
| `method` | VARCHAR | `procurementMethodDetails`, fallback `procurementMethod` |
| `amount_pen` | DECIMAL(18,2) | `amount_PEN`, fallback `amount`; 0 = no informado |
| `currency` | VARCHAR | Moneda original (usualmente `PEN`) |
| `published_date` | DATE | `tender.datePublished`, fallback `release.date` |
| `tender_start` | DATE | Inicio del plazo (`tenderPeriod.startDate`) |
| `tender_end` | DATE | Fin del plazo (`tenderPeriod.endDate`) |
| `status` | VARCHAR | Estado del `tender` |
| `buyer_id` | VARCHAR | `buyer.id`; obligatorio |
| `buyer_name` | VARCHAR | `buyer.name` |
| `department` | VARCHAR | Departamento del comprador, sin tildes y en mayúsculas |
| `department_code` | VARCHAR | Código INEI de 2 dígitos; nulo si el departamento no es válido |
| `segmentation_id` | VARCHAR | `dataSegmentation.id` (ej. `2025-02`) |
| `segmentation_year` | INTEGER | Año de la cohorte |
| `mype_fit` | BOOLEAN | Heurística calculada por el pipeline (ver §6) |
| `dates_valid` | BOOLEAN | `false` si alguna fecha no parsea |
| `period_start_eq_end` | BOOLEAN | `true` si inicio = fin (dato observado, no error) |

## 3. `buyers` y `suppliers`

| Columna | Tipo | Regla |
|---|---|---|
| `buyer_id` / `supplier_id` | VARCHAR | Identificador de la parte en OCDS |
| `name` | VARCHAR | Nombre oficial |
| `ruc` | VARCHAR | RUC peruano cuando `additionalIdentifiers` trae `scheme = PE-RUC` |
| `department` | VARCHAR | Departamento declarado; puede faltar |

`suppliers` se deduplica por `supplier_id`; `buyers` por `buyer_id`.

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
proveedor genera una fila con `supplier_id = ''` (warning de calidad).

## 5. `contracts`

| Columna | Tipo | Regla |
|---|---|---|
| `ocid` | VARCHAR | Proceso |
| `contract_id` | VARCHAR | ID del contrato |
| `award_id` | VARCHAR | Award referenciado; vacío si el contrato no lo trae |
| `amount_pen` | DECIMAL(18,2) | Valor contractual |
| `signed_date` | DATE | `dateSigned` |
| `status` | VARCHAR | Estado del contrato |

**Limitación medida:** 5,128 de 107,301 contratos (4.8%) referencian un
`award_id` ausente del `compiledRelease`. Es un warning, no un fallo
bloqueante; no se fabrican awards. Ver `docs/data-profile-2025.md`.

## 6. Regla MYPE

```text
mype_fit = amount_pen <= mype_threshold
           AND category IN ('goods', 'services')
```

- `mype_threshold` default: **S/ 200,000**, configurable con `--mype-threshold`.
- `target_departments` vacío por defecto (todas las regiones).
- La etiqueta visible es **“compatible”**; no es elegibilidad legal.
- La regla se calcula una sola vez en el pipeline; la web y el dashboard leen
  `mype_fit` y no la recalculan.

## 7. Artefactos

| Archivo | Uso |
|---|---|
| `quality_report.json` | 12 checks con conteos, SQL y gate |
| `run_manifest.json` | SHA-256 del input, conteos, timings y hashes de payloads |
| `checksums.sha256` | SHA-256 de los payloads exportados |
| `tenders.parquet`, `awards.parquet`, `contracts.parquet`, `buyers.parquet`, `suppliers.parquet` | Power BI / análisis |
| `mype_opportunities.csv` | Oportunidades de la cohorte con `mype_fit = true` |

`checksums.sha256` no cubre `run_manifest.json` ni a sí mismo para evitar una
dependencia circular; el manifest sí lista los hashes de los payloads.

## 8. Campos que no se usan

No se usan datos personales de postores, correos, teléfonos ni documentos de
identidad. El RUC de proveedores es público y se conserva para trazabilidad.
