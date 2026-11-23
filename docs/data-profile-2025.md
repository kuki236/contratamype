# Perfil de datos OCDS 2024–2025

> **Fuente:** OECE — Portal de Contrataciones Abiertas, estándar OCDS.
> **Archivos:** `data/raw/ocds/2024.jsonl.gz` y `data/raw/ocds/2025.jsonl.gz`
> (no se commitean).
> **Descarga:** 20/11/2026 desde el Registro de Datos de Open Contracting
> Partnership.
> **Licencia:** CC BY 4.0.

## 1. Archivos y hashes

| Dato | 2024 | 2025 |
|---|---:|---:|
| URL | `https://data.open-contracting.org/es/publication/135/download?name=2024.jsonl.gz` | `https://data.open-contracting.org/es/publication/135/download?name=2025.jsonl.gz` |
| Bytes | 125,638,249 | 148,719,573 |
| SHA-256 | `9f50c84423c65605b4280d2d88b9da0853ebeb0b556d2dedf66add435cbde6e0` | `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b` |
| Líneas / registros | 108,451 | 124,538 |
| Cohorte same-year (auditoría) | 46,328 | 59,141 |
| Cohorte fusionada | **64,783** | **59,148** |

`input_sha256` combinado del manifest:
`1a7e3defdf6c5b0b3400966b74db27f4de7361c86b646661b3ca5094e9206cff`
(SHA-256 de las líneas `2024.jsonl.gz:<hash>` y `2025.jsonl.gz:<hash>`).

**Lectura clave:** cada archivo anual es un **snapshot de actualizaciones**, no
una cohorte de procesos iniciados ese año. Incluye procesos antiguos
actualizados durante el año y filas segmentadas a otros años. La fecha oficial
de segmentación se publica en `dataSegmentation.id` (criterios: año/mes de
inicio de convocatoria o de publicación).

La cohorte fusionada se calcula con `segmentation_year IN (2024, 2025)` después
del dedupe por OCID: **64,783 + 59,148 = 123,931**. El snapshot 2025 aporta
18,455 filas segmentadas 2024 que actualizan procesos de ese año; el snapshot
2024 aporta 7 filas segmentadas 2025. Son cohorte válida, no ruido.
`snapshot_year` solo define qué fila gana cuando un OCID se repite.

Las auditorías `docs/cohort-2024.json` (46,328) y `docs/cohort-2025.json`
(59,141) cuentan solo el **mismo año dentro de su archivo** y no representan la
cohorte fusionada.

## 2. Cohortes fusionadas

| Métrica | 2024 | 2025 | Total |
|---|---:|---:|---:|
| Procesos | **64,783** | **59,148** | **123,931** |
| Awards | 56,101 | 47,115 | 103,216 |
| Contratos | 49,383 | 42,650 | 92,033 |
| `goods` | 29,438 | 26,982 | 56,420 |
| `services` | 28,629 | 25,491 | 54,120 |
| `works` | 6,716 | 6,675 | 13,391 |
| MYPE compatible | **28,458** (43.9%) | **29,922** (50.6%) | **58,380** (47.1%) |

**2024 — montos (PEN):** mediana 145,520.00; p90 1,362,461.22; p99
17,074,165.10; máximo 1,057,661,667.78.

| Umbral (solo monto) | 2024 | % | 2025 | % |
|---|---:|---:|---:|---:|
| ≤ S/ 50,000 | 12,581 | 19.4% | 8,158 | 13.8% |
| ≤ S/ 100,000 | 25,752 | 39.8% | 22,923 | 38.8% |
| ≤ S/ 200,000 | 38,202 | 59.0% | 35,312 | 59.7% |
| ≤ S/ 400,000 | 48,775 | 75.3% | 45,238 | 76.5% |
| ≤ S/ 1,000,000 | 56,661 | 87.5% | 52,651 | 89.0% |

Estos buckets son **solo de monto**: incluyen procesos con monto 0 y obras, por
lo que no equivalen a `mype_fit`. La regla MYPE final se mide en §5.

**2024 — regiones principales:** Lima 20,480; Cusco 5,798; Áncash 3,444; Puno
2,856; Arequipa 2,755; Junín 2,460; La Libertad 2,457.

**2024 — métodos principales:** Adjudicación Simplificada 37,539; Subasta
Inversa Electrónica 7,063; Licitación Pública 4,316; Comparación de Precios
3,917; Concurso Público 3,292; Contratación Directa 3,235.

**2025 — montos (PEN):** mediana 145,700.00; p90 1,117,463.33; p99
14,751,543.23; máximo 1,134,909,484.19.

**2025 — regiones principales:** Lima 16,327; Cusco 5,052; Áncash 3,242; Puno
3,063; Ayacucho 2,875; Junín 2,680; Apurímac 2,449.

**2025 — métodos principales:** Adjudicación Simplificada 13,929; Licitación
Pública Abreviada 10,227; Concurso Público Abreviado 9,380; Subasta Inversa
Electrónica 7,193; Comparación de Precios 5,097; Contratación Directa 3,516.

## 3. Calidad

| Regla | 2024 (64,783) | 2025 (59,148) | Cohorte total (123,931) |
|---|---:|---:|---:|
| `amount_zero` | 9,383 (14.5%) | 4,952 (8.4%) | 14,335 (11.6%) |
| `period_missing` | 3,572 (5.5%) | 3,975 (6.7%) | 7,547 (6.1%) |
| `period_start_eq_end` | 61,211 (94.5%) | 55,173 (93.3%) | 116,384 (93.9%) |
| `period_quality` (faltante o inicio = fin) | 64,783 (100%) | 59,148 (100%) | 123,931 (100%) |
| `awards_without_supplier` | 2,717 | 62 | 2,779 |
| `contracts_without_award` | 0 | 0 | 0 |
| `missing_department` | 0 | 0 | 0 |
| `invalid_category` | 0 | 0 | 0 |
| `amount_missing` | 0 | 0 | 0 |

Sobre el bulk completo (232,989 filas), los warnings del pipeline son 232,982
`period_quality`, 19,100 `amount_zero`, 3,866 `award_complete`, 11,274
`contract_award_linked` y 91,879 `supplier_address_present`; los 7 checks `fail`
pasan en 0. Detalle en `docs/quality-checks.md`.

**Proveedores sin dirección:** 91,879 de 91,879 (100%) tienen `department`
nulo en ambos bulks. Las partes proveedoras suelen traer solo `countryName`. Es
una limitación de la fuente, no un error del pipeline; el check
`supplier_address_present` la reporta como warn y no se inventa el departamento.

**Implicaciones de producto:**
- El **plazo** no es confiable: en 100% de la cohorte falta el período o
  `tenderPeriod.startDate == endDate`. La app debe mostrar “fecha de referencia”
  y enlace al portal oficial; las alertas se basan en **oportunidades nuevas**,
  no en cuentas regresivas.
- 11.6% de la cohorte tiene monto 0 (2024: 14.5%; 2025: 8.4%): mostrar “monto
  no informado”, no S/ 0. La regla MYPE excluye esos registros.
- Los awards sin proveedor son 2.7% de los awards de la cohorte (2,779); el
  resto se puede modelar.

## 4. API vs bulk (spot-check)

- Se compararon 20 registros de la API (`sourceId=seace_v3`, `dataSegmentationID=2025-01`, página 1) contra el bulk 2025.
- **9/20 OCIDs encontrados** en el bulk; **0 diferencias** en título, categoría, monto y segmentación.
- 11 no están en el bulk porque la API está más fresca (actualizaciones posteriores a la generación del archivo anual).
- **Decisión:** bulk como base reproducible; API para refresco incremental/spot-check, no para reconstruir el volumen completo.
- **En el pipeline:** este spot-check **no se ejecuta**; `quality_report.json`
  registra `api_vs_bulk_spot_check` con estado `not_run` y la razón (sin red).
  La comparación de arriba es una verificación manual del perfil, no un
  resultado que cada corrida pueda reproducir offline.

## 5. Regla MYPE y umbral

No existe un flag MYPE en OCDS. La regla es **monto + rubro + región**,
configurable y etiquetada como **“compatible”**, nunca como elegibilidad legal.

```text
mype_fit = amount_pen > 0
           AND amount_pen <= 200,000
           AND category IN (goods, services)
           AND (target_departments vacío OR department IN target_departments)
```

- Un monto 0 o nulo **no** se marca compatible: 0 significa “no informado”.
- **Resultado cohorte 2024–2025: 58,380 procesos compatibles (47.1% de
  123,931).** Por año: 2024 **28,458 de 64,783 (43.9%)**; 2025 **29,922 de
  59,148 (50.6%)**.
- Los 14,335 registros de la cohorte con monto 0 quedan fuera de la etiqueta
  (2024: 9,383; 2025: 4,952).
- La tabla de umbrales de §2 es solo de **monto** (incluye 0 y obras) y no debe
  citarse como participación MYPE.
- Alternativas de umbral (solo monto 2025): S/ 100,000 (38.8%, más selectivo) o
  S/ 400,000 (76.5%, demasiado amplio para llamarlo MYPE).
- El umbral se guarda en configuración y en el bloque `settings` de
  `run_manifest.json`; no se hardcodea en la web.

## 6. Decisión de alcance v1.1

- **2024 y 2025** como años de cohorte. Después del dedupe se cuentan todas las
  filas con `segmentation_year` 2024 o 2025, incluidas las que aparecen en el
  snapshot del otro año: 64,783 + 59,148 = **123,931**.
- `snapshot_year` se guarda y se usa solo para priorizar la actualización más
  nueva cuando un OCID se repite; no restringe la cohorte.
- Cargar los 232,989 registros deduplicados con `segmentation_year` y
  `snapshot_year` para búsqueda/historia; la web y el dashboard filtran por año
  y usan “Todos (2024–2025)” por defecto.
- **2013–2023** no forma parte de la promesa de v1.1: esas filas existen en
  `tenders` como historia, pero no son cohorte.
- **Sin Spark:** 274 MB comprimidos y 233k filas se procesan con Python +
  DuckDB/PostgreSQL.

## 7. Reproducibilidad

```bash
python tools/audit_cohort_2025.py \
  --input data/raw/ocds/2024.jsonl.gz \
  --output docs/cohort-2024.json \
  --year 2024

python tools/audit_cohort_2025.py \
  --input data/raw/ocds/2025.jsonl.gz \
  --output docs/cohort-2025.json \
  --year 2025

python -m contratamype run \
  --input data/raw/ocds/2024.jsonl.gz \
  --input data/raw/ocds/2025.jsonl.gz \
  --artifacts artifacts/2024-2025 \
  --db data/processed/contratamype.duckdb
```

Artefactos: `docs/data-profile-2025.json`, `docs/data-profile-2025.md` (este
documento), `docs/cohort-2024.json` y `docs/cohort-2025.json`. Los SHA-256 de
ambos bulks están en los JSON, en `data/raw/README.md` y en el manifest. Los
cohort JSON son auditorías por archivo aislado; la cohorte fusionada se mide en
el pipeline y en este documento.

## 8. Integridad referencial contracts → awards (bulk completo)

- **11,274 de 195,583 contratos (5.8%)** referencian un `awardID` que no aparece
  en el `compiledRelease`; en el snapshot 2025 son 5,128 de 107,301,
  distribuidos en 3,855 OCIDs.
- El 100% de los contratos trae `awardID` no vacío
  (`contracts_without_award = 0` en la cohorte); la brecha es de referencia, no
  de campo.
- **Decisión:** `contract_award_linked` es un check **warn**, no bloqueante. El
  snapshot no permite reconstruir el award faltante y fabricarlo violaría la
  fuente. El conteo y la muestra quedan en `quality_report.json`; la app debe
  mostrar el contrato sin inventar proveedor.
- Los checks **fail** que bloquean exports son: esquema raw (parseo, OCID,
  `tender` y título), OCID único en `tenders`, comprador, categoría,
  departamento, fechas parseables y monto no negativo.
- `supplier_address_present` es **warn**: los 91,879 proveedores de ambos bulks
  no traen departamento. Es una limitación de la fuente, no del pipeline.

## 9. Limitaciones

- Dos snapshots de actualizaciones, no una serie histórica limpia; la cohorte
  fusionada suma las filas segmentadas a 2024/2025 de ambos archivos.
- Algunos procesos 2024 solo aparecen en el snapshot 2025 (18,455 filas) y 7
  procesos 2025 solo aparecen en el snapshot 2024. Son datos válidos y se
  cuentan; el dedupe por OCID evita duplicados.
- Fechas de plazo incompletas o con inicio = fin (100% de la cohorte sin
  cronograma utilizable).
- Proveedores sin `address.department`: 100% en ambos bulks. No se imputa
  región.
- La API es beta y puede cambiar; el spot-check API-vs-bulk no corre en el
  pipeline.
- Los nombres de entidades/proveedores pueden tener ruido de codificación.
- Este perfil describe datos, no elegibilidad legal ni calidad de la gestión.
