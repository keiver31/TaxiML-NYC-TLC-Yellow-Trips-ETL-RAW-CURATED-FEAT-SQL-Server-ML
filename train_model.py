

import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib

# ==========================================================
# OBJETIVO GENERAL DEL SCRIPT
# ----------------------------------------------------------
# Entrenar un modelo que prediga la cantidad de viajes (trips_count)
# por hora y zona, usando variables de tiempo (fecha/hora)
# y promedios de distancia/duración/valor.
#
# El modelo se entrena con log(1 + trips_count) para que los "picos"
# no dominen tanto el ajuste.
# ==========================================================


# =========================
# 1) Conexión a SQL Server
# =========================
# Estas variables son las credenciales y ubicación del servidor SQL.
SERVER = r"DESKTOP-5VDFT83\SQLEXPRESS"
DB = "TaxiML"
USER = "user_daemon"
PWD = "userdaemon"

# create_engine crea un "motor" (engine) para conectarse a SQL usando SQLAlchemy.
# mssql+pyodbc indica que hablamos con SQL Server usando el driver ODBC.
engine = create_engine(
    f"mssql+pyodbc://{USER}:{PWD}@{SERVER}/{DB}?driver=ODBC+Driver+17+for+SQL+Server"
)


# =========================
# 2) Leer FEAT desde SQL
# =========================
# Este query trae un dataset ya "procesado" (features) desde la capa feat.
# Cada fila representa una combinación (fecha + hora + zona) con variables agregadas.
query = """
SELECT
  trip_date,
  pickup_hour,
  PULocationID,
  trips_count,
  avg_trip_distance,
  avg_trip_duration_min,
  avg_total_amount
FROM feat.features_hour_zone
"""

# pd.read_sql ejecuta el query y lo trae como un DataFrame (tabla en memoria).
df = pd.read_sql(query, engine)

print("Filas leídas:", len(df))

# Convertimos trip_date a tipo fecha real (datetime).
df["trip_date"] = pd.to_datetime(df["trip_date"])

# Creamos variables derivadas de la fecha:
# - day_of_week: 0=lunes ... 6=domingo (número de día de semana)
# - month: número de mes (1..12)
# - day_of_month: día del mes (1..31)
df["day_of_week"] = df["trip_date"].dt.dayofweek
df["month"] = df["trip_date"].dt.month
df["day_of_month"] = df["trip_date"].dt.day


# =========================
# 3) Definir y (objetivo) y X (features)
# =========================
# y_real: es el conteo real de viajes.
y_real = df["trips_count"].astype(float)

# y_log: es una versión transformada para entrenar mejor.
# np.log1p(y_real) = log(1 + y_real)
# ¿Por qué se usa?
# - Si hay valores muy altos (picos), el modelo puede sesgarse.
# - El log "comprime" esos picos, haciendo el entrenamiento más estable.
y_log = np.log1p(y_real)

# X: variables de entrada del modelo.
# Son las columnas que el modelo va a usar para predecir y.
X = df[[
  "pickup_hour",
  "day_of_week",
  "month",
  "day_of_month",
  "avg_trip_distance",
  "avg_trip_duration_min",
  "avg_total_amount"
]].copy()

# ----------------------------------------------------------
# PULocationID como categórica -> one-hot encoding (get_dummies)
# ----------------------------------------------------------
# PULocationID es una "zona" (categoría). Un modelo lineal no entiende bien
# categorías como números, porque "zona 100" no significa "más" que "zona 10".
#
# Por eso se convierte a columnas binarias 0/1:
# - PULocationID_10, PULocationID_11, PULocationID_12, ...
# Cada fila tendrá 1 en la columna que corresponde a su zona, y 0 en las demás.
#
# pd.get_dummies hace esa transformación automáticamente.
#
# drop_first=True:
# - Se elimina una categoría para evitar multicolinealidad perfecta
#   (el famoso "dummy variable trap") en modelos lineales.
X = pd.get_dummies(
    X.join(df["PULocationID"].astype("int").astype("category")),
    columns=["PULocationID"],
    drop_first=True
)

print("Columnas X:", X.shape[1])


# =========================
# 4) Split Train/Test
# =========================
# train_test_split divide datos en:
# - train: para entrenar
# - test : para evaluar
#
# test_size=0.2 -> 20% test, 80% train
# random_state=42 -> hace la separación reproducible (si corres el script,
# queda el mismo split)
#
# Aquí se pasan 3 "objetivos" a la vez: X, y_log, y_real.
# sklearn los separa con el MISMO corte, para que:
# - y_log y y_real sigan alineados fila a fila con X_train / X_test.
X_train, X_test, y_train_log, y_test_log, y_train_real, y_test_real = train_test_split(
    X, y_log, y_real, test_size=0.2, random_state=42
)

print("Train:", X_train.shape, "Test:", X_test.shape)


# =========================
# 5) Entrenar modelo con "pesos" (sample_weight)
# =========================
# sample_weight permite decirle al modelo:
# "estas filas importan más que estas otras".
#
# La idea aquí: darle más importancia a casos con conteos altos (picos),
# para que el modelo aprenda mejor esos escenarios.
#
# OJO: tú entrenas con y_train_log (log), pero los pesos se basan en y_train_real (real).
# Esto tiene sentido si lo que quieres es "priorizar picos reales".

# Creamos un vector de pesos del mismo tamaño que y_train_real.
# Por defecto todas las filas pesan 1.
weights = np.ones(len(y_train_real), dtype=float)

# Marcamos casos "altos" y "pico" según umbrales.
# - Si trips_count > 200 -> peso mayor
# - Si trips_count > 500 -> peso aún mayor (sobrescribe el anterior)
weights[y_train_real > 200] = 3.0
weights[y_train_real > 500] = 8.0


# OPCIÓN A: Ajustar prints a 3 y 8
# OPCIÓN B: Ajustar pesos a 5 y 10 (si eso era lo planeado)
print("Weights resumen:")
print(" - peso=1  (normal):", int((weights == 1).sum()))
print(" - peso=3  (alto):  ", int((weights == 3).sum()))
print(" - peso=8  (pico):  ", int((weights == 8).sum()))

# Entrenamos el modelo lineal.
# Aprende a predecir y_train_log a partir de X_train, usando weights.
model = LinearRegression()
model.fit(X_train, y_train_log, sample_weight=weights)


# =========================
# 6) Guardar artefactos
# =========================
# Creamos carpeta artifacts/ si no existe.
os.makedirs("artifacts", exist_ok=True)

# Guardamos el modelo ya entrenado.
joblib.dump(model, "artifacts/linreg_trips_count_v2.joblib")

# Guardamos X_test: las entradas que se usan para validar.
X_test.to_csv("artifacts/X_test_v2.csv", index=False)

# Guardamos el objetivo REAL para evaluar resultados en escala real.
y_test_real.to_csv("artifacts/y_test_real_v2.csv", index=False)

# Guardamos también el objetivo en log (opcional, útil para debug).
y_test_log.to_csv("artifacts/y_test_log_v2.csv", index=False)

print("✅ Guardado:")
print("- artifacts/linreg_trips_count_v2.joblib")
print("- artifacts/X_test_v2.csv")
print("- artifacts/y_test_real_v2.csv   (para validar)")
print("- artifacts/y_test_log_v2.csv    (debug opcional)")
