# ROADMAP — ContrataMYPE

> **Regla:** no se avanza de fase sin el E2E de la fase y su artefacto verificable.
> **Estado:** v1.0.0 en preparación. Fases 0–2, 4 y 6 cerradas; Fase 3 (Power BI), Fase 5 (evaluación LLM) y Fase 7 (release) en integración.
> **Tests:** `pytest -m fast` después de cada cambio; `pytest -m slow` solo en checkpoint/release.

## Fase 0 — Documentos y boundaries

- [x] `SPECS.md` con problema, usuarios, alcance, fuente, modelo, calidad y E2E.
- [x] `ROADMAP.md` con checkpoints.
- [x] `README.md` del producto terminado.
- [x] `CODESTYLE.md` con reglas de código, formato, tests y commits.
- [x] `AGENTS.md` con las reglas de trabajo y los límites del proyecto.
- [x] `.gitignore` sin datos crudos ni secretos.
- [x] Repositorio Git inicial y commit `docs: add project specs and roadmap`.

**Criterio:** los cinco documentos existen y no hay código de producto antes de la Fase 1.

## Fase 1 — Auditoría de datos 2025

- [x] Descargar el bulk 2025 (`2025.jsonl.gz`, 148,719,573 bytes) y registrar SHA-256 (`65444cad…160b`).
- [x] Perfilar: 124,538 actualizaciones, 2,994 compradores, 56,734 proveedores, 174,101 postores.
- [x] Medir calidad: montos 0, período inicio=fin, awards sin proveedor, etc.
- [x] Analizar distribución de montos y elegir el umbral MYPE propuesto (S/ 200,000, configurable).
- [x] Decidir ventana v1.0.0: cohorte `dataSegmentation` 2025 = **59,141 procesos**; 2024–2025 a v1.1.
- [x] Escribir `docs/data-profile-2025.md`, `docs/data-profile-2025.json`, `docs/cohort-2025.json` y `data/raw/README.md`.
- [x] Spot-check API vs bulk: 20 registros, 9 encontrados, 0 diferencias; 11 ausentes porque la API está más fresca.

**Evidencia del checkpoint:**

- Bulk: 148,719,573 bytes; SHA-256 `65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b`.
- Global: 124,538 procesos actualizados; 59,141 en la cohorte 2025; 47,115 awards; 42,650 contratos.
- Cohorte: mediana S/ 145,694.87; 59.7% ≤ S/ 200k; 8.4% con monto 0; 93.3% con período inicio=fin.
- Herramientas: `tools/audit_ocds.py` y `tools/audit_cohort_2025.py` (streaming, stdlib).

**E2E del checkpoint:**
- El perfil se regenera desde el bulk con dos comandos y produce JSON/Markdown con el SHA-256 del input.
- El bulk no se commitea; el README y los perfiles sí.

**Criterio:** números reales, no estimaciones; decisión de ventana documentada.

## Fase 2 — Pipeline, modelo y calidad

- [x] Ingesta OCDS → normalización → star schema.
- [x] Star schema en DuckDB y exports Parquet/CSV para Power BI.
- [ ] PostgreSQL 17 para la app (se resuelve en Fase 4).
- [x] 10–12 validaciones con reporte y gate.
- [x] `run_manifest.json` con SHA-256 del bulk y checksums de los payloads.
- [x] E2E con escenario medio-difícil (duplicados, monto 0, fecha inicio=fin, award sin contrato, proveedor sin dirección, categoría inválida).

**Evidencia del checkpoint:**
- Bulk completo en **22.9 s**: 124,538 actualizaciones, 59,141 cohorte 2025, 34,486 oportunidades MYPE; gate abierto con 0 fails y 4 warns.
- Fast tier: 3 passed en 1.3 s. Slow tier: 1 passed en 22.8 s. El bulk nunca se commitea.

**E2E del checkpoint:**
- Las 10–12 validaciones detectan exactamente lo inyectado; el gate bloquea/publica según corresponda; los artefactos se recomputan y coinciden.

**Criterio:** el pipeline corre desde un clon limpio con datos de prueba; el bulk real solo en local.

## Fase 3 — Power BI

- [ ] Modelo TMDL con hechos/dimensiones y medidas.
- [ ] Página 1: mercado por región/rubro/monto/evolución/participación MYPE.
- [ ] Página 2: explorador de oportunidades con filtros y tabla.
- [ ] Tema, capturas y PBIP/PBIX.
- [ ] `powerbi-report-author validate` 0/0 + capturas Desktop.

**E2E del checkpoint:**
- PBIR válido, modelo refrescado con el dataset de prueba y capturas revisadas.

**Criterio:** el dashboard no duplica la búsqueda de la web app; cuenta la historia del mercado.

## Fase 4 — Web app Next.js

- [x] App Router + TypeScript + Tailwind.
- [x] Búsqueda por texto/región/rubro/categoría/monto/estado.
- [x] Detalle de oportunidad y MYPE fit.
- [x] Checklist/PDF.
- [x] Estados vacíos y datos incompletos explicados.
- [x] Playwright E2E con dataset sembrado.

**Evidencia del checkpoint:**
- Web + API read-only sobre DuckDB; `mype_fit` se lee, no se recalcula.
- **8/8 Playwright E2E en 23.7 s**, `npm run lint`, `npm run format:check` y `npm run build` verdes.
- PDF real (`application/pdf`, `%PDF`) generado con `pdf-lib`, sin servicios externos.
- Casos sembrados: descripción faltante, monto 0, inicio=fin, award sin proveedor, contrato con award colgante, departamento desconocido y estado vacío.

**E2E del checkpoint:**
- Búsqueda, filtro, detalle, PDF y estado vacío; una oportunidad con datos faltantes no rompe la UI.

**Criterio:** un usuario MYPE encuentra una oportunidad y entiende qué le falta sin leer código.

## Fase 5 — LLM y checklist

- [x] Explicador acotado a campos oficiales, con citas y disclaimer.
- [ ] Gemini si hay API key; fallback plantilla si no. **(fallback implementado; adaptador Gemini diferido por falta de key)**
- [ ] Evaluación con 10–20 oportunidades reales; no inventar requisitos.
- [x] Checklist/PDF con pasos y documentos.

**Evidencia del checkpoint:**
- Explicador por plantilla con cita de tabla/campo y disclaimer; `CONTRATAMYPE_EXPLAINER=gemini` cae a plantilla sin red ni key.
- Muestra reproducible de 15 oportunidades en `docs/llm-eval-sample-2025.json`; falta ejecutar la evaluación con la UI y registrar resultados.
- Checklist de 9 pasos y PDF real; no enumera requisitos que no estén en las bases.

**Criterio:** el LLM no es una caja negra; se puede apagar y la app sigue funcionando.

## Fase 6 — Alertas

- [x] Digest CSV/email de oportunidades nuevas compatibles.
- [x] Adaptador Power Automate si hay licencia; si no, flujo documentado y simulable.
- [x] Registro de alertas enviadas y no duplicadas.

**Evidencia del checkpoint:**
- `python -m contratamype digest` escribe CSV/JSON con `csv_sha256`, estado deduplicado y falla si el gate está bloqueado. Adaptador Power Automate documentado en `docs/alerts.md`; sin licencia confirmada, se simula localmente.

**E2E del checkpoint:**
- Un conjunto de oportunidades nuevas genera un digest determinista; no se repiten alertas.

## Fase 7 — Release v1.0.0

- [ ] README ES/EN, diccionario de datos, arquitectura y ADRs.
- [ ] E2E completo (pipeline + web + Power BI) y artefactos con checksums.
- [ ] Tag `v1.0.0` y release con bulk manifest, CSVs, PBIX, capturas y reporte de calidad.
- [ ] Test con una persona MYPE y feedback registrado.

**Criterio:** se puede clonar, correr y entender el producto sin acceso al chat.
