# `validate_model.py` — Validación del modelo (Regresión: `trips_count`)

Este documento describe la **funcionalidad** del script `validate_model.py` para que cualquier persona (técnica o no técnica) pueda:
- entender qué valida,
- saber cómo ejecutarlo,
- interpretar sus métricas y salidas,
- reutilizarlo en su propio proyecto.

---

## Contexto: ¿qué está prediciendo el modelo?

El objetivo del modelo es predecir **cuántos viajes** (`trips_count`) ocurren en una combinación específica (por ejemplo: zona + hora).

Durante el entrenamiento, el modelo **no** aprendió a predecir `trips_count` directamente, sino una versión transformada:

- Transformación usada:  
  `y_log = log(1 + trips_count)` (en Python: `np.log1p(trips_count)`)

**¿Por qué?**  
En datos de conteo suele haber muchos valores bajos (incluyendo ceros) y pocos “picos” muy altos. La transformación `log(1 + y)` reduce esa asimetría y hace el aprendizaje más estable.

---

## Qué hace este script (resumen)

1. Carga artefactos: modelo + `X_test` + `y_test_real`.
2. Predice en **escala log** (salida del modelo).
3. Convierte a **escala real** (conteos) con la inversa de la transformación.
4. Calcula métricas principales (MAE, RMSE, R²) en escala real.
5. Construye un **baseline** simple (predice la mediana) y calcula mejoras porcentuales.
6. Calcula percentiles del error (P50, P90, P95) para ver la “cola” de errores.
7. Emite un **dictamen** (heurístico) basado en mejora vs baseline y una señal por R².
8. Evalúa desempeño por rangos de conteo (bajo/medio/alto/pico).
9. Guarda métricas e información por fila para comparar iteraciones y diagnosticar.

---

## Entradas esperadas

El script espera encontrar estos archivos en la carpeta `artifacts/`:

| Archivo | Qué contiene | Notas |
|---|---|---|
| `linreg_trips_count_v2.joblib` | Modelo entrenado (scikit-learn) | Se carga con `joblib.load()` |
| `X_test_v2.csv` | Features del set de prueba | Debe tener **las mismas columnas** usadas al entrenar |
| `y_test_real_v2.csv` | `trips_count` real del set de prueba | **Conteos reales**, no log |

**Requisito crítico**  
`X_test_v2.csv` debe coincidir con el set de features del entrenamiento (mismas columnas y orden). Si no, `model.predict(X_test)` puede fallar o producir resultados incorrectos.

---

## Salidas generadas

| Archivo | Qué contiene | Para qué sirve |
|---|---|---|
| `artifacts/metrics_summary.txt` | Línea por ejecución con métricas + baseline + percentiles | Comparar iteraciones (v1/v2/v3…) |
| `artifacts/validation_results.csv` | Resultado por fila: `y_real`, `y_pred`, `abs_error` | Auditoría / diagnóstico / análisis posterior |

Además, imprime un reporte completo en consola y muestra los **primeros 5 ejemplos**.

---

## Requisitos para ejecutar

Dependencias Python:
- `pandas`
- `numpy`
- `joblib`
- `scikit-learn`

Instalación:
```bash
pip install pandas numpy joblib scikit-learn
```

Ejecución:
```bash
python validate_model.py
```

---

## Cómo funciona: sección por sección (mapeado al código)

### 1) Cargar modelo y datos de test

- Carga el modelo entrenado desde `.joblib`
- Lee `X_test` (matriz de variables de entrada)
- Lee `y_test` real (vector de conteos)

Detalle práctico:
- `squeeze("columns")` convierte un CSV de una sola columna a un vector 1D (Serie).

Validación rápida que imprime el script:
- `X_test.shape` (n_filas, n_features)
- `y_test.shape` (n_filas)

**Regla simple:** `X_test` y `y_test` deben tener el **mismo número de filas**.

---

### 2) Predicción en escala LOG y devolución a escala REAL

El modelo devuelve:
- `pred_log ≈ log(1 + trips_count)`

Para volver a conteo real:
- Si `pred_log = log(1 + y)`, entonces `y = exp(pred_log) - 1`

En el script:
- `pred = np.expm1(pred_log)`  (equivalente a `np.exp(pred_log) - 1`, pero más estable)

Luego se aplica una protección:
- `pred = np.clip(pred, 0, None)`

**¿Por qué?**  
Un conteo real no debería ser negativo. Por ruido del modelo, la inversión puede dar valores menores a 0; el `clip` fuerza mínimo 0.

---

### 3) Métricas principales (en escala REAL)

Se calculan comparando `y_test` (real) vs `pred` (real):

- **MAE (Mean Absolute Error)**  
  Promedio de `|y - y_pred|`  
  Interpretación: “en promedio, me equivoco por X viajes”.

- **RMSE (Root Mean Squared Error)**  
  Raíz del error cuadrático medio  
  Interpretación: penaliza más los errores grandes (picos).

- **R² (Coeficiente de determinación)**  
  Interpretación: qué tan bien el modelo explica la variación del objetivo.  
  Valores típicos:
  - `1.0` = perfecto
  - cercano a `0` = similar a un baseline simple
  - negativo = peor que un baseline (depende del caso)

---

### 4) Baseline (modelo “tonto”) usando la mediana

Se construye un baseline que predice **la misma constante para todas las filas**:
- `baseline_pred = mediana(y_test)`

**Motivo:**  
En conteos con distribución sesgada, la mediana suele ser un baseline robusto.

Se calculan:
- `baseline_mae`, `baseline_rmse`

Y luego la mejora porcentual:
- `ImproveMAE% = (baseline_mae - mae) / baseline_mae * 100`
- `ImproveRMSE% = (baseline_rmse - rmse) / baseline_rmse * 100`

Interpretación:
- mejora **positiva** => el modelo supera al baseline
- mejora **≤ 0** => el modelo no aporta mejora real vs “predecir la mediana”

---

### 5) Distribución de errores (percentiles)

Se calcula error absoluto por fila:
- `abs_error = |y_real - y_pred|`

Y percentiles:
- **P50**: error “típico” (mediana del error)
- **P90** / **P95**: cola del error (casos difíciles, picos, outliers)

Esto ayuda a responder:
- “¿Qué tan grande es el error en el peor 10% o 5% de casos?”

---

### 6) Dictamen (heurístico)

El script genera un dictamen para ayudar a decidir si el modelo “pasa” o “no pasa” con reglas simples:

1) Regla base:
- si **no mejora** MAE vs baseline → **🔴 Todavía NO**

2) Si mejora MAE vs baseline, clasifica con umbrales:

- ✅ **Bien entrenado** si:
  - `ImproveMAE% >= 30` **y** `ImproveRMSE% >= 35`

- 🟡 **Aceptable** si:
  - `ImproveMAE% >= 15` **y** `ImproveRMSE% >= 20`

- 🔴 **Todavía NO** si:
  - la mejora existe, pero es débil

Se añade una señal extra:
- si `R² < 0.2` agrega razón: “R2 bajo”.

> Nota: estos umbrales son **criterios prácticos** del proyecto (reglas internas). Si cambias dataset o contexto, ajústalos.

---

### 7) Reporte en consola

Imprime:
- Métricas principales (MAE/RMSE/R²)
- Media y mediana del objetivo real
- Métricas del baseline + mejoras porcentuales
- Percentiles del error
- Dictamen + razones

---

### 7.5) Evaluación por rangos (BAJO / MEDIO / ALTO / PICO)

Propósito:
- ver cómo cambia el error cuando el conteo real es pequeño vs grande

El script define segmentos por `trips_count` real:
- **BAJO:** `<= 20`
- **MEDIO:** `20–200`
- **ALTO:** `> 200`
- **PICO:** `> 500`

Para cada segmento calcula:
- `n` (número de filas)
- MAE, RMSE
- `y_mean` del segmento

---

### 7.6) Guardar resumen de métricas (historial)

Se escribe en modo append (`"a"`) en:
- `artifacts/metrics_summary.txt`

Cada ejecución agrega una línea con:
- MAE, RMSE, R²
- baseline MAE/RMSE
- mejoras %
- P50/P90/P95

Esto permite comparar fácilmente resultados entre versiones del modelo.

---

### 8) Export de resultados por fila

Se exporta el CSV completo:
- `artifacts/validation_results.csv`

Columnas:
- `y_real`: valor real
- `y_pred`: predicción (conteo)
- `abs_error`: error absoluto por fila

También se imprime una muestra con los primeros 5 registros para inspección rápida.

---

## Personalización rápida

Si cambias versión de artefactos (v3, v4...), actualiza estos nombres:
- `linreg_trips_count_v2.joblib`
- `X_test_v2.csv`
- `y_test_real_v2.csv`

Si tu distribución es distinta, ajusta los segmentos:
- BAJO / MEDIO / ALTO / PICO

Si quieres conteos enteros, podrías redondear `pred`, pero **ten en cuenta** que cambia métricas y análisis:
- `pred = np.rint(pred)` (opcional y depende del caso)

---

## Troubleshooting (fallos típicos)

**1) `FileNotFoundError`**  
- Los archivos no están en `artifacts/` o el nombre no coincide.

**2) Error en `model.predict(X_test)`**  
- `X_test` no tiene las mismas columnas que el entrenamiento.  
  Recomendación: reconstruir `X_test` usando el mismo pipeline de features.

**3) Predicciones negativas**  
- Es esperable por la inversión `expm1` + ruido del modelo.  
  El script ya lo corrige con `np.clip(pred, 0, None)`.

**4) NaNs o tipos raros**  
- Revisa `X_test` por valores faltantes y tipos (`X_test.isna().sum()`).

---

## Glosario

- **Artefactos:** archivos generados por el pipeline (modelo, datasets, métricas).
- **Feature:** variable de entrada del modelo (columna de `X_test`).
- **Objetivo / target:** variable a predecir (`trips_count`).
- **`log1p`:** `log(1 + y)` (estable con ceros).
- **`expm1`:** `exp(x) - 1` (inversa de `log1p`).
- **Baseline:** referencia simple para comparar (aquí: mediana constante).
- **Percentil:** valor bajo el cual cae un % de datos (P90 = 90% por debajo).
- **Máscara booleana (mask):** vector `True/False` para filtrar filas por condición.
- **MAE:** error absoluto promedio.
- **RMSE:** penaliza más los errores grandes.
- **R²:** capacidad explicativa global del modelo.

