# Resultados de validación — LinearRegression + `log1p(trips_count)` (v2)

Este documento registra los **resultados finales** obtenidos al ejecutar el script `validate_model.py` para la versión **v2** del modelo.

- **Fecha de ejecución:** 2026-02-15 
- **Script:** `validate_model.py`  
- **Modelo:** `artifacts/linreg_trips_count_v2.joblib`  
- **Features de test:** `artifacts/X_test_v2.csv`  
- **Objetivo real (test):** `artifacts/y_test_real_v2.csv`  
- **Transformación objetivo (entrenamiento):** `y_log = log(1 + trips_count)`  

---

## 1) Tamaño del set de prueba

- **X_test:** 63,221 filas × 267 features  
- **y_test:** 63,221 valores (conteos reales)

> Validación básica: el número de filas coincide entre `X_test` y `y_test`, por lo que el set es consistente para evaluar.

---

## 2) Métricas principales (en escala REAL)

| Métrica | Valor | Interpretación práctica |
|---|---:|---|
| MAE | 28.2096 | Error absoluto promedio: en promedio, la predicción se desvía **~28 viajes** |
| RMSE | 72.9374 | Penaliza más errores grandes: indica que los **picos** impactan el error |
| R² | 0.6390 | Capacidad explicativa global **moderada-alta** para este problema |

---

## 3) Contexto del objetivo (distribución del `trips_count`)

| Estadística | Valor |
|---|---:|
| Media | 51.12 |
| Mediana | 6.00 |

**Lectura rápida:** la media (51.12) es mucho mayor que la mediana (6.00), lo que sugiere una distribución **sesgada con cola larga** (muchos casos pequeños y pocos casos muy grandes).  
Este patrón suele hacer que los modelos tengan buen desempeño en valores bajos/medios y más dificultad en **picos**.

---

## 4) Baseline (referencia) y mejora del modelo

Baseline usado: **predecir siempre la mediana del test** (`6.00`) para todas las filas.

| Métrica | Baseline | Modelo | Mejora |
|---|---:|---:|---:|
| MAE | 48.7332 | 28.2096 | **42.11%** |
| RMSE | 129.5102 | 72.9374 | **43.68%** |

**Conclusión:** el modelo mejora de forma **fuerte** frente a una referencia robusta (mediana), tanto en MAE como en RMSE.

---

## 5) Distribución del error absoluto (qué pasa en la cola)

| Percentil | abs_error |
|---|---:|
| P50 | 3.25 |
| P90 | 84.56 |
| P95 | 142.60 |

**Lectura rápida:**
- P50 = 3.25 → en la mitad de los casos, el error típico es **bajo** (≈ 3 viajes).
- P90/P95 crecen mucho → el error se concentra en casos difíciles (cola / picos).

---

## 6) Dictamen automático del script

**✅ Bien entrenado (mejora fuerte vs baseline)**

Criterio del dictamen: mejora porcentual vs baseline (mediana) con umbrales heurísticos del proyecto.

---

## 7) Desempeño por segmentos (errores según tamaño del conteo real)

Estos segmentos se basan en `trips_count` REAL (`y_test`):

| Segmento | Condición | n | y_mean | MAE | RMSE | Lectura rápida |
|---|---|---:|---:|---:|---:|---|
| BAJO | <= 20 | 44,132 | 4.68 | 7.50 | 25.25 | El modelo se comporta bien en casos comunes (bajos) |
| MEDIO | 20–200 | 14,376 | 79.94 | 49.68 | 77.63 | Aumenta el error, pero sigue siendo manejable |
| ALTO | > 200 | 4,713 | 398.08 | 156.58 | 216.82 | El error crece en valores altos |
| PICO | > 500 | 1,018 | 727.97 | 327.07 | 387.75 | Donde más falla: picos muy altos |

**Conclusión por segmentos:** el rendimiento es **muy bueno en valores bajos** (la mayoría del dataset) y empeora progresivamente en **altos/picos**, que es un patrón esperado en conteos con cola larga.

---

## 8) Artefactos generados por la validación

Al finalizar la ejecución se generaron/actualizaron:

- `artifacts/metrics_summary.txt`  
  Historial (append) con métricas para comparar iteraciones.

- `artifacts/validation_results.csv`  
  Resultados por fila con:
  - `y_real`
  - `y_pred`
  - `abs_error`

---

## 9) Ejemplos (primeros 5)

```text
y_real_trips  pred_trips   abs_error
6.0          2.330128     3.669872
12.0         7.619053     4.380947
3.0          3.793419     0.793419
12.0         13.170970    1.170970
13.0         3.795092     9.204908
```

---

## 10) Interpretación final (para README / GitHub)

- El modelo **sí aporta valor**: mejora ~42–44% vs baseline robusto (mediana).
- El error típico es bajo (P50 ≈ 3.25), pero existe una cola pesada (P90/P95 altos).
- La mayor oportunidad de mejora está en **picos** (`> 500`), donde el error es significativamente mayor.

---

## 11) Siguientes pasos sugeridos (opcional)

Si el objetivo es mejorar desempeño en picos, suele funcionar:

- Modelos no lineales (árboles / boosting) para capturar interacciones y umbrales.
- Ajustar features orientadas a picos (hora/día festivo/eventos, señales externas, etc.).
- Evaluar métricas por percentiles o por segmentos como criterio principal (no solo promedio global).

> Recomendación práctica: conservar este documento como “registro” de la versión v2 y crear uno nuevo por cada iteración (v3, v4...).
