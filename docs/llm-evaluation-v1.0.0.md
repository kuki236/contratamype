# Evaluación del explicador — ContrataMYPE v1.0.0

> **Fecha de ejecución:** 2026-11-20
> **Explicador evaluado:** `template` (`web/lib/explainer.ts`), sin LLM ni API key.
> **Datos:** base real del pipeline (`data/processed/contratamype.duckdb`), cohorte 2025:
> 59,141 procesos y 29,921 marcados con `mype_fit = true`.
> **Muestra:** los 15 OCID reales de `docs/llm-eval-sample-2025.json`
> (3 completos, 3 con monto 0, 3 con inicio=fin, 3 sin award y 3 con contrato sin award).

## 1. Método

El script `web/scripts/evaluate-explainer.ts` hace, para cada OCID:

1. `GET http://127.0.0.1:8000/opportunities/{ocid}` contra la API real.
2. Ejecuta la misma función que usa la ficha web: `getExplainer()(detail)`.
3. Verifica criterios sobre la salida, no sobre el JSON de entrada:
   - **Citas:** los 8 puntos tienen `source` no vacío.
   - **Qué revisar:** existe un punto con ese nombre y cita las bases del proceso.
   - **Datos faltantes:** existe un punto con ese nombre que cita los flags
     `data_quality.*` y enumera cada vacío real del caso (descripción, monto,
     fechas, entidad, departamento, categoría, método, awards, contratos,
     proveedor, vínculo contrato–award, `mype_fit`, inicio=fin).
   - **Disclaimer:** contiene “heurística de compatibilidad MYPE” y
     “no elegibilidad legal”.
   - **Sin elegibilidad:** el texto completo no contiene afirmaciones como
     “elegible”, “puede postular”, “califica” o “cumple los requisitos”.

El script falla con código distinto de cero si un caso incumple un criterio.
Las 15 llamadas de detalle devolvieron HTTP 200 y el OCID devuelto coincidió con
el solicitado; el script aborta si la API falla o responde otro OCID.

## 2. Reproducción

Desde la raíz del repo:

```powershell
$env:CONTRATAMYPE_DB = "data/processed/contratamype.duckdb"
.\.venv\Scripts\python.exe -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

En otra terminal:

```powershell
cd web
npx tsx scripts/evaluate-explainer.ts
```

Salida esperada: 15 filas y `15/15 casos cumplen todos los criterios.`

## 3. Resultado por caso

| Bucket | OCID | Puntos | Citas | Qué revisar | Datos faltantes | Vacíos cubiertos | Disclaimer | Sin elegibilidad | Resultado |
|---|---|---:|---|---|---|---|---|---|---|
| complete | ocds-dgv273-seacev3-1085591 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| complete | ocds-dgv273-seacev3-1085661 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| complete | ocds-dgv273-seacev3-1085752 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| zero_amount | ocds-dgv273-seacev3-1004130 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| zero_amount | ocds-dgv273-seacev3-1038229 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| zero_amount | ocds-dgv273-seacev3-1038241 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| start_eq_end | ocds-dgv273-seacev3-1085089 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| start_eq_end | ocds-dgv273-seacev3-1085166 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| start_eq_end | ocds-dgv273-seacev3-1085649 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| no_award | ocds-dgv273-seacev3-1085796 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| no_award | ocds-dgv273-seacev3-1085866 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| no_award | ocds-dgv273-seacev3-1086047 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| dangling_contract | ocds-dgv273-seacev3-1109565 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| dangling_contract | ocds-dgv273-seacev3-1116693 | 8 | sí | sí | sí | sí | sí | sí | PASA |
| dangling_contract | ocds-dgv273-seacev3-1118047 | 8 | sí | sí | sí | sí | sí | sí | PASA |

**Total: 15/15 casos cumplen todos los criterios.**

## 4. Vacíos declarados por el explicador

La sección “Datos faltantes” no rellena campos: enumera lo que la fuente no
informa y lo que está incompleto. El script imprime el texto exacto; esta tabla
resume los campos detectados:

| Bucket / OCID | Vacíos declarados (resumen) |
|---|---|
| complete / 1085591 | Cronograma completo (inicio y fin registran la misma fecha) |
| complete / 1085661 | Cronograma completo (inicio y fin registran la misma fecha) |
| complete / 1085752 | Fechas del período |
| zero_amount / 1004130 | Monto útil (S/ 0.00); fechas del período; adjudicaciones; contratos |
| zero_amount / 1038229 | Monto útil (S/ 0.00); fechas del período |
| zero_amount / 1038241 | Monto útil (S/ 0.00); fechas del período |
| start_eq_end / 1085089 | Adjudicaciones; contratos; cronograma con inicio=fin |
| start_eq_end / 1085166 | Adjudicaciones; contratos; cronograma con inicio=fin |
| start_eq_end / 1085649 | Cronograma con inicio=fin |
| no_award / 1085796 | Adjudicaciones; contratos; cronograma con inicio=fin |
| no_award / 1085866 | Adjudicaciones; contratos; cronograma con inicio=fin |
| no_award / 1086047 | Adjudicaciones; contratos; cronograma con inicio=fin |
| dangling_contract / 1109565 | 1 contrato sin adjudicación vinculada; cronograma con inicio=fin |
| dangling_contract / 1116693 | 6 contratos sin adjudicación vinculada; cronograma con inicio=fin |
| dangling_contract / 1118047 | 11 contratos sin adjudicación vinculada; cronograma con inicio=fin |

Todos los textos terminan con “No se completa con supuestos.” y citan
`data_quality.* (flags de la API)` como fuente.

## 5. Límites de esta evaluación

- Evalúa solo el camino `template`; no hay adaptador Gemini ni API key. El
  resultado no se puede extrapolar a un LLM generativo.
- La detección de afirmaciones de elegibilidad es por patrones léxicos
  (“elegible”, “puede postular”, “califica”, “cumple los requisitos”); no
  sustituye una revisión semántica humana.
- La muestra es fija y pequeña (15 casos) y cubre los buckets del pipeline, no
  la distribución completa de 59,141 procesos.
- El explicador no valida el contenido de las bases del proceso: solo cita los
  campos OCDS y remite al portal oficial.
- Los textos no constituyen asesoría legal.
