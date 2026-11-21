# data/raw — Procedencia del bulk OCDS 2025

> Esta carpeta está **gitignored**: el bulk no se commitea. Este README sí.

## Archivo

| Dato | Valor |
|---|---|
| Fuente | OECE — Portal de Contrataciones Abiertas (OCDS) |
| URL | `https://data.open-contracting.org/es/publication/135/download?name=2025.jsonl.gz` |
| Descarga | 20/11/2026 |
| Formato | JSONL comprimido (`.jsonl.gz`), un proceso por línea |
| Bytes | 148,719,573 |
| SHA-256 | `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b` |
| Registros | 124,538 actualizaciones de 2025 |
| Cohorte 2025 | 59,141 procesos con `dataSegmentation.id` 2025 |
| Licencia | CC BY 4.0 |

## Estructura OCDS usada

- `ocid`, `date`, `dataSegmentation.id`/`criteria`.
- `buyer` y `parties[]` (RUC/departamento en `address`).
- `tender`: título, descripción, `mainProcurementCategory`, método, valor `amount_PEN`, `tenderPeriod`.
- `awards[]` y `contracts[]`.

## Lectura importante

El archivo anual es un **snapshot de actualizaciones**: incluye procesos de años anteriores que fueron modificados en 2025. No se debe usar el total de 124,538 como “procesos 2025”. La cohorte 2025 es `dataSegmentation.id` 2025 = **59,141**.

## API

- Base: `https://contratacionesabiertas.oece.gob.pe/api/v1` (beta).
- `GET /records?sourceId=seace_v3&dataSegmentationID=YYYY-MM&page=N` — 20 procesos/página.
- Sin filtro nativo por departamento; `parties[].address.department` se filtra del lado del cliente.
- Spot-check: 20 registros de 2025-01; 9 encontrados en el bulk, 0 diferencias; 11 no estaban porque la API está más fresca.

## Calidad conocida

Montos 0, `tenderPeriod` con inicio = fin, períodos faltantes, awards sin proveedor, ruido de codificación. El perfil completo está en `docs/data-profile-2025.md`; los JSON con checksums en `docs/data-profile-2025.json` y `docs/cohort-2025.json`.

## Atribución

Fuente: OECE — Portal de Contrataciones Abiertas, datos en estándar OCDS, redistribuidos por el Registro de Datos de Open Contracting Partnership bajo CC BY 4.0. ContrataMYPE no está afiliado al OECE.
