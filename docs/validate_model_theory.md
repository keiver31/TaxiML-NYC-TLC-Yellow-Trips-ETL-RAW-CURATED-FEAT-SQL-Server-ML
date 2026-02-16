# Validación teórica del modelo de regresión (trips_count)

Este documento explica el **marco teórico** detrás del script `validate_model.py`, cuyo propósito es **validar** un modelo de regresión que predice el número de viajes por hora (`trips_count`) a partir de un conjunto de variables explicativas (**features**).

> **Idea central:** un modelo de ML no se “acepta” solo porque produce predicciones; se acepta cuando demuestra que **generaliza** y que es **mejor que una regla simple** (baseline) en datos no vistos.

---

## 1) Contexto del problema

- **Objetivo de predicción:** estimar el conteo real de viajes por hora.
- **Naturaleza del objetivo:** `trips_count` es un **conteo** (0, 1, 2, …), típicamente:
  - muy **sesgado** (muchas horas con pocos viajes y pocas horas con muchos viajes),
  - con **picos**,
  - con **varianza creciente** (cuando el conteo es alto, el error tiende a aumentar).

---

## 2) La hipótesis del modelo

En términos estadísticos, el modelo intenta aproximar una relación funcional:

![Hipótesis de predicción](../imeges/formula_01_prediccion.png)

donde:

- \(X\) representa el conjunto de variables explicativas (features),
- \(\hat{y}\) es la predicción del modelo,
- \(y\) es el conteo real de viajes por hora.

---

## 3) Entrenamiento en escala logarítmica (log1p)

### 3.1 Transformación del objetivo

El modelo no se entrenó directamente con el conteo \(y\), sino con una transformación logarítmica:

![Log1p](../imeges/formula_02_log1p.png)

**Por qué se usa `log(1 + y)` en conteos:**

- **Reduce el impacto de picos**: comprime valores grandes.
- **Mejora la estabilidad**: suele acercar la distribución a algo más manejable para modelos lineales.
- **Ayuda con la heterocedasticidad**: atenúa el crecimiento del error cuando \(y\) aumenta.

> El “+1” evita problemas con \(\log(0)\) cuando \(y=0\).

### 3.2 Modelo lineal en la escala log

Con esta transformación, la regresión lineal aprende una relación lineal en la escala log:

![Modelo lineal en log](../imeges/formula_03_modelo_lineal_log.png)

Interpretación práctica:
- el modelo aprende cómo cambian los conteos **en términos relativos** (multiplicativos) más que en diferencias absolutas.

---

## 4) Predicción y retorno a conteos reales (escala original)

La salida del modelo está en escala logarítmica \(\widehat{y_{\log}}\). Para volver a conteos reales:

![Inversa](../imeges/formula_04_inversa.png)

### Restricción de dominio (conteos no negativos)

En teoría, un conteo no puede ser negativo. En práctica, por ruido del modelo (sobre todo en regresiones lineales), pueden aparecer valores menores a 0 tras la inversión. Por eso se fuerza un mínimo de 0.

---

## 5) Métricas de desempeño (en escala REAL)

Aunque el entrenamiento fue en log, la validación se calcula en **conteos reales**, porque esa es la magnitud de interés.

### 5.1 MAE — Mean Absolute Error
Mide el error “promedio típico” en unidades de viajes/hora.

![MAE](../imeges/formula_05_mae.png)

- Interpretación: “en promedio me equivoco en ~\(MAE\) viajes por hora”.

### 5.2 RMSE — Root Mean Squared Error
Penaliza más los errores grandes (muy sensible a picos mal predichos).

![RMSE](../imeges/formula_06_rmse.png)

- Interpretación: si el RMSE es mucho mayor que el MAE, suele indicar que hay **errores grandes** en una fracción de casos (cola/picos).

### 5.3 R² — Coeficiente de determinación
Mide cuánto de la variabilidad del objetivo es explicada por el modelo (en promedio global).

![R2](../imeges/formula_07_r2.png)

Guía de lectura:
- \(R^2 = 1\): ajuste perfecto.
- \(R^2 \approx 0\): desempeño similar a un predictor constante.
- \(R^2 < 0\): peor que un predictor constante (señal de problema).

> En problemas con conteos muy sesgados, un R² “decente” no garantiza buen desempeño en picos; por eso se complementa con percentiles y segmentación.

---

## 6) Baseline: “regla tonta” (predicción por mediana)

Una validación sólida siempre compara contra un baseline:  
**¿el modelo aporta señal real o solo está “adivinando”?**

En este caso, el baseline predice siempre la **mediana** del `trips_count` del conjunto de prueba:

- La mediana es robusta ante sesgo y valores extremos.
- Es un punto de comparación práctico cuando la distribución tiene colas largas.

### 6.1 Mejora porcentual vs baseline

Se mide cuánto reduce el error el modelo comparado con el baseline:

![Mejora](../imeges/formula_08_mejora_pct.png)

- Si **Mejora% > 0**, el modelo supera al baseline.
- Si **Mejora% ≤ 0**, el modelo no está agregando valor (al menos con esa métrica).

---

## 7) Distribución del error: percentiles (P50, P90, P95)

El script calcula el **error absoluto por fila**:

- \(|y - \hat{y}|\) para cada observación del test.

Luego resume con percentiles típicos:

- **P50**: error “típico” (mediana del error absoluto).
- **P90 / P95**: comportamiento en la cola (casos difíciles, picos, condiciones raras).

Lectura recomendada:
- P50 bajo + P95 muy alto → el modelo funciona bien “en lo normal”, pero falla fuerte en una minoría (picos).

---

## 8) Dictamen (criterio operativo)

El script asigna un dictamen (“bien entrenado”, “aceptable”, “todavía no”) usando:

- mejora vs baseline (MAE y RMSE),
- una señal adicional con R² bajo.

Esto es una **regla práctica de decisión** (heurística) para comparar iteraciones del modelo (v1, v2, v3…).

> Importante: los umbrales no son “leyes” universales; son criterios internos para decidir si vale la pena iterar o avanzar.

---

## 9) Evaluación por rangos (BAJO / MEDIO / ALTO / PICO)

La segmentación busca responder:

**¿cómo cambia el desempeño cuando el conteo real es pequeño vs grande?**

Los segmentos típicos (ejemplo):
- **BAJO**: \(y \le 20\)
- **MEDIO**: \(20 < y \le 200\)
- **ALTO**: \(y > 200\)
- **PICO**: \(y > 500\)

Por qué es útil:
- en conteos, es común que el modelo tenga **errores pequeños** en valores bajos y **errores mayores** en picos.
- permite diagnosticar si el modelo está **subestimando picos** (frecuente con transformaciones log).

---

## 10) Artefactos de validación (salidas) y cómo usarlos

El script genera dos productos principales:

1) `artifacts/metrics_summary.txt`  
   - historial “append” para comparar iteraciones.
   - útil para llevar un tracking tipo bitácora de experimentos.

2) `artifacts/validation_results.csv`  
   - por fila: `y_real`, `y_pred`, `abs_error`.
   - útil para análisis posterior (Excel/Power BI) y diagnóstico:
     - ¿en qué horas/días falla más?
     - ¿hay sesgos sistemáticos (subestima picos)?
     - ¿qué condiciones del dataset producen mayor error?

---

## Glosario rápido

- **Feature (variable explicativa):** columna de entrada que describe el contexto para predecir.
- **Generalización:** capacidad del modelo de rendir bien en datos no vistos.
- **Baseline:** regla simple usada como referencia mínima (si no la superas, hay poco valor).
- **Heterocedasticidad:** la variabilidad del error cambia según el nivel de \(y\) (típico en conteos).
- **Percentil:** valor que deja por debajo un porcentaje de datos (P90 deja debajo el 90%).

---
