"""
SCRIPT: Cargar archivos .parquet a SQL Server (tabla raw.yellow_trips)

¿Para qué sirve?
- Lee muchos archivos .parquet desde una carpeta (PARQUET_DIR).
- Por cada archivo:
  1) lo carga a un DataFrame (tabla en memoria con pandas)
  2) asegura que tenga las columnas esperadas y tipos correctos
  3) agrega una columna para saber de qué archivo salió cada fila (source_file)
  4) inserta los datos en SQL Server en la tabla definida por TABLE

¿En qué escenario se usa?
- Cuando descargaste datos (ej: NYC Taxi) en formato parquet y quieres guardarlos en una tabla SQL
  para luego hacer consultas, limpieza, features, modelos, etc.

Requisitos:
- Python con: pandas, numpy, pyodbc
- SQL Server accesible y un driver ODBC instalado (ej: ODBC Driver 17 for SQL Server)
- Que exista la carpeta con los .parquet
"""

from pathlib import Path
import pandas as pd
import numpy as np
import pyodbc

# ============================================================
# 1) CONFIGURACIÓN (ajusta esto según tu PC / servidor / rutas)
# ============================================================

# Datos de conexión a SQL Server
SERVER = r"DESKTOP-5VDFT83\SQLEXPRESS"  # nombre del servidor\instancia
DB = "TaxiML"                           # base de datos
USER = "user_daemon"                    # usuario SQL
PWD = "userdaemon"                      # contraseña SQL

# Carpeta donde están los archivos .parquet (entrada)
PARQUET_DIR = Path(r"C:\Users\Keiver\Downloads\Proyecto_RegresionLineal\data\raw\yellow")

# Tabla destino (schema.tabla) en SQL Server
TABLE = "raw.yellow_trips"

# ==================================
# 2) CONEXIÓN A LA BASE DE DATOS SQL
# ==================================

# Creamos la conexión con pyodbc usando el driver ODBC
# Encrypt=yes + TrustServerCertificate=yes:
# - cifra la conexión (Encrypt)
# - permite confiar en el certificado sin validarlo (útil en local/lab; en prod se revisa bien)
conn = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DB};"
    f"UID={USER};"
    f"PWD={PWD};"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)

# autocommit=False significa:
# - Los INSERT no se “guardan” automáticamente.
# - Necesitas llamar conn.commit() para confirmar los cambios.
# Esto es útil para tener control: si algo falla, puedes evitar que queden datos “a medias”.
conn.autocommit = False


def ensure_table(cursor):
    """
    Asegura que la tabla destino exista.

    ¿Qué hace?
    - Pregunta a SQL Server: "¿existe la tabla raw.yellow_trips?"
    - Si NO existe, la crea con la estructura esperada.

    Nota:
    - Si la tabla ya existe, no hace nada (no la borra ni la modifica).
    """
    cursor.execute(f"""
    IF OBJECT_ID('{TABLE}', 'U') IS NULL
    BEGIN
        CREATE TABLE {TABLE} (
            VendorID INT NULL,
            tpep_pickup_datetime DATETIME2 NULL,
            tpep_dropoff_datetime DATETIME2 NULL,
            passenger_count FLOAT NULL,
            trip_distance FLOAT NULL,
            RatecodeID FLOAT NULL,
            store_and_fwd_flag VARCHAR(5) NULL,
            PULocationID INT NULL,
            DOLocationID INT NULL,
            payment_type FLOAT NULL,
            fare_amount FLOAT NULL,
            extra FLOAT NULL,
            mta_tax FLOAT NULL,
            tip_amount FLOAT NULL,
            tolls_amount FLOAT NULL,
            improvement_surcharge FLOAT NULL,
            total_amount FLOAT NULL,
            congestion_surcharge FLOAT NULL,
            Airport_fee FLOAT NULL,
            cbd_congestion_fee FLOAT NULL,
            source_file VARCHAR(260) NULL
        );
    END
    """)


def prep_df(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    """
    Prepara (limpia/estandariza) el DataFrame para poder insertarlo a SQL sin problemas.

    Objetivos:
    1) Asegurar que existan todas las columnas esperadas.
    2) Reordenar columnas (para que el INSERT coincida).
    3) Convertir tipos:
       - fechas -> datetime
       - enteros -> Int64 (entero “nullable” de pandas, permite NULL)
       - floats -> numérico
       - strings -> string
    4) Agregar "source_file" para trazabilidad (saber de cuál parquet salió cada fila).
    """

    # Lista oficial de columnas que queremos guardar (en este orden)
    cols = [
        "VendorID", "tpep_pickup_datetime", "tpep_dropoff_datetime", "passenger_count", "trip_distance",
        "RatecodeID", "store_and_fwd_flag", "PULocationID", "DOLocationID", "payment_type", "fare_amount",
        "extra", "mta_tax", "tip_amount", "tolls_amount", "improvement_surcharge", "total_amount",
        "congestion_surcharge", "Airport_fee", "cbd_congestion_fee"
    ]

    # -----------------------------
    # (1) Garantizar columnas
    # -----------------------------
    # Si el parquet viene sin alguna columna (o cambia de versión),
    # aquí la creamos con None (equivalente a NULL).
    for c in cols:
        if c not in df.columns:
            df[c] = None

    # Nos quedamos SOLO con estas columnas y en este orden
    # .copy() evita que pandas nos dé advertencias por modificar “vistas”
    df = df[cols].copy()

    # -----------------------------
    # (2) Convertir fechas
    # -----------------------------
    # errors="coerce" significa:
    # - si una fecha viene dañada o vacía, la convierte en NaT (fecha nula)
    df["tpep_pickup_datetime"] = pd.to_datetime(df["tpep_pickup_datetime"], errors="coerce")
    df["tpep_dropoff_datetime"] = pd.to_datetime(df["tpep_dropoff_datetime"], errors="coerce")

    # -----------------------------
    # (3) Convertir enteros (nullable)
    # -----------------------------
    # Int64 de pandas permite valores enteros con nulos (NULL).
    for c in ["VendorID", "PULocationID", "DOLocationID"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")

    # -----------------------------
    # (4) Convertir floats (numérico)
    # -----------------------------
    # Calculamos cuáles columnas deben ser float (todas menos enteros, strings y fechas)
    float_cols = [
        c for c in cols
        if c not in ["VendorID", "PULocationID", "DOLocationID", "store_and_fwd_flag",
                     "tpep_pickup_datetime", "tpep_dropoff_datetime"]
    ]
    for c in float_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # -----------------------------
    # (5) Convertir strings
    # -----------------------------
    # store_and_fwd_flag suele ser "Y"/"N" o null, lo dejamos como string de pandas
    df["store_and_fwd_flag"] = df["store_and_fwd_flag"].astype("string")

    # -----------------------------
    # (6) Trazabilidad
    # -----------------------------
    # Guardamos el nombre del archivo para poder rastrear el origen del dato
    df["source_file"] = source_file

    return df


def to_py(x):
    """
    Convierte valores de pandas/numpy a tipos nativos de Python para que pyodbc los inserte bien.

    ¿Por qué esto es necesario?
    - pandas usa tipos especiales (ej: Int64 nullable, Timestamp, NA)
    - pyodbc a veces no sabe cómo insertar esos tipos directamente
    - por eso transformamos a: int, float, datetime de Python o None (NULL)
    """
    if x is None:
        return None
    if pd.isna(x):
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, pd.Timestamp):
        return x.to_pydatetime()
    # pandas string -> str
    # (Si detecta tipos “NA” de pandas, los manda a NULL)
    if isinstance(x, pd.StringDtype) or isinstance(x, pd._libs.missing.NAType):
        return None
    return x


def insert_df(cursor, df: pd.DataFrame, batch_size=5000):
    """
    Inserta un DataFrame en SQL Server usando INSERT + executemany (por lotes).

    Puntos clave:
    - cursor.fast_executemany = True:
      acelera muchísimo inserts masivos con pyodbc en SQL Server.
    - batch_size:
      inserta en grupos para no saturar memoria/tiempo (ej: 5000 filas por “viaje”).
    """
    cursor.fast_executemany = True

    # SQL parametrizado: usamos ? para evitar construir valores dentro del SQL
    # (más seguro y más estable para tipos)
    sql = f"""
    INSERT INTO {TABLE} (
      VendorID,tpep_pickup_datetime,tpep_dropoff_datetime,passenger_count,trip_distance,
      RatecodeID,store_and_fwd_flag,PULocationID,DOLocationID,payment_type,fare_amount,
      extra,mta_tax,tip_amount,tolls_amount,improvement_surcharge,total_amount,
      congestion_surcharge,Airport_fee,cbd_congestion_fee,source_file
    )
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """

    # Convertimos el DataFrame a una lista de tuplas “listas para SQL”
    # df.itertuples(...) recorre fila por fila de forma eficiente
    rows = [tuple(to_py(v) for v in row) for row in df.itertuples(index=False, name=None)]

    # Insert por lotes: 0..4999, 5000..9999, etc.
    for i in range(0, len(rows), batch_size):
        cursor.executemany(sql, rows[i:i + batch_size])


def main():
    """
    Orquesta todo el proceso (pipeline):
    1) abre cursor
    2) asegura tabla
    3) busca archivos .parquet
    4) por cada archivo: leer -> preparar -> insertar -> commit
    5) cierra conexión
    """
    cur = conn.cursor()

    # Creamos la tabla si no existe (y confirmamos esa creación)
    ensure_table(cur)
    conn.commit()

    # Buscamos todos los .parquet en la carpeta (ordenados)
    files = sorted(PARQUET_DIR.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No encontré .parquet en: {PARQUET_DIR}")

    # Recorremos archivo por archivo (esto ayuda a manejar volúmenes grandes)
    for f in files:
        print("Cargando:", f.name)

        # 1) Leer parquet -> DataFrame
        df = pd.read_parquet(f)

        # 2) Preparar (columnas/tipos + source_file)
        df = prep_df(df, f.name)

        # 3) Insertar a SQL
        insert_df(cur, df)

        # 4) Confirmar (guardar cambios) por archivo
        conn.commit()

        print("OK -> filas:", len(df))

    # Cierre limpio de recursos
    cur.close()
    conn.close()

    print("Listo: cargado a raw.yellow_trips")


# Punto de entrada del script:
# Esto hace que main() solo se ejecute si corres este archivo directamente,
# y no si lo importas desde otro script.
if __name__ == "__main__":
    main()
