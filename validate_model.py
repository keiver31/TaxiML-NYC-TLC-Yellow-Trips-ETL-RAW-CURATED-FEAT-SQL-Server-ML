"""
validate_model.py — Validación del modelo de regresión (trips_count)

Este script valida un modelo entrenado que predice el número de viajes por hora (`trips_count`).
El modelo fue entrenado con el objetivo transformado: y_log = log(1 + trips_count).

Flujo de alto nivel:
1) Carga artefactos (modelo + X_test + y_test_real)
2) Predice en escala LOG (salida del modelo) y convierte a escala REAL (conteos)
3) Calcula métricas (MAE, RMSE, R²) en escala REAL
4) Calcula un baseline (modelo "tonto") que predice la mediana
5) Calcula percentiles de error absoluto (P50, P90, P95)
6) Emite un dictamen basado en la mejora vs baseline
7) Evalúa desempeño por rangos (bajo/medio/alto/pico)
8) Guarda resúmenes y resultados para comparar iteraciones

Entradas esperadas (en carpeta artifacts/):
- linreg_trips_count_v2.joblib  -> modelo entrenado (scikit-learn)
- X_test_v2.csv                 -> features del set de prueba
- y_test_real_v2.csv             -> objetivo REAL (conteo) del set de prueba

Salidas generadas:
- artifacts/metrics_summary.txt       -> append de métricas para comparar iteraciones
- artifacts/validation_results.csv    -> y_real, y_pred, abs_error por fila
"""

import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


# =========================
# 1) Cargar modelo y datos de test
# =========================
# - model: objeto scikit-learn ya entrenado (LinearRegression en este caso)
# - X_test: matriz de features del set de prueba (mismas columnas usadas en entrenamiento)
# - y_test: objetivo REAL (conteo). Importante: NO está en log.
model = joblib.load("artifacts/linreg_trips_count_v2.joblib")
X_test = pd.read_csv("artifacts/X_test_v2.csv")

# `squeeze("columns")` convierte un DataFrame de una sola columna en una Serie (vector 1D).
# `astype(float)` asegura el tipo numérico para métricas.
y_test = pd.read_csv("artifacts/y_test_real_v2.csv").squeeze("columns").astype(float)

print("Tamaño X_test:", X_test.shape)
print("Tamaño y_test:", y_test.shape)


# =========================
# 2) Predecir (en escala LOG) y devolver a escala REAL
# =========================
# El modelo fue entrenado para predecir:
#   pred_log ≈ log(1 + trips_count)
# Por eso su salida está en escala log.
pred_log = model.predict(X_test)

# Conversión a escala real:
#   Si pred_log = log(1 + y), entonces y = exp(pred_log) - 1
# np.expm1(x) calcula exp(x) - 1 (más estable numéricamente que np.exp(x) - 1).
pred = np.expm1(pred_log)

# Un conteo no debería ser negativo. Por ruido del modelo puede salir < 0.
# np.clip(pred, 0, None) fuerza mínimo 0.
pred = np.clip(pred, 0, None)


# =========================
# 3) Métricas principales (YA en escala real)
# =========================
# MAE (Mean Absolute Error): promedio del error absoluto |y - y_hat|
# RMSE: raíz del error cuadrático medio (penaliza más los errores grandes)
# R²: qué tan bien explica la variación del objetivo (1.0 perfecto, 0 ~ baseline tipo media)
mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))
r2 = r2_score(y_test, pred)


# =========================
# 4) Baseline (modelo tonto) - predice mediana del test
# =========================
# Baseline usado:
# - Predice la mediana del conjunto de prueba para TODAS las filas.
# Motivo:
# - En conteos muy sesgados, la mediana suele ser un baseline robusto.
y_median = float(np.median(y_test))
y_mean = float(np.mean(y_test))

baseline_pred = np.full(shape=len(y_test), fill_value=y_median)
baseline_mae = mean_absolute_error(y_test, baseline_pred)
baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))

# Mejora porcentual vs baseline:
# - Si mae < baseline_mae => mejora positiva
# - Se protege contra división por 0
improve_mae_pct = (baseline_mae - mae) / baseline_mae * 100 if baseline_mae != 0 else 0
improve_rmse_pct = (baseline_rmse - rmse) / baseline_rmse * 100 if baseline_rmse != 0 else 0


# =========================
# 5) Distribución de errores (picos)
# =========================
# Error absoluto por fila:
abs_err = np.abs(y_test.values - pred)

# Percentiles típicos:
# - P50: mediana del error absoluto (error "típico")
# - P90/P95: qué pasa en la cola (casos difíciles / picos)
p50 = float(np.percentile(abs_err, 50))
p90 = float(np.percentile(abs_err, 90))
p95 = float(np.percentile(abs_err, 95))


# =========================
# 6) Dictamen (basado en mejora vs baseline)
# =========================
# Criterio simple: el modelo debe mejorar el baseline.
# Luego se usan umbrales prácticos (heurísticos) para clasificar la mejora.
verdict = "🔴 Todavía NO (no mejora baseline)"
reasons = []

if improve_mae_pct <= 0:
    reasons.append("No mejora el baseline (mediana).")
else:
    # Umbrales prácticos para clasificar el entrenamiento
    # (son reglas de negocio/criterios internos, no una regla universal)
    if improve_mae_pct >= 30 and improve_rmse_pct >= 35:
        verdict = "✅ Bien entrenado (mejora fuerte vs baseline)"
    elif improve_mae_pct >= 15 and improve_rmse_pct >= 20:
        verdict = "🟡 Aceptable (mejora clara vs baseline)"
    else:
        verdict = "🔴 Todavía NO (mejora débil vs baseline)"
        reasons.append("Mejora baja vs baseline.")

# Señal adicional: si R² es muy bajo, indica poca capacidad explicativa global.
if r2 < 0.2:
    reasons.append("R2 bajo (poca explicación de variación).")


# =========================
# 7) Reporte (resumen en consola)
# =========================
print("\n=== Validación (LinearRegression + log1p) ===")
print(f"MAE:  {mae:.4f}")
print(f"RMSE: {rmse:.4f}")
print(f"R2:   {r2:.4f}")

print("\n=== Contexto del objetivo (trips_count REAL) ===")
print(f"Media y_test:   {y_mean:.2f}")
print(f"Mediana y_test: {y_median:.2f}")

print("\n=== Baseline (predecir mediana) ===")
print(f"Baseline MAE:  {baseline_mae:.4f}")
print(f"Baseline RMSE: {baseline_rmse:.4f}")
print(f"Mejora MAE vs baseline:  {improve_mae_pct:.2f}%")
print(f"Mejora RMSE vs baseline: {improve_rmse_pct:.2f}%")

print("\n=== Distribución de errores absolutos ===")
print(f"P50 abs_error: {p50:.2f}")
print(f"P90 abs_error: {p90:.2f}")
print(f"P95 abs_error: {p95:.2f}")

print("\n=== Dictamen ===")
print(verdict)
if reasons:
    print("Razones/Señales:")
    for r in reasons:
        print("-", r)


# =========================
# 7.5) Evaluación por rangos (BAJO / MEDIO / ALTO / PICO)
# =========================
# Objetivo:
# - Entender cómo se comporta el error cuando los conteos son pequeños vs grandes.
# - En conteos tipo "picos", el modelo suele fallar más; esto lo cuantifica.
def eval_segment(name, mask):
    """
    Calcula MAE y RMSE para un segmento definido por una máscara booleana.

    Parámetros:
    - name: etiqueta del segmento (string)
    - mask: array booleano del mismo tamaño que y_test/pred
            True indica filas que pertenecen al segmento.
    """
    y_s = y_test[mask]
    p_s = pred[mask]

    mae_s = mean_absolute_error(y_s, p_s)
    rmse_s = np.sqrt(mean_squared_error(y_s, p_s))

    print(
        f"{name}: n={mask.sum()} | MAE={mae_s:.2f} | RMSE={rmse_s:.2f} | y_mean={y_s.mean():.2f}"
    )


# y = valores reales del objetivo (array)
y = y_test.values

# Segmentos basados en rangos de trips_count REAL
eval_segment("BAJO (<=20)",    y <= 20)
eval_segment("MEDIO (20-200)", (y > 20) & (y <= 200))
eval_segment("ALTO (>200)",    y > 200)
eval_segment("PICO (>500)",    y > 500)


# =========================
# 7.6) Guardar resumen de métricas (para comparar iteraciones)
# =========================
# Se escribe en modo append ("a") para conservar historial de ejecuciones.
# Útil cuando entrenas varias versiones del modelo (v1, v2, v3...) y quieres comparar.
with open("artifacts/metrics_summary.txt", "a", encoding="utf-8") as f:
    f.write(
        f"MAE={mae:.2f} RMSE={rmse:.2f} R2={r2:.3f} "
        f"BaselineMAE={baseline_mae:.2f} BaselineRMSE={baseline_rmse:.2f} "
        f"ImproveMAE%={improve_mae_pct:.2f} ImproveRMSE%={improve_rmse_pct:.2f} "
        f"P50={p50:.2f} P90={p90:.2f} P95={p95:.2f}\n"
    )

print("✅ Guardado: artifacts/metrics_summary.txt")


# =========================
# 8) Ejemplos (primeros 5) y export de resultados por fila
# =========================
# Ejemplos rápidos para inspección visual:
n = 5
sample = pd.DataFrame({
    "y_real_trips": y_test.values[:n],
    "pred_trips": pred[:n],
    "abs_error": abs_err[:n]
})

# Resultado completo por fila (útil para análisis posterior en Excel/Power BI)
out = pd.DataFrame({
    "y_real": y_test.values,
    "y_pred": pred,
    "abs_error": np.abs(y_test.values - pred)
})

out.to_csv("artifacts/validation_results.csv", index=False)
print("✅ Guardado: artifacts/validation_results.csv")

print("\n=== Ejemplos (primeros 5) ===")
print(sample)
