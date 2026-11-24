# Release local — ContrataMYPE v1.1.1

El repositorio está publicado en GitHub (`tejedasebastian/contratamype`). El release se
construye como un bundle verificable en `dist/v1.1.1/` y se publica como assets
del tag. El bundle incluye las cohortes 2024 + 2025.

## 1. Prerrequisitos

- Bulks 2024 y 2025 en `data/raw/ocds/` (gitignored).
- Entorno Python: `.venv` con `pip install -e ".[dev]"`.
- Power BI Desktop para refrescar/validar el PBIP y capturar pantallas.
- Node 24 para la web.
- `gh` autenticado para publicar el release.

## 2. Secuencia

```powershell
# 1. Pipeline real (dos snapshots)
python -m contratamype run `
  --input data/raw/ocds/2024.jsonl.gz `
  --input data/raw/ocds/2025.jsonl.gz `
  --artifacts artifacts/2025 `
  --db data/processed/contratamype.duckdb

# 2. Tests completos (solo en checkpoint/release)
pytest -m "fast or slow"

# 3. Bundle
python scripts/build_release.py --version v1.1.1 --notes-file docs/release-notes-v1.1.1.md

# 4. Verificar el bundle (exit 1 si algo falla)
python scripts/verify_release.py --root dist/v1.1.1

# 5. Tag y release
git tag -a v1.1.1 -m "ContrataMYPE v1.1.1"
git push origin v1.1.1
gh release create v1.1.1 --title "ContrataMYPE v1.1.1" --notes-file dist/v1.1.1/RELEASE_NOTES.md

# 6. PBIX como asset (no se commitea; sale del export manual de Desktop)
gh release upload v1.1.1 ruta\a\ContrataMYPE.pbix
```

`build_release.py` valida y verifica los artefactos del pipeline antes de
reemplazar el bundle anterior; si algo falla, el bundle previo queda intacto.
`--notes-file` reemplaza las notas generadas (útil en patch releases).
`verify_release.py` revisa `SHA256SUMS`, los archivos requeridos, la ausencia de
`data/raw` y `.env`, e imprime un resumen JSON con `ok`, `files`,
`checksums_verified` y `errors`.

## 3. Contenido esperado

| Ruta | Contenido |
|---|---|
| `artifacts/` | `quality_report.json`, `run_manifest.json`, `checksums.sha256`, Parquet, `mype_opportunities.csv` |
| `dashboard/` | PBIP, capturas y script de build; el `.pbix` se sube como asset del release |
| `docs/` | README, diccionario, arquitectura, perfil, límites |
| `RELEASE_NOTES.md` | cifras y estado del gate |
| `SHA256SUMS` | hash de cada archivo |

El bundle **no** incluye el bulk crudo, la base DuckDB ni secretos.

## 4. Criterios de aceptación

- [ ] `pytest -m "fast or slow"` verde.
- [ ] Gate abierto (0 fails) y `run_manifest.json` con SHA del bulk válido.
- [ ] `scripts/verify_release.py --root dist/v1.1.1` retorna 0 y `checksums_verified` cubre todo el bundle.
- [ ] Web: búsqueda, detalle, checklist/PDF y estado vacío probados con Playwright.
- [ ] Power BI: `powerbi-report-author validate` 0/0 y capturas de ambas páginas.
- [ ] Digest real: primera corrida envía, segunda envía 0.
- [ ] Sin datos crudos, secretos ni PII innecesaria en Git.
- [ ] README ES/EN y ROADMAP actualizados.

## 5. Limitaciones del release local

- Power BI no se publica en Service (v1.1).
- PostgreSQL queda como adaptador pendiente; la API local usa DuckDB.
- El test con una persona MYPE es manual y se registra aparte.
