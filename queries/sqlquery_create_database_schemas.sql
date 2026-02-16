/* 
=========================================================
00_create_database_and_schemas.sql

IDEA :
- Vamos a crear una "caja grande" llamada TaxiML.
- Dentro de esa caja vamos a crear "carpetas" (schemas)
  para guardar las cosas ordenadas por etapas.
=========================================================
*/

-- 1) Crear la base de datos (la "caja grande")
-- Si no existe, la creamos. Si ya existe, no hacemos nada.
IF DB_ID('TaxiML') IS NULL
BEGIN
    CREATE DATABASE TaxiML;
END
GO

-- 2) Decirle a SQL Server: "vamos a trabajar dentro de TaxiML"
USE TaxiML;
GO

-- 3) Crear las "carpetas" (schemas) para ordenar las tablas

-- raw = donde guardo datos crudos (tal cual llegan)
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'raw')
BEGIN
    EXEC('CREATE SCHEMA raw');
END
GO

-- curated = donde guardo datos limpios y listos para usar
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'curated')
BEGIN
    EXEC('CREATE SCHEMA curated');
END
GO

-- feat = donde guardo features (columnas calculadas para ML)
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'feat')
BEGIN
    EXEC('CREATE SCHEMA feat');
END
GO

-- ml = donde guardo salidas del modelo (predicciones, m�tricas, etc.)
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'ml')
BEGIN
    EXEC('CREATE SCHEMA ml');
END
GO
