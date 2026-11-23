# ContrataMYPE v1.1.1

Patch sobre v1.1.0: bundle con PBIX, dashboard y scripts de digest.

## Cifras (sin cambios respecto de v1.1.0)

- Procesos en las cohortes 2024 + 2025: 123,931 (2024: 64,783; 2025: 59,148)
- Oportunidades compatibles MYPE: 58,380 (47.1%)
- Compradores: 3,080
- Proveedores: 91,879
- Awards (filas por proveedor): 201,299
- Contratos: 195,583

## Cambios

- `dashboard/ContrataMYPE.pbix`: dashboard con datos embebidos; es la vía
  principal para abrir el reporte sin configurar el PBIP.
- PBIP: `DataFolder` apunta a `C:\Users\Public\contratamype\artifacts\2025`
  (junction documentado) para no exponer rutas de usuario.
- Gemini: modelo `gemini-3.5-flash`, con fallback a plantilla si no hay key.
- Scripts locales `send_digest.ps1` y `run_digest_and_email.ps1` para generar
  el digest y enviarlo por Outlook Desktop.
- Documentación de alertas, Power BI y límites actualizada.

## Calidad

- Checks: 12 (7 pass, 5 warn, 0 fail)
- Gate: abierto

## Límites

- El envío de alertas por Outlook Desktop requiere una cuenta configurada; no
  se incluye como servicio automático. El release no envía correo por sí solo.
- La regla MYPE es una heurística de compatibilidad, no elegibilidad legal.

## Contenido

- `artifacts/`: Parquet/CSV, reporte de calidad, manifest y checksums del pipeline.
- `dashboard/`: PBIP/PBIX y capturas.
- `docs/`: diccionario, arquitectura, perfil de datos y límites.
- `SHA256SUMS`: hash de cada archivo del bundle.

## Atribución

Datos: OECE, Portal de Contrataciones Abiertas, estándar OCDS, CC BY 4.0.
