# CODESTYLE — ContrataMYPE

> **Regla de oro:** código en inglés, UI/documentación en español, nombres claros, cero adornos.

## 1. Idioma y nombres

- Código, tablas, columnas, variables, funciones, commits: **inglés**.
- UI, mensajes, documentación, hallazgos: **español**.
- Nombres descriptivos; evitar abreviaturas opacas (`buyer`, no `b`).
- Fechas en ISO 8601; montos en `PEN` con `decimal`/`numeric`, nunca `float` para dinero.

## 2. Python

- Python 3.13; `ruff format` y `ruff check`.
- Type hints en funciones públicas; `pathlib` para rutas.
- DuckDB/PyArrow para el audit, las transformaciones y el serving local; PostgreSQL 17 como adaptador pendiente.
- Sin Spark: el bulk anual no lo justifica.
- Comentarios solo para decisiones no obvias; no narrar lo que el código ya dice.
- Errores explícitos con contexto; no silenciar excepciones.
- Tests E2E primero; no unit tests después del código.

## 3. TypeScript / Next.js

- Next.js App Router; TypeScript `strict`.
- Server Components por defecto; `"use client"` solo cuando haga falta interactividad.
- ESLint + Prettier; sin `any` injustificado.
- Acceso a datos en `lib/` o `server/`; no lógica de negocio en componentes de presentación.
- Componentes pequeños y accesibles; teclado y contraste AA.
- No duplicar la regla MYPE: una sola función/configuración compartida.

## 4. Datos y boundaries

- `data/raw/` gitignored; `data/processed/` gitignored.
- Pipeline Python es la única fuente de verdad del modelo; la web lee PostgreSQL/API, no recalcula reglas de negocio.
- Power BI lee Parquet/CSV exportados por el pipeline; no consulta la base de la web.
- El LLM no decide elegibilidad; solo explica campos oficiales con citas y disclaimer.
- Secretos en `.env`, nunca en Git; `.env.example` documenta las variables.

## 5. Testing

- **E2E primero.** Antes de implementar una feature, escribir el escenario que describe el comportamiento.
- Pipeline: pytest E2E con un dataset determinista medio-difícil (duplicados, monto 0, fecha inicio=fin, award sin contrato, proveedor sin dirección, categoría inválida).
- Web: Playwright E2E con datos sembrados; búsqueda, detalle, PDF y estados vacíos.
- Power BI: `powerbi-report-author validate` + capturas; no se acepta solo “valida”.
- Artefactos verificables con checksums; nada de tests tautológicos o change-detector.
- No crear tests de regresión sin una brecha real de comportamiento.

## 6. Git y commits

- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `chore:`.
- Un commit por checkpoint significativo; no mezclar refactor grande con feature.
- Formatear antes de commitear.
- No commitear datos crudos, secretos, `node_modules`, `.next`, `artifacts/` generados.

## 7. Rendimiento y operación

- El bulk 2025 es ~150 MB comprimido; el audit debe correr en minutos, no horas.
- Paginación de API con pausas y User-Agent; no abusar del endpoint beta.
- Logs estructurados y tiempos por fase; manifest del run.
- Local-first; cloud solo si aporta y se documenta.

## 8. Seguridad y ética

- No asesoría legal; disclaimers visibles.
- No PII innecesaria; RUC de proveedores es dato público, pero no enriquecer con datos personales.
- No spam: alertas solo con consentimiento y deduplicadas.
- Atribución CC BY 4.0 y enlace a la fuente oficial.
