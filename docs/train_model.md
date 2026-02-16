# TaxiML — Entrenamiento de Regresión Lineal (trips_count) desde SQL Server

Este script entrena un modelo de **Regresión Lineal** para predecir el **número de viajes por hora** (`trips_count`) usando variables temporales (hora, día, mes) y promedios agregados (distancia, duración y monto), tomando los datos desde una tabla de **features** en SQL Server.

El modelo se entrena sobre una transformación logarítmica del objetivo: `log(1 + trips_count)` para estabilizar la variabilidad cuando hay valores muy altos (picos).

---

## ¿Qué hace este script?

1. Se conecta a **SQL Server** usando SQLAlchemy + pyodbc.
2. Consulta una tabla de **features**: `feat.features_hour_zone`.
3. Genera variables de calendario a partir de `trip_date`.
4. Define:
   - `X`: variables predictoras (features).
   - `y_real`: objetivo en escala real (`trips_count`).
   - `y_log`: objetivo transformado (`log1p(y_real)`).
5. Convierte `PULocationID` a variables binarias (one-hot encoding).
6. Divide en conjuntos de **entrenamiento** y **prueba** (train/test split).
7. Entrena un modelo `LinearRegression` usando `sample_weight` para ponderar casos con conteos altos.
8. Guarda artefactos (modelo y datasets de prueba) en la carpeta `artifacts/`.

---

## Requisitos

### Librerías Python
- `pandas`
- `numpy`
- `sqlalchemy`
- `pyodbc`
- `scikit-learn`
- `joblib`

Instalación sugerida:

```bash
pip install pandas numpy sqlalchemy pyodbc scikit-learn joblib
