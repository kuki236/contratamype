# Release local — ContrataMYPE v1.0.0

El repositorio es local y todavía no tiene remoto. El release se construye como
un bundle verificable en `dist/v1.0.0/` y se etiqueta en Git. Cuando exista
remoto, se publican los mismos archivos como assets.

## 1. Prerrequisitos

- Bulk 2025 en `data/raw/ocds/2025.jsonl.gz` (gitignored).
- Entorno Python: `.venv` con `pip install -e ".[dev]"`.
- Power BI Desktop para refrescar/validar el PBIP y capturar pantallas.
- Node 24 para la web.

## 2. Secuencia

```bash
# 1. Pipeline real
python -m contratamype run \
  --input data/raw/ocds/2025.jsonl.gz \
  --artifacts artifacts/2025 \
  --db data/processed/contratamype.duckdb

# 2. Tests completos (solo en checkpoint/release)
pytest -m "fast or slow"

# 3. Bundle
python scripts/build_release.py --version v1.0.0

# 4. Verificar checksums
python - <<'PY'
from pathlib import Path
import hashlib
root = Path("dist/v1.0.0")
for line in (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    digest, name = line.split("  ", 1)
    actual = hashlib.sha256((root / name).read_bytes()).hexdigest()
    assert actual == digest, name
print("checksums OK")
PY

# 5. Tag local
git tag -a v1.0.0 -m "ContrataMYPE v1.0.0"
```

## 3. Contenido esperado

| Ruta | Contenido |
|---|---|
| `artifacts/` | `quality_report.json`, `run_manifest.json`, `checksums.sha256`, Parquet, `mype_opportunities.csv` |
| `dashboard/` | PBIP/PBIX y capturas revisadas |
| `docs/` | README, diccionario, arquitectura, perfil, límites |
| `RELEASE_NOTES.md` | cifras y estado del gate |
| `SHA256SUMS` | hash de cada archivo |

El bundle **no** incluye el bulk crudo, la base DuckDB ni secretos.

## 4. Criterios de aceptación

- [ ] `pytest -m "fast or slow"` verde.
- [ ] Gate abierto (0 fails) y `run_manifest.json` con SHA del bulk.
- [ ] `checksums.sha256` recomputado coincide.
- [ ] Web: búsqueda, detalle, checklist/PDF y estado vacío probados con Playwright.
- [ ] Power BI: `powerbi-report-author validate` 0/0 y capturas de ambas páginas.
- [ ] Digest real: primera corrida envía, segunda envía 0.
- [ ] Sin datos crudos, secretos ni PII innecesaria en Git.
- [ ] README ES/EN y ROADMAP actualizados.

## 5. Limitaciones del release local

- Power BI no se publica en Service (v1.1).
- PostgreSQL queda como adaptador pendiente; la API local usa DuckDB.
- El test con una persona MYPE es manual y se registra aparte.
