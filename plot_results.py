import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("artifacts/validation_results.csv")

y_real = df["y_real"].values
y_pred = df["y_pred"].values
abs_error = df["abs_error"].values

# =========================
# 1) Scatter: Real vs Pred
# =========================
plt.figure()
plt.scatter(y_real, y_pred, s=5, alpha=0.3)
m = max(y_real.max(), y_pred.max())
plt.plot([0, m], [0, m])  # línea y=x (ideal)
plt.xlabel("y_real (trips_count real)")
plt.ylabel("y_pred (trips_count predicho)")
plt.title("Real vs Predicho (si cae en la diagonal, está perfecto)")
plt.show()

# =========================
# 2) Histograma de error absoluto
# =========================
plt.figure()
plt.hist(abs_error, bins=50)
plt.xlabel("abs_error = |real - pred|")
plt.ylabel("Frecuencia")
plt.title("Distribución del error absoluto")
plt.show()

# =========================
# 3) Error vs Real (dónde falla más)
# =========================
plt.figure()
plt.scatter(y_real, abs_error, s=5, alpha=0.3)
plt.xlabel("y_real (trips_count real)")
plt.ylabel("abs_error")
plt.title("Error vs Valor real (suele crecer en picos)")
plt.show()

# =========================
# Bonus (opcional): percentiles
# =========================
print("P50 abs_error:", np.percentile(abs_error, 50))
print("P90 abs_error:", np.percentile(abs_error, 90))
print("P95 abs_error:", np.percentile(abs_error, 95))
