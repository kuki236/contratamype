# AGENTS.md — ContrataMYPE

## 1. Lee esto antes de tocar código

1. `SPECS.md`
2. `ROADMAP.md`
3. `CODESTYLE.md`
4. `README.md`
5. `AGENTS.md`

Si hay contradicción: `SPECS.md` manda sobre producto; `AGENTS.md` sobre proceso; `CODESTYLE.md` sobre forma.

## 2. Rol y estándar

Tu trabajo está siendo evaluado por **Linus Torvalds**. Puede despedirte si haces lo incorrecto. Principios:

- Corrección y simplicidad por encima de elegancia.
- No agregues abstracciones que no resuelvan un problema real.
- No dejes código muerto, TODOs sin dueño ni comentarios que narran lo obvio.
- Si no sabes qué es lo correcto, **detente y propón 2–3 opciones con tradeoffs**.
- Si un requisito es ambiguo, pregunta antes de implementar.
- No ocultes fallos en logs, README ni métricas.
- Deja el código mejor de como lo encontraste.

## 3. Testing — obligatorio

- **Nunca** escribas unit tests después de escribir el código.
- Prefiere **E2E** como mecanismo principal; al final, un artefacto verificable y repetible.
- Si pruebas algo aislado, **primero** enumera las formas en que puede fallar; **después** escribe el código.
- Tests tautológicos y change-detector: prohibidos.
- No tests de regresión sin una brecha real de comportamiento.
- E2E con escenario **medio-difícil**, no el camino feliz.
- No maquilles fixtures para hacer pasar un test.

### E2E del proyecto

- **Pipeline:** dataset determinista con duplicados, monto 0, fecha inicio=fin, award sin contrato, proveedor sin dirección y categoría inválida; 10–12 validaciones con conteos exactos; artefactos con checksums.
- **Web:** Playwright con datos sembrados; búsqueda, detalle, PDF, estados vacíos y datos incompletos.
- **Power BI:** PBIR válido + capturas Desktop; no se acepta solo `validate`.

### Tiers de test — rápido vs lento (obligatorio)

No corras la suite entera en cada cambio. El default es rápido:

| Tier | Comando | Cuándo | Qué cubre |
|---|---|---|---|
| **Fast** | `pytest -m fast` | Después de **cada cambio**; segundos | Fixtures deterministas del pipeline, quality report, gate, exports y CLI. Sin bulk. |
| **Slow** | `pytest -m slow` | Solo en un **checkpoint** o antes de release; minutos | Bulk 2025 real (124,538 actualizaciones / 59,141 cohorte). Local; el bulk está gitignored. |
| **Full** | `pytest -m "fast or slow"` | Antes de cerrar un checkpoint/release | Fast + slow. No en cada edición. |
| **Power BI** | `powerbi-report-author validate ...` + capturas | Al tocar el dashboard | PBIR/PBIP, Desktop y screenshots. |

`pytest.ini` excluye `slow` por defecto (`addopts = -m "not slow"`). CI corre solo fast; el bulk es local. Si un test lento no puede correr (bulk ausente), se salta con un mensaje explícito, no se borra.

## 4. Boundaries

- `contratamype/` (Python) es la única fuente del modelo y la calidad.
- `web/` (Next.js) lee PostgreSQL/API; no recalcula reglas de negocio ni duplica la regla MYPE.
- `dashboard/` (Power BI) lee exports del pipeline; no consulta la base de la web.
- `docs/` contiene decisiones, diccionario y evidencia.
- El LLM solo explica campos oficiales; no decide elegibilidad.

## 5. Datos y ética

- Fuente: OCDS/OECE, datos abiertos CC BY 4.0; bulk/API. **No scraping** de SEACE/OECE.
- `data/raw/` y `data/processed/` no se commitean; solo procedencia y hashes.
- No PII innecesaria; RUC de proveedores es público.
- La regla MYPE es una heurística de compatibilidad, **no asesoría legal**.
- Alertas solo con consentimiento y deduplicadas.
- Atribución CC BY 4.0 y enlace a la fuente.

## 6. Flujo de trabajo

1. Abre el checkpoint actual en `ROADMAP.md`.
2. Escribe el E2E del comportamiento.
3. Implementa lo mínimo para que pase.
4. Ejecuta el E2E y genera artefactos con checksums.
5. Actualiza el checkbox del ROADMAP.
6. Actualiza README/docs si cambió algo visible.
7. `ruff format/check`, ESLint/Prettier.
8. Commit convencional.
9. Pasa al siguiente checkpoint.

No saltes checkpoints. No commitees con tests rojos. No dejes artefactos sin checksums.

## 7. Commits

```text
feat: add ocds ingestion
test: add medium-hard pipeline e2e
feat: add mype search
docs: add data dictionary
chore: release v1.0.0
```

- Inglés, imperativo, corto.
- Un commit por checkpoint significativo.
- Formatear antes de commitear.

## 8. Cuándo detenerte y preguntar

- Un requisito es ambiguo.
- El formato OCDS real no coincide con el contrato.
- Un test falla y no entiendes por qué.
- Hay riesgo legal (elegibilidad, asesoría, datos personales).
- Necesitas una API key, licencia de Power Automate o credencial.
- Una decisión afecta el alcance de v1.0.0.
- Necesitas romper un boundary.

## 9. Definición de terminado

- El E2E del checkpoint pasa y el artefacto es reproducible.
- `ROADMAP.md` tiene el checkbox marcado.
- README/docs actualizados.
- `ruff`/ESLint/Prettier pasan.
- No hay datos crudos, secretos ni PII innecesaria.
- Commit hecho.
