# Política del explicador — ContrataMYPE v1.0.0

El explicador traduce campos oficiales a lenguaje claro. **No decide
elegibilidad, no interpreta bases legales y no inventa requisitos.**

## 1. Entradas permitidas

Solo campos que existen en el pipeline:

- `ocid`, `title`, `description`
- `category`, `method`, `status`
- `amount_pen`, `currency`
- `published_date`, `tender_start`, `tender_end`
- `buyer_name`, `department`
- awards/contracts y RUC de proveedores, si existen

No se envían nombres de personas, correos, teléfonos ni documentos de identidad.
Los nombres de proveedores pueden corresponder a personas naturales: el adaptador
LLM no los envía; usa el RUC o un identificador neutro. La UI puede mostrarlos
como dato público de la fuente.

## 2. Salida obligatoria

1. **Resumen** en 2–3 frases sobre qué se compra y quién convoca.
2. **Datos clave** con el campo oficial que respalda cada dato.
3. **Qué revisar** en el portal oficial (bases, cronograma, requisitos).
4. **Datos faltantes** explícitos (“no informado”), sin rellenar.
5. **Disclaimer**: “Compatible con la heurística MYPE; no es elegibilidad legal.”

## 3. Prohibiciones

- Afirmar que la MYPE “califica”, “es elegible” o “puede postular”.
- Inventar documentos, requisitos, montos, fechas o entidades.
- Convertir `mype_fit` en una decisión legal.
- Usar conocimiento externo al registro OCDS.
- Ocultar campos vacíos o contradictorios.

## 4. Fallback de plantilla (camino por defecto)

Sin `GEMINI_API_KEY` o con `CONTRATAMYPE_EXPLAINER=template`, la app usa una
plantilla determinista con los mismos campos y disclaimer. Debe funcionar
offline y ser la referencia para comparar cualquier salida del LLM.

## 5. Adaptador Gemini (opcional, implementado para la introducción)

La web llama a Gemini solo para redactar la **introducción**. Los 8 puntos,
las citas y el disclaimer siguen viniendo de la plantilla; así el modelo no
puede agregar requisitos ni decidir elegibilidad.

- `temperature` baja (0.2), sin herramientas externas.
- Prompt con las prohibiciones de §3 y solo campos oficiales.
- Timeout de 5 s; cualquier error, cuota o texto con lenguaje de elegibilidad
  cae a la plantilla.
- La key vive en `web/.env.local` (`GEMINI_API_KEY`, `GEMINI_MODEL`), nunca en
  el cliente ni en Git. El `.env` raíz es para la API/pipeline, no para Next.js.
- El modo se activa con `CONTRATAMYPE_EXPLAINER=gemini`.

## 6. Evaluación (10–20 oportunidades reales)

Muestra: oportunidades completas, con descripción faltante, monto 0, fechas
inicio=fin y sin award/contrato. La muestra reproducible de 15 casos está en
`docs/llm-eval-sample-2025.json` (3 por bucket: completa, monto 0, inicio=fin,
sin award, contrato con award ausente).

| Criterio | Pasa si |
|---|---|
| Citas | Cada dato clave referencia un campo oficial |
| Vacíos | Los campos faltantes se declaran, no se inventan |
| Requisitos | No aparece ningún documento/requisito no presente en la fuente |
| Elegibilidad | Ninguna frase afirma elegibilidad legal |
| Disclaimer | Visible en todas las respuestas |
| Fallback | Con LLM apagado, la app sigue explicando |

Se registra el resultado en `docs/llm-evaluation-v1.0.0.md` cuando se ejecute
con key. Sin key, se evalúa la plantilla y se documenta como tal.

## 7. Límites

- El explicador no reemplaza las bases integradas ni el cronograma oficial.
- La descripción OCDS puede ser breve o estar ausente; el texto debe decirlo.
- Un texto fluido no es evidencia de corrección: mandan los campos y la fuente.
