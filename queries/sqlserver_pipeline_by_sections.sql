/* 
=========================================================
00_sqlserver_pipeline_by_sections_explained.sql

OBJETIVO (en fácil):
Este archivo prepara y construye tu pipeline en SQL Server así:

RAW (datos crudos)  ->  CURATED (datos limpios)  ->  FEAT (features para ML)

REGLA DE ORO:
- NO ejecutes todo de una.
- Selecciona una sección completa (desde INICIO hasta FIN) y presiona F5.

Qué significa cada “carpeta” (schema):
- raw     = datos crudos tal cual llegan (normalmente los carga Python)
- curated = datos limpios (los construye SQL)
- feat    = tabla final para ML (features resumidas)
- ml      = a futuro: predicciones y métricas del modelo
=========================================================
*/

-- =========================================================
-- SECCIÓN 00) CREAR BASE DE DATOS + SCHEMAS
-- (esto normalmente se ejecuta SOLO una vez)
-- =========================================================
PRINT '========== ✅ INICIO SECCIÓN 00: DB + SCHEMAS ==========';

-- DB_ID('TaxiML') devuelve un número si la base existe, o NULL si no existe.
-- Entonces esta condición significa:
-- "Si TaxiML NO existe, créala"
IF DB_ID('TaxiML') IS NULL
BEGIN
    CREATE DATABASE TaxiML;          -- crea la "casa" (base de datos)
    PRINT 'Se creó la base de datos TaxiML.';
END
ELSE
BEGIN
    PRINT 'TaxiML ya existía. No se creó de nuevo.';
END
GO

-- USE TaxiML significa: "Ahora todo lo que haga, lo haré dentro de la base TaxiML"
USE TaxiML;
GO

-- Un schema es como una “carpeta/cuarto” dentro de la base.
-- Aquí creamos 4 “carpetas” para organizar tablas.

-- Si el schema raw NO existe, lo creamos
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'raw')
BEGIN
    EXEC('CREATE SCHEMA raw'); -- EXEC ejecuta una cadena de texto como comando SQL
    PRINT 'Se creó el schema raw.';
END
ELSE PRINT 'Schema raw ya existía.';
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'curated')
BEGIN
    EXEC('CREATE SCHEMA curated');
    PRINT 'Se creó el schema curated.';
END
ELSE PRINT 'Schema curated ya existía.';
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'feat')
BEGIN
    EXEC('CREATE SCHEMA feat');
    PRINT 'Se creó el schema feat.';
END
ELSE PRINT 'Schema feat ya existía.';
GO

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ml')
BEGIN
    EXEC('CREATE SCHEMA ml');
    PRINT 'Se creó el schema ml.';
END
ELSE PRINT 'Schema ml ya existía.';
GO

PRINT '========== ✅ FIN SECCIÓN 00 =========='; 
GO


-- =========================================================
-- SECCIÓN 01) RAW: VERIFICAR QUE EXISTA LA TABLA RAW
-- (RAW normalmente NO se crea aquí, se carga desde Python)
-- =========================================================
PRINT '========== ✅ INICIO SECCIÓN 01: RAW (verificación) ==========';

USE TaxiML;
GO

-- OBJECT_ID('raw.yellow_trips','U') devuelve:
-- - un número (ID interno) si la tabla existe
-- - NULL si la tabla NO existe
SELECT OBJECT_ID('raw.yellow_trips', 'U') AS raw_table_exists;
GO

-- ✅ ANTES / DESPUÉS (en raw solo podemos “ver”, porque raw lo carga Python)
IF OBJECT_ID('raw.yellow_trips', 'U') IS NOT NULL
BEGIN
    PRINT 'RAW existe ✅. Mostrando TOP 5 de raw.yellow_trips';

    -- TOP (5) = solo 5 filas para que sea rápido
    -- ORDER BY ... DESC = lo más reciente primero
    SELECT TOP (5) *
    FROM raw.yellow_trips
    ORDER BY tpep_pickup_datetime DESC;
END
ELSE
BEGIN
    PRINT 'RAW NO existe ❌. Primero corre tu ETL de Python que carga raw.yellow_trips.';
END
GO

PRINT '========== ✅ FIN SECCIÓN 01 =========='; 
GO


-- =========================================================
-- SECCIÓN 02) CURATED: CONSTRUIR TABLA LIMPIA DESDE RAW
-- =========================================================
PRINT '========== ✅ INICIO SECCIÓN 02: RAW → CURATED (limpieza) ==========';

USE TaxiML;
GO

-- ✅ ANTES: mostrar 5 filas del ORIGEN (raw)
IF OBJECT_ID('raw.yellow_trips', 'U') IS NOT NULL
BEGIN
    PRINT 'ANTES (origen) ✅: TOP 5 de raw.yellow_trips';
    SELECT TOP (5) *
    FROM raw.yellow_trips
    ORDER BY tpep_pickup_datetime DESC;
END
ELSE
BEGIN
    PRINT 'ERROR ❌: No existe raw.yellow_trips. No se puede crear curated.';
END
GO

-- Si curated.yellow_trips ya existe, la borramos
-- ¿Por qué? para reconstruirla desde cero y que quede actualizada y limpia.
IF OBJECT_ID('curated.yellow_trips', 'U') IS NOT NULL
BEGIN
    DROP TABLE curated.yellow_trips;
    PRINT 'Se borró curated.yellow_trips (para reconstruirla).';
END
GO

-- Esta consulta hace TODO esto:
-- 1) SELECT: escoge columnas
-- 2) FROM raw.yellow_trips: saca data de raw
-- 3) WHERE: filtra basura / datos raros
-- 4) INTO curated.yellow_trips: crea una tabla nueva en curated y guarda el resultado ahí
SELECT
  VendorID,                      -- quién operó el viaje
  tpep_pickup_datetime,          -- fecha/hora inicio
  tpep_dropoff_datetime,         -- fecha/hora fin
  passenger_count,               -- pasajeros
  trip_distance,                 -- distancia
  PULocationID,                  -- zona pickup
  DOLocationID,                  -- zona dropoff
  total_amount,                  -- total pagado
  fare_amount,                   -- tarifa base
  tip_amount,                    -- propina
  congestion_surcharge,          -- recargo congestión
  Airport_fee,                   -- tarifa aeropuerto (si aplica)

  -- DATEDIFF(SECOND, inicio, fin) = diferencia en segundos
  -- / 60.0 = convertir a minutos con decimales
  DATEDIFF(SECOND, tpep_pickup_datetime, tpep_dropoff_datetime) / 60.0 AS trip_duration_min,

  source_file                    -- para saber de qué archivo vino
INTO curated.yellow_trips        -- 👈 CREA LA TABLA Y GUARDA EL RESULTADO
FROM raw.yellow_trips            -- 👈 ORIGEN: RAW
WHERE
  -- “colador”: quitamos registros inválidos
  tpep_pickup_datetime IS NOT NULL
  AND tpep_dropoff_datetime IS NOT NULL
  AND tpep_dropoff_datetime > tpep_pickup_datetime  -- el fin debe ser después del inicio
  AND trip_distance > 0                              -- distancia debe ser positiva
  AND total_amount > 0;                              -- total debe ser positivo
GO

-- ✅ DESPUÉS: mostrar 5 filas del DESTINO (curated)
IF OBJECT_ID('curated.yellow_trips', 'U') IS NOT NULL
BEGIN
    PRINT 'DESPUÉS (destino) ✅: TOP 5 de curated.yellow_trips';
    SELECT TOP (5) *
    FROM curated.yellow_trips
    ORDER BY tpep_pickup_datetime DESC;
END
GO

PRINT '========== ✅ FIN SECCIÓN 02 =========='; 
GO


-- =========================================================
-- SECCIÓN 03) FEAT: CREAR FEATURES (TABLA RESUMIDA PARA ML)
-- =========================================================
PRINT '========== ✅ INICIO SECCIÓN 03: CURATED → FEAT (features) ==========';

USE TaxiML;
GO

-- ✅ ANTES: mostrar 5 filas del ORIGEN (curated)
IF OBJECT_ID('curated.yellow_trips', 'U') IS NOT NULL
BEGIN
    PRINT 'ANTES (origen) ✅: TOP 5 de curated.yellow_trips';
    SELECT TOP (5) *
    FROM curated.yellow_trips
    ORDER BY tpep_pickup_datetime DESC;
END
ELSE
BEGIN
    PRINT 'ERROR ❌: No existe curated.yellow_trips. No se puede crear feat.';
END
GO

-- Si feat.features_hour_zone ya existe, la borramos
IF OBJECT_ID('feat.features_hour_zone', 'U') IS NOT NULL
BEGIN
    DROP TABLE feat.features_hour_zone;
    PRINT 'Se borró feat.features_hour_zone (para reconstruirla).';
END
GO

-- IDEA GRANDE:
-- En curated: 1 fila = 1 viaje
-- En feat:    1 fila = (un día + una hora + una zona)
-- O sea: resumimos muchos viajes en una sola fila por grupo.

SELECT
  -- CAST(... AS date) = quitar la hora y dejar solo la fecha
  CAST(tpep_pickup_datetime AS date) AS trip_date,

  -- DATEPART(HOUR, ...) = sacar la hora (0 a 23)
  DATEPART(HOUR, tpep_pickup_datetime) AS pickup_hour,

  -- Zona del pickup
  PULocationID,

  -- COUNT(*) = cuántos viajes hay en ese grupo (día + hora + zona)
  COUNT(*) AS trips_count,

  -- AVG(...) = promedio (media) de una columna dentro del grupo
  AVG(trip_distance) AS avg_trip_distance,
  AVG(trip_duration_min) AS avg_trip_duration_min,
  AVG(total_amount) AS avg_total_amount
INTO feat.features_hour_zone     -- CREA la tabla de features y guarda aquí el resultado
FROM curated.yellow_trips        -- ORIGEN: curated (ya limpio)
WHERE PULocationID IS NOT NULL   -- sin zona, no podemos agrupar por zona
GROUP BY
  -- GROUP BY define qué significa “un grupo”
  CAST(tpep_pickup_datetime AS date),
  DATEPART(HOUR, tpep_pickup_datetime),
  PULocationID;
GO

-- ✅ DESPUÉS: mostrar 5 filas del DESTINO (feat)
IF OBJECT_ID('feat.features_hour_zone', 'U') IS NOT NULL
BEGIN
    PRINT 'DESPUÉS (destino) ✅: TOP 5 de feat.features_hour_zone';
    SELECT TOP (5) *
    FROM feat.features_hour_zone
    ORDER BY trip_date DESC, pickup_hour DESC, PULocationID;
END
GO

PRINT '========== ✅ FIN SECCIÓN 03 =========='; 
GO


-- =========================================================
-- SECCIÓN 04) ML (placeholder): SOLO NOTA PARA EL FUTURO
-- =========================================================
PRINT '========== ✅ INICIO SECCIÓN 04: ML (placeholder) ==========';

-- Esta sección no crea tablas aún.
-- Solo te recuerda que aquí irían:
-- - predicciones
-- - métricas
-- - versiones del modelo
PRINT 'SECCIÓN 04) ML: (a futuro) tablas para predicciones y métricas del modelo.';
GO

PRINT '========== ✅ FIN SECCIÓN 04 =========='; 
GO


-- =========================================================
-- SECCIÓN 05) VALIDACIONES: CONTAR Y VER DATOS (RAW/CURATED/FEAT)
-- =========================================================
PRINT '========== ✅ INICIO SECCIÓN 05: VALIDACIONES ==========';

USE TaxiML;
GO

-- 05.1) Ver si existen las tablas (si devuelven NULL, no existen)
SELECT 
  OBJECT_ID('raw.yellow_trips', 'U')     AS raw_yellow_trips_exists,
  OBJECT_ID('curated.yellow_trips', 'U') AS curated_yellow_trips_exists,
  OBJECT_ID('feat.features_hour_zone', 'U') AS feat_features_exists;
GO

-- 05.2) Conteo total de filas (esto dice cuántos registros hay en cada tabla)
SELECT 'raw.yellow_trips' AS table_name, COUNT(*) AS total_rows
FROM raw.yellow_trips;
GO

SELECT 'curated.yellow_trips' AS table_name, COUNT(*) AS total_rows
FROM curated.yellow_trips;
GO

SELECT 'feat.features_hour_zone' AS table_name, COUNT(*) AS total_rows
FROM feat.features_hour_zone;
GO

-- 05.3) Preview (solo 5 filas para no saturar)
PRINT 'Preview TOP 5 RAW:';
SELECT TOP (5) * FROM raw.yellow_trips ORDER BY tpep_pickup_datetime DESC;

PRINT 'Preview TOP 5 CURATED:';
SELECT TOP (5) * FROM curated.yellow_trips ORDER BY tpep_pickup_datetime DESC;

PRINT 'Preview TOP 5 FEAT:';
SELECT TOP (5) * FROM feat.features_hour_zone ORDER BY trip_date DESC, pickup_hour DESC;

-- 05.4) Sanity checks (fechas mínimas y máximas)
SELECT 
  'raw.yellow_trips' AS table_name,
  MIN(tpep_pickup_datetime) AS min_pickup,
  MAX(tpep_pickup_datetime) AS max_pickup
FROM raw.yellow_trips;
GO

SELECT 
  'curated.yellow_trips' AS table_name,
  MIN(tpep_pickup_datetime) AS min_pickup,
  MAX(tpep_pickup_datetime) AS max_pickup
FROM curated.yellow_trips;
GO

--Que no haya duplicados en FEAT (debería ser 0 filas):
SELECT trip_date, pickup_hour, PULocationID, COUNT(*) AS c
FROM feat.features_hour_zone
GROUP BY trip_date, pickup_hour, PULocationID
HAVING COUNT(*) > 1;
GO

--Que FEAT tenga datos coherentes (por ejemplo trips_count mínimo >= 1):
SELECT 
  MIN(trips_count) AS min_trips,
  MAX(trips_count) AS max_trips
FROM feat.features_hour_zone;
GO



PRINT '========== ✅ FIN SECCIÓN 05 =========='; 
GO



