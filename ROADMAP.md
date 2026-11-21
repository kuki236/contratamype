# ROADMAP — ContrataMYPE

> **Regla:** no se avanza de fase sin el E2E de la fase y su artefacto verificable.
> **Estado:** Fase 0 (docs) en curso; Fase 1 (audit) arranca con el bulk 2025.

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

- [ ] Descargar el bulk 2025 (`2025.jsonl.gz`, ~148.7 MB) y registrar SHA-256.
- [ ] Perfilar: procesos, OCIDs únicos, fechas, categorías, departamentos, compradores, proveedores, awards, contracts.
- [ ] Medir calidad: nulos, montos 0, duplicados, fechas inicio=fin, awards/contracts sin vínculo, proveedores sin dirección.
- [ ] Analizar distribución de montos para elegir el umbral MYPE.
- [ ] Decidir ventana v1.0.0: 2025 solo o 2024–2025.
- [ ] Escribir `docs/data-profile-2025.md` y `data/raw/README.md` (procedencia).
- [ ] Spot-check API vs bulk en un mes.

**E2E del checkpoint:**
- El perfil se regenera desde el bulk con un comando y produce un JSON/Markdown con conteos y checksums.
- El bulk no se commitea; el README y el perfil sí.

**Criterio:** números reales, no estimaciones; decisión de ventana documentada.

## Fase 2 — Pipeline, modelo y calidad

- [ ] Ingesta OCDS → normalización → star schema.
- [ ] PostgreSQL 17 para la app; Parquet/CSV para Power BI.
- [ ] 10–12 validaciones con reporte y gate.
- [ ] `run_manifest.json` con SHA-256 del bulk y checksums de los payloads.
- [ ] E2E con escenario medio-difícil (duplicados, monto 0, fecha inicio=fin, award sin contrato, proveedor sin dirección, categoría inválida).

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

- [ ] App Router + TypeScript + Tailwind.
- [ ] Búsqueda por texto/región/rubro/categoría/monto/estado.
- [ ] Detalle de oportunidad y MYPE fit.
- [ ] Checklist/PDF.
- [ ] Estados vacíos y datos incompletos explicados.
- [ ] Playwright E2E con dataset sembrado.

**E2E del checkpoint:**
- Búsqueda, filtro, detalle, PDF y estado vacío; una oportunidad con datos faltantes no rompe la UI.

**Criterio:** un usuario MYPE encuentra una oportunidad y entiende qué le falta sin leer código.

## Fase 5 — LLM y checklist

- [ ] Explicador acotado a campos oficiales, con citas y disclaimer.
- [ ] Gemini si hay API key; fallback plantilla si no.
- [ ] Evaluación con 10–20 oportunidades reales; no inventar requisitos.
- [ ] Checklist/PDF con pasos y documentos.

**E2E del checkpoint:**
- Para una oportunidad con datos completos y otra incompleta, el explicador cita la fuente y no afirma elegibilidad legal.

**Criterio:** el LLM no es una caja negra; se puede apagar y la app sigue funcionando.

## Fase 6 — Alertas

- [ ] Digest CSV/email de oportunidades nuevas compatibles.
- [ ] Adaptador Power Automate si hay licencia; si no, flujo documentado y simulable.
- [ ] Registro de alertas enviadas y no duplicadas.

**E2E del checkpoint:**
- Un conjunto de oportunidades nuevas genera un digest determinista; no se repiten alertas.

## Fase 7 — Release v1.0.0

- [ ] README ES/EN, diccionario de datos, arquitectura y ADRs.
- [ ] E2E completo (pipeline + web + Power BI) y artefactos con checksums.
- [ ] Tag `v1.0.0` y release con bulk manifest, CSVs, PBIX, capturas y reporte de calidad.
- [ ] Test con una persona MYPE y feedback registrado.

**Criterio:** se puede clonar, correr y entender el producto sin acceso al chat.
