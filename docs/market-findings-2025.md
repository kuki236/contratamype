# Hallazgos del mercado 2025 — ContrataMYPE

Cohorte `dataSegmentation` 2025 del bulk OCDS del OECE. Cifras calculadas
desde `data/processed/contratamype.duckdb`; no son proyecciones.

## 1. Titular

- **59,141 procesos** en la cohorte 2025, por **S/ 66,624,609,619**.
- **34,486 procesos (58.3%)** cumplen la heurística MYPE (`mype_fit`).
- Esos procesos MYPE suman **S/ 2,952,693,559**, solo **4.4% del monto total**.
- La mediana del proceso es **S/ 145,694.87**; el 59.7% está por debajo de S/ 200,000.

La brecha no es un error: la heurística excluye `works`, que concentra
**S/ 40,230,411,491 (60.4%)** del valor. Las MYPE aparecen en muchos procesos
pequeños, no en los contratos grandes de infraestructura.

## 2. Por categoría

| Categoría | Procesos | Monto (S/) | MYPE | % MYPE |
|---|---:|---:|---:|---:|
| goods | 26,982 | 10,710,571,940 | 18,285 | 67.8% |
| services | 25,485 | 15,683,626,189 | 16,201 | 63.6% |
| works | 6,674 | 40,230,411,491 | 0 | 0.0% |

`goods` y `services` son el espacio real de la MYPE; `works` queda fuera por
diseño de la regla v1.0, no por falta de datos.

## 3. Top 10 departamentos por procesos

| Departamento | Procesos | Monto (S/) | MYPE | % MYPE |
|---|---:|---:|---:|---:|
| LIMA | 16,320 | 28,726,728,951 | 9,372 | 57.4% |
| CUSCO | 5,052 | 3,099,411,224 | 3,582 | 70.9% |
| ANCASH | 3,242 | 2,417,280,936 | 1,757 | 54.2% |
| PUNO | 3,063 | 1,937,123,887 | 1,934 | 63.1% |
| AYACUCHO | 2,875 | 1,403,822,266 | 1,965 | 68.3% |
| JUNIN | 2,680 | 2,331,743,210 | 1,507 | 56.2% |
| APURIMAC | 2,449 | 960,994,008 | 1,648 | 67.3% |
| CAJAMARCA | 2,291 | 2,246,743,493 | 1,139 | 49.7% |
| AREQUIPA | 2,192 | 1,867,969,302 | 1,226 | 55.9% |
| LA LIBERTAD | 2,120 | 2,198,022,606 | 943 | 44.5% |

Lima concentra el 27.6% de los procesos y el 43.1% del monto. Cusco, Puno y
Ayacucho tienen mayor proporción MYPE que Lima; Cañete/La Libertad y Cajamarca,
menor.

## 4. Estacionalidad

| Mes | Procesos | MYPE |
|---|---:|---:|
| 2025-01 | 1,056 | 532 |
| 2025-02 | 4,481 | 2,747 |
| 2025-03 | 7,341 | 4,599 |
| 2025-04 | 8,329 | 4,754 |
| 2025-05 | 3,320 | 2,210 |
| 2025-06 | 5,318 | 3,146 |
| 2025-07 | 5,877 | 3,143 |
| 2025-08 | 6,458 | 3,555 |
| 2025-09 | 6,284 | 3,417 |
| 2025-10 | 5,982 | 3,320 |
| 2025-11 | 3,595 | 2,253 |
| 2025-12 | 1,095 | 808 |

Abril es el pico (8,329 procesos) y diciembre el valle. Cinco registros de la
cohorte tienen `published_date` en diciembre 2024; no se incluyen en la tabla
mensual.

## 5. Cobertura de adjudicación y contrato

- **44,509 procesos (75.3%)** tienen al menos un award.
- **40,598 procesos (68.6%)** tienen al menos un contrato.
- **4,952 procesos (8.4%)** tienen monto 0 (no informado), no monto gratuito.
- **0 procesos** tienen descripción vacía en la cohorte; el riesgo está en
  campos de plazos y awards, no en el objeto.

## 6. Concentración de compradores

Los mayores montos de la cohorte están en unidades ejecutoras de salud e
infraestructura, no en municipios pequeños:

| Comprador | Procesos | Monto (S/) |
|---|---:|---:|
| UNIDAD EJECUTORA 125 PROGRAMA NACIONAL DE INVERSIONES EN SALUD | 53 | 4,183,267,680 |
| AUTORIDAD NACIONAL DE INFRAESTRUCTURA | 32 | 3,182,259,680 |
| GOBIERNO REGIONAL DE LORETO - OPIP | 8 | 2,074,187,735 |
| FONDO METROPOLITANO DE INVERSIONES | 54 | 1,660,943,282 |
| GOBIERNO REGIONAL DE JUNIN SEDE CENTRAL | 400 | 1,419,852,801 |

Para una MYPE, el mercado relevante no es el top por monto: es el volumen de
procesos pequeños y medianos. El dashboard debe mostrar ambas cosas.

## 7. Métodos más usados

| Método | Procesos |
|---|---:|
| Adjudicación Simplificada | 13,929 |
| Licitación Pública Abreviada | 10,227 |
| Concurso Público Abreviado | 9,380 |
| Subasta Inversa Electrónica | 7,193 |
| Comparación de Precios | 5,097 |
| Contratación Directa | 3,516 |
| Licitación Pública | 2,620 |
| Régimen Especial | 1,606 |

## 8. Reproducción

```sql
-- Titular
SELECT COUNT(*), SUM(amount_pen), MEDIAN(amount_pen),
       COUNT(*) FILTER (WHERE mype_fit)
FROM tenders WHERE segmentation_year = 2025;

-- Categoría
SELECT category, COUNT(*), SUM(amount_pen), COUNT(*) FILTER (WHERE mype_fit)
FROM tenders WHERE segmentation_year = 2025 GROUP BY 1 ORDER BY 2 DESC;
```

Los números corresponden al snapshot con SHA-256
`65444cad90df5c559584d75124884734bff2875616de716d949aa5b858bd160b`.
Un nuevo bulk puede cambiar los conteos; el manifest del run conserva la
procedencia.

## 9. Límites

- La heurística MYPE es compatibilidad por monto/rubro, no elegibilidad legal.
- El monto es el valor referencial del `tender`, no el adjudicado.
- El snapshot puede omitir actualizaciones posteriores; la API está más fresca.
- No se comparan años: v1.0 cubre solo 2025.
