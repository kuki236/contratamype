# Hallazgos del mercado 2024–2025 — ContrataMYPE

Cohortes `dataSegmentation` 2024 y 2025, después de deduplicar OCIDs entre los
dos snapshots. Las cifras salen de `data/processed/contratamype.duckdb` y del
`run_manifest.json` del pipeline v1.1.0.

## 1. Titular

- **123,931 procesos** por **S/ 158,343,983,740.46**.
- **58,380 procesos (47.1%)** cumplen la heurística MYPE.
- Esos procesos suman **S/ 5,773,289,671.05**, solo **3.6% del monto total**.
- Mediana del proceso: **S/ 145,600.00**.

## 2. Por año

| Año | Procesos | Monto (S/) | MYPE | % MYPE | Monto MYPE (S/) |
|---|---:|---:|---:|---:|---:|
| 2024 | 64,783 | 91,704,508,196.24 | 28,458 | 43.9% | 2,820,459,891.02 |
| 2025 | 59,148 | 66,639,475,544.22 | 29,922 | 50.6% | 2,952,829,780.03 |
| **Total** | **123,931** | **158,343,983,740.46** | **58,380** | **47.1%** | **5,773,289,671.05** |

La cohorte 2024 incluye **18,455 filas segmentadas 2024 que llegan actualizadas
en el snapshot 2025**; la 2025 incluye 7 filas segmentadas 2025 que aparecen en
el snapshot 2024. Se conservan porque son procesos válidos; `snapshot_year` solo
se usa para deduplicar.

## 3. Por categoría

| Categoría | Procesos | Monto (S/) | MYPE |
|---|---:|---:|---:|
| goods | 56,420 | 23,921,099,222.49 | 29,782 |
| services | 54,120 | 35,854,104,352.56 | 28,598 |
| works | 13,391 | 98,568,780,165.41 | 0 |

`goods` y `services` concentran la MYPE; `works` explica la brecha de monto.

## 4. Cobertura y calidad

- **14,335 procesos (11.6%)** tienen monto 0 (no informado); no se marcan MYPE.
- **116,384 (93.9%)** registran inicio = fin del período; se reporta.
- **94,570 procesos (76.3%)** tienen al menos un award.
- **85,496 (69.0%)** tienen al menos un contrato.
- **12 checks:** 7 pass / 5 warn / 0 fail.
- Auditorías: 24/24 meses, 25/25 regiones, API-vs-bulk `not_run` (offline).

## 5. Reproducción

```powershell
python -m contratamype run `
  --input data/raw/ocds/2024.jsonl.gz `
  --input data/raw/ocds/2025.jsonl.gz `
  --artifacts artifacts/2025 `
  --db data/processed/contratamype.duckdb
```

El manifest registra ambos inputs y sus hashes:

- 2024: `9f50c84423c65605b4280d2d88b9da0853ebeb0b556d2dedf66add435cbde6e0`
- 2025: `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b`

## 6. Límites

- La heurística MYPE es compatibilidad por monto/rubro, no elegibilidad legal.
- El monto es el valor referencial del `tender`, no el adjudicado.
- El bulk es un snapshot de actualizaciones; la API puede estar más fresca.
- v1.1 no promete una serie 2013–2023; esas filas quedan fuera de la cohorte.
