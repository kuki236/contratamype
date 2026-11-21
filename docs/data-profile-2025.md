# Perfil de datos OCDS 2025

> **Fuente:** OECE — Portal de Contrataciones Abiertas, estándar OCDS.
> **Archivo:** `data/raw/ocds/2025.jsonl.gz` (no se commitea).
> **Descarga:** 20/11/2026 desde el Registro de Datos de Open Contracting Partnership.
> **Licencia:** CC BY 4.0.

## 1. Archivo y hashes

| Dato | Valor |
|---|---|
| URL | `https://data.open-contracting.org/es/publication/135/download?name=2025.jsonl.gz` |
| Bytes | 148,719,573 |
| SHA-256 | `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b` |
| Líneas / registros | 124,538 |
| OCIDs únicos | 124,538 |
| Rango de actualización | 2025-01-03 → 2025-12-31 |

**Lectura clave:** el archivo anual es un **snapshot de actualizaciones de 2025**, no una cohorte de procesos iniciados en 2025. Incluye procesos antiguos que fueron actualizados durante 2025. La fecha oficial de segmentación se publica en `dataSegmentation.id` (criterios: año/mes de inicio de convocatoria o de publicación).

## 2. Cohorte 2025 (`dataSegmentation` 2025)

| Métrica | Valor |
|---|---:|
| Procesos | **59,141** |
| Awards | 47,115 |
| Contratos | 42,650 |
| Categorías | `goods` 26,982 · `services` 25,485 · `works` 6,674 |
| Lima | 16,320 |
| Cusco | 5,052 |
| Áncash | 3,242 |
| Puno | 3,063 |
| Ayacucho | 2,875 |
| Junín | 2,680 |

**Montos (PEN):** mediana 145,694.87; p90 1,117,307.65; p99 14,756,943.06; máximo 1,134,909,484.19.

| Umbral | Procesos ≤ umbral | % de la cohorte |
|---|---:|---:|
| ≤ S/ 50,000 | 8,158 | 13.8% |
| ≤ S/ 100,000 | 22,923 | 38.8% |
| ≤ S/ 200,000 | 35,311 | 59.7% |
| ≤ S/ 400,000 | 45,237 | 76.5% |
| ≤ S/ 1,000,000 | 52,649 | 89.0% |

Estos buckets son **solo de monto**: incluyen procesos con monto 0 y obras, por
lo que no equivalen a `mype_fit`. La regla MYPE final se mide en §5.

**Métodos principales:** Adjudicación Simplificada 13,929; Licitación Pública Abreviada 10,227; Concurso Público Abreviado 9,380; Subasta Inversa Electrónica 7,193; Comparación de Precios 5,097; Contratación Directa 3,516.

## 3. Calidad

| Regla | Global (124,538) | Cohorte 2025 (59,141) |
|---|---:|---:|
| `amount_zero` | 8,586 (6.9%) | 4,952 (8.4%) |
| `period_missing` | 7,703 (6.2%) | 3,975 (6.7%) |
| `period_start_eq_end` | 116,832 (93.8%) | 55,166 (93.3%) |
| `period_quality` (faltante o inicio = fin) | 124,535 (99.998%) | 59,141 (100%) |
| `awards_without_supplier` | 1,741 | 62 |
| `contracts_without_award` | 0 | 0 |
| `missing_department` | 0 | 0 |
| `invalid_category` | 0 | 0 |
| `amount_missing` | 0 | 0 |

**Proveedores sin dirección:** 56,734 de 56,734 (100%) tienen
`department` nulo. Las partes proveedoras del bulk suelen traer solo
`countryName`. Es una limitación de la fuente, no un error del pipeline; el
check `supplier_address_present` la reporta como warn y no se inventa el
departamento.

**Implicaciones de producto:**
- El **plazo** no es confiable: en 100% de la cohorte falta el período o
  `tenderPeriod.startDate == endDate`. La app debe mostrar “fecha de referencia”
  y enlace al portal oficial; las alertas se basan en **oportunidades nuevas**,
  no en cuentas regresivas.
- 8.4% tiene monto 0: mostrar “monto no informado”, no S/ 0. La regla MYPE
  excluye esos registros.
- Los `awards` sin proveedor son 0.13% en la cohorte; el resto se puede modelar.

## 4. API vs bulk (spot-check)

- Se compararon 20 registros de la API (`sourceId=seace_v3`, `dataSegmentationID=2025-01`, página 1) contra el bulk.
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
- **Resultado bulk 2025: 29,921 procesos compatibles (50.6% de la cohorte de
  59,141).** Son 4,565 menos que la versión anterior de la regla, que incluía
  montos 0; los 387 restantes de `amount_zero` de la cohorte son obras, que no
  están en el rubro objetivo.
- La tabla de umbrales de §2 es solo de **monto** (incluye 0 y obras) y no debe
  citarse como participación MYPE. Bajo la regla final, el umbral de S/ 200,000
  deja una oportunidad compatible en 50.6% de la cohorte.
- Alternativas de umbral (solo monto): S/ 100,000 (38.8%, más selectivo) o
  S/ 400,000 (76.5%, demasiado amplio para llamarlo MYPE).
- El umbral se guarda en configuración y en el bloque `settings` de
  `run_manifest.json`; no se hardcodea en la web.

## 6. Decisión de alcance v1.0.0

- **2025** como año de la cohorte (`dataSegmentation` 2025, 59,141 procesos).
- Cargar los 124,538 registros con `segmentation_year` para búsqueda/historia, pero el dashboard y el buscador por defecto filtran 2025.
- **2024–2025** se difiere a v1.1: requiere el bulk 2024 y deduplicar OCIDs entre snapshots.
- **Sin Spark:** 150 MB y 124k procesos se procesan con Python + DuckDB/PostgreSQL.

## 7. Reproducibilidad

```bash
python tools/audit_ocds.py \
  --input data/raw/ocds/2025.jsonl.gz \
  --output-dir docs

python tools/audit_cohort_2025.py \
  --input data/raw/ocds/2025.jsonl.gz \
  --output docs/cohort-2025.json \
  --year 2025
```

Artefactos: `docs/data-profile-2025.json`, `docs/data-profile-2025.md` y `docs/cohort-2025.json`. El SHA-256 del bulk está en ambos JSON.

## 8. Integridad referencial contracts → awards (bulk completo)

- **5,128 de 107,301 contratos (4.8%)** referencian un `awardID` que no aparece en el `compiledRelease`, distribuidos en 3,855 OCIDs.
- El 100% de los contratos trae `awardID` no vacío (`contracts_without_award = 0` en la cohorte); la brecha es de referencia, no de campo.
- **Decisión:** `contract_award_linked` es un check **warn**, no bloqueante. El snapshot no permite reconstruir el award faltante y fabricarlo violaría la fuente. El conteo y la muestra quedan en `quality_report.json`; la app debe mostrar el contrato sin inventar proveedor.
- Los checks **fail** que bloquean exports son: esquema raw (parseo, OCID, `tender` y título), OCID único, comprador, categoría, departamento, fechas parseables y monto no negativo.
- `supplier_address_present` es **warn**: los 56,734 proveedores del bulk no traen departamento. Es una limitación de la fuente, no del pipeline.

## 9. Limitaciones

- Un solo año y un snapshot de actualizaciones; no es una serie histórica limpia.
- Fechas de plazo incompletas o con inicio = fin (100% de la cohorte sin cronograma utilizable).
- Proveedores sin `address.department`: 100% en el bulk. No se imputa región.
- La API es beta y puede cambiar; el spot-check API-vs-bulk no corre en el pipeline.
- Los nombres de entidades/proveedores pueden tener ruido de codificación.
- Este perfil describe datos, no elegibilidad legal ni calidad de la gestión.
