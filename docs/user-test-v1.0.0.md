# Test con una persona MYPE — ContrataMYPE v1.0.0

Objetivo: verificar si una persona sin conocimiento de OCDS encuentra una
oportunidad compatible, entiende sus datos y sabe qué hacer después. No es un
test de usabilidad experta ni una validación legal.

## 1. Perfil

- Dueño/a o personal administrativo de una MYPE.
- Sin experiencia previa en SEACE/OECE.
- Sector y región reales de la persona (se registran sin datos personales).
- Duración: 30–40 minutos, remoto o presencial.
- Consentimiento verbal para observar la sesión; no se graba rostro ni voz sin
  permiso adicional.

## 2. Preparación

1. Pipeline y API corriendo en local.
2. Web en `http://localhost:3000`.
3. Tres oportunidades sembradas o reales:
   - Una completa y compatible.
   - Una con descripción faltante.
   - Una con monto 0 o fechas incompletas.
4. Checklist/PDF disponible.
5. Hoja de observación (sección 5).

## 3. Tareas (sin explicar la interfaz)

| # | Tarea | Éxito observable |
|---|---|---|
| 1 | “Busca una oportunidad de tu rubro en tu región por menos de S/ 200,000.” | Llega a resultados con filtros correctos |
| 2 | “Abre una y cuéntame qué entiendes del objeto, el plazo, el monto y quién compra.” | Explica los 4 campos sin ayuda |
| 3 | “Descarga el checklist y dime qué documentos ya tienes y cuáles te faltan.” | Abre el PDF y marca al menos 2 documentos |
| 4 | “¿Esta oportunidad te asegura que puedes postular?” | Responde que no; entiende que es compatible, no elegibilidad |
| 5 | “Mira esta oportunidad con datos incompletos. ¿Qué harías?” | Detecta el vacío y busca la fuente oficial |
| 6 | “Filtra algo que no exista. ¿Entiendes el resultado?” | Reconoce el estado vacío y ajusta el filtro |

## 4. Métricas

- Éxito por tarea (sí/no/parcial) y tiempo.
- Puntos de confusión (dónde duda, qué término no entiende).
- Confianza declarada 1–5 en “encontré algo que me sirve”.
- ¿Recomendaría la herramienta? 1–5.
- Errores de datos percibidos (monto, fecha, entidad).

## 5. Hoja de observación

| Campo | Registro |
|---|---|
| Fecha y modalidad | |
| Sector / región / tamaño | |
| Tarea 1–6 | éxito, tiempo, notas |
| Frases textuales | |
| Confusión principal | |
| Confianza (1–5) | |
| Recomendación (1–5) | |
| Qué falta | |
| Qué sobra | |
| ¿Volvería a usarla? | |

## 6. Preguntas de cierre

1. ¿Qué fue lo primero que buscaste y por qué?
2. ¿Qué dato no encontraste o no creíste?
3. ¿El checklist te sirve para decidir si postular?
4. ¿Confiarías en el explicador? ¿Por qué?
5. ¿Qué te haría volver la próxima semana?

## 7. Reglas

- No prometer elegibilidad ni asesoría legal.
- No corregir al participante durante la tarea; anotar y preguntar al final.
- No registrar RUC, correo, teléfono ni nombre completo.
- Si la persona pide ayuda legal, derivar al portal oficial del OECE.
- El feedback se registra en `docs/feedback-v1.0.0.md` cuando exista.

## 8. Criterio de cierre

- 4 de 6 tareas completadas sin ayuda, incluida la tarea 4 (disclaimer).
- Ninguna persona interpreta “compatible” como “elegible”.
- Al menos una mejora concreta priorizada para v1.1.
