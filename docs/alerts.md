# Alertas — digest determinista y deduplicado

## 1. Qué hace

`contratamype digest` lee la base del pipeline y genera un CSV/JSON con las
oportunidades **nuevas** de las cohortes 2024–2025 que cumplen `mype_fit = true`.
No recalcula la regla MYPE: usa la columna calculada por el pipeline.

- Ventana: `--since` (obligatorio) y `--until` (opcional), sobre `published_date`.
- Dedupe: un estado JSON guarda los OCIDs ya alertados. Reejecutar la misma
  ventana produce `sent = 0`.
- Seguridad: si `quality_report.json` tiene el gate bloqueado, el digest falla.
  No se alerta sobre datos que no pasaron el gate.

## 2. Uso

```bash
python -m contratamype digest \
  --db data/processed/contratamype.duckdb \
  --artifacts artifacts/2025 \
  --out artifacts/alerts \
  --state artifacts/alerts/state.json \
  --since 2024-01-01
```

Salida:

| Archivo | Contenido |
|---|---|
| `alert_digest.csv` | Columnas: `ocid,title,category,amount_pen,department,buyer_name,published_date,tender_start,tender_end` |
| `alert_digest.json` | Metadatos + filas, con `generated_at` y ventana |
| `power_automate_payload.json` | Mismo payload listo para el adaptador |
| `state.json` | OCIDs alertados y timestamp; no se commitea |

`csv_sha256` en el resumen permite verificar el artefacto.

## 3. Adaptador Power Automate (sin licencia confirmada)

No hay licencia verificada, así que v1.1 usa el digest local y deja el flujo
documentado. Cuando exista licencia:

1. Programar el pipeline y el digest (Task Scheduler o Power Automate Desktop).
2. Disparar el flujo con `power_automate_payload.json` (o subir el CSV a OneDrive).
3. Enviar un correo con `subject` y una tabla HTML construida desde `rows`.
4. Incluir `disclaimer`, `source` y `license` del payload, y un enlace de baja.
5. No reenviar: el flujo confía en `state.json`; si se ejecuta en otra máquina,
   sincronizar el estado o usar una tabla en SharePoint con el OCID como clave.

Solo se envían alertas a destinatarios que dieron consentimiento. El digest no
implementa el envío ni la baja: el adaptador debe incluir ambos en el correo.

## 4. Límites

- El bulk es un snapshot; una oportunidad puede aparecer con fechas antiguas.
  La ventana usa `published_date`, no la fecha de ingesta.
- Sin cuentas de usuario ni preferencias por región/rubro en v1.1.
- El digest no sustituye la revisión de bases ni la asesoría legal.

## 5. Evidencia v1.1

- Primera corrida desde 2024-01-01: **58,380 enviados**.
- Segunda corrida idéntica: **0 enviados**, estado con 58,380 OCIDs.
- El digest incluye cohortes 2024/2025; `--cohort-year` es repetible para acotar.

## 6. Envío local con Outlook (sin OneDrive ni Premium)

`scripts/run_digest_and_email.ps1` ejecuta el digest y `scripts/send_digest.ps1`
adjunta el CSV en un correo de Outlook Desktop. No usa OneDrive, SharePoint ni
Power Automate.

```powershell
# Validar sin enviar
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_digest_and_email.ps1 -DryRun

# Enviar (requiere Outlook Desktop con una cuenta configurada)
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\run_digest_and_email.ps1
```

- Si el CSV solo tiene cabecera, no envía nada.
- El correo va a `sebastian.tejeda@unmsm.edu.pe` por defecto; se puede cambiar con
  `-To` en `send_digest.ps1`.
- Si Outlook no está configurado, Windows abrirá el asistente; no se envía nada
  hasta completarlo.

Programación diaria con el Programador de tareas:

```powershell
schtasks /Create /SC DAILY /TN "ContrataMYPE Digest" `
  /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File \"C:\ruta\a\contratamype\scripts\run_digest_and_email.ps1\"" `
  /ST 08:00
```

Para el CV, esto se describe como **automatización local Python + Outlook +
Programador de tareas**, no como Power Automate. Power Automate queda como flujo
manual estándar/documentado si se necesita la etiqueta.
