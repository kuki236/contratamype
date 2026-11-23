# data/raw — Procedencia de los bulks OCDS 2024 y 2025

> Esta carpeta está **gitignored**: los bulks no se commitean. Este README sí.

## Archivos

| Dato | 2024 | 2025 |
|---|---:|---:|
| Fuente | OECE — Portal de Contrataciones Abiertas (OCDS) | OECE — Portal de Contrataciones Abiertas (OCDS) |
| URL | `https://data.open-contracting.org/es/publication/135/download?name=2024.jsonl.gz` | `https://data.open-contracting.org/es/publication/135/download?name=2025.jsonl.gz` |
| Descarga | 20/11/2026 | 20/11/2026 |
| Formato | JSONL comprimido (`.jsonl.gz`), un proceso por línea | JSONL comprimido (`.jsonl.gz`), un proceso por línea |
| Bytes | 125,638,249 | 148,719,573 |
| SHA-256 | `9f50c84423c65605b4280d2d88b9da0853ebeb0b556d2dedf66add435cbde6e0` | `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b` |
| Registros | 108,451 actualizaciones | 124,538 actualizaciones |
| Cohorte same-year (auditoría) | 46,328 procesos con `dataSegmentation.id` 2024 | 59,141 procesos con `dataSegmentation.id` 2025 |
| Cohorte fusionada | **64,783** | **59,148** |
| Licencia | CC BY 4.0 | CC BY 4.0 |

La cohorte fusionada después del dedupe por OCID es
**64,783 + 59,148 = 123,931 procesos**.

## Cohorte fusionada y snapshots

Cada archivo anual es un **snapshot de actualizaciones**: incluye procesos de
años anteriores que fueron modificados en ese año. Además trae filas cuyo
`dataSegmentation` pertenece a otro año: 18,455 con 2024 dentro del archivo 2025
y 7 con 2025 dentro del archivo 2024. Son actualizaciones válidas y se cuentan:
la cohorte 2024 pasa de 46,328 a **64,783**; la cohorte 2025 pasa de 59,141 a
**59,148**.

No se debe usar 108,451 ni 124,538 como “procesos 2024/2025”. Esos son registros
del snapshot. Las auditorías same-year por archivo dan 46,328 y 59,141; la
cohorte fusionada del pipeline es 64,783 y 59,148.

## Estructura OCDS usada

- `ocid`, `date`, `dataSegmentation.id`/`criteria`.
- `buyer` y `parties[]` (RUC/departamento en `address`).
- `tender`: título, descripción, `mainProcurementCategory`, método, valor `amount_PEN`, `tenderPeriod`.
- `awards[]` y `contracts[]`.

## API

- Base: `https://contratacionesabiertas.oece.gob.pe/api/v1` (beta).
- `GET /records?sourceId=seace_v3&dataSegmentationID=YYYY-MM&page=N` — 20 procesos/página.
- Sin filtro nativo por departamento; `parties[].address.department` se filtra del lado del cliente.
- Spot-check: 20 registros de 2025-01; 9 encontrados en el bulk 2025, 0 diferencias; 11 no estaban porque la API está más fresca.

## Calidad conocida

Montos 0 (14,335 en la cohorte fusionada: 9,383 en 2024 y 4,952 en 2025),
`tenderPeriod` con inicio = fin, períodos faltantes, awards sin proveedor (2,779
en la cohorte), ruido de codificación y 11,274 contratos con award ausente en el
bulk completo. El perfil completo está en `docs/data-profile-2025.md`; los JSON
con checksums en `docs/data-profile-2025.json`, `docs/cohort-2024.json` y
`docs/cohort-2025.json`. Los cohort JSON son auditorías por archivo aislado.

## Atribución

Fuente: OECE — Portal de Contrataciones Abiertas, datos en estándar OCDS, redistribuidos por el Registro de Datos de Open Contracting Partnership bajo CC BY 4.0. ContrataMYPE no está afiliado al OECE.
