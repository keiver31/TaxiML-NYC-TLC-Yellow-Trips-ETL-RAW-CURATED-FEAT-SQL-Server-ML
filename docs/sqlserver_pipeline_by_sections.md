# SQL Server Pipeline (RAW → CURATED → FEAT) — Ejecución por secciones

Archivo asociado: `queries/sqlserver_pipeline_by_sections.sql`

Este script arma el flujo de datos dentro de SQL Server en tres capas:

- `raw`     → datos crudos (llegan tal cual; normalmente los carga Python)
- `curated` → datos limpios (se construyen desde `raw` con reglas básicas)
- `feat`    → tabla resumida para analítica / Machine Learning (features)
- `ml`      → reservado para predicciones y métricas (no implementado aquí)

## Convención de ejecución

El archivo está dividido por secciones independientes.  
Cada sección está marcada con:

- `INICIO SECCIÓN XX`
- `FIN SECCIÓN XX`

La ejecución recomendada es por bloque completo (sección completa) para evitar estados intermedios.

---

## Dependencias y precondiciones

- Motor: Microsoft SQL Server.
- Herramienta: SSMS (o un cliente que respete `GO`).
- Base de datos objetivo: `TaxiML`.
- Tabla de entrada esperada:
  - `raw.yellow_trips` debe existir y contener datos antes de construir `curated` y `feat`.
  - Esta tabla se espera que sea alimentada desde el proceso de carga en Python.

---

## Diseño del pipeline

### 1) Capa RAW (`raw.yellow_trips`)
Propósito: persistir el dato tal cual llega (sin limpieza).  
Origen: carga externa (Python).  
Uso en este script: solo verificación y lectura.

### 2) Capa CURATED (`curated.yellow_trips`)
Propósito: normalizar y filtrar registros inválidos desde RAW.  
Salida esperada: 1 fila = 1 viaje válido.

Reglas de limpieza aplicadas:
- fechas no nulas
- `dropoff > pickup`
- `trip_distance > 0`
- `total_amount > 0`

Además:
- se calcula `trip_duration_min` como duración del viaje en minutos.
- se conserva `source_file` para trazabilidad.

### 3) Capa FEAT (`feat.features_hour_zone`)
Propósito: resumir viajes (curated) en grupos útiles para modelos/analítica.  
Salida esperada: 1 fila = (fecha + hora + zona pickup).

Métricas creadas por grupo:
- `trips_count`
- `avg_trip_distance`
- `avg_trip_duration_min`
- `avg_total_amount`

---

# Secciones del script

## Sección 00 — Base de datos y Schemas

Alcance:
- crea la base `TaxiML` si no existe.
- crea schemas `raw`, `curated`, `feat`, `ml` si no existen.

Notas:
- esta sección se ejecuta normalmente una sola vez por ambiente.
- utiliza `DB_ID()` y `sys.schemas` para validar existencia.

Artefactos generados:
- `TaxiML` (si no existía)
- `raw`, `curated`, `feat`, `ml` (si no existían)

---

## Sección 01 — Verificación de RAW

Alcance:
- valida existencia de `raw.yellow_trips` usando `OBJECT_ID`.
- si existe, muestra `TOP 5` ordenado por `tpep_pickup_datetime DESC`.
- si no existe, informa que primero debe ejecutarse el proceso de carga (Python).

Artefactos generados:
- ninguno (solo lectura y mensajes).

---

## Sección 02 — Construcción de CURATED (RAW → CURATED)

Alcance:
- valida que exista `raw.yellow_trips`.
- elimina `curated.yellow_trips` si ya existe (reconstrucción completa).
- crea `curated.yellow_trips` mediante `SELECT ... INTO ...` desde RAW.
- aplica filtros de calidad y calcula `trip_duration_min`.
- muestra `TOP 5` de la tabla construida.

Artefactos generados:
- `curated.yellow_trips` (recreada en cada ejecución de la sección).

Comportamiento de reconstrucción:
- la tabla `curated.yellow_trips` se borra y se crea de nuevo para garantizar consistencia con RAW.

---

## Sección 03 — Construcción de FEAT (CURATED → FEAT)

Alcance:
- valida existencia de `curated.yellow_trips`.
- elimina `feat.features_hour_zone` si ya existe (reconstrucción completa).
- crea `feat.features_hour_zone` con agregaciones por:
  - `trip_date` (fecha)
  - `pickup_hour` (hora)
  - `PULocationID` (zona pickup)
- muestra `TOP 5` del resultado.

Artefactos generados:
- `feat.features_hour_zone` (recreada en cada ejecución de la sección).

---

## Sección 04 — ML (placeholder)

Alcance:
- no crea tablas.
- deja un mensaje guía para futura expansión (predicciones, métricas, versionado).

Artefactos generados:
- ninguno.

---

## Sección 05 — Validaciones

Alcance:
- valida existencia de tablas (`OBJECT_ID`).
- realiza conteo total de filas por capa:
  - `raw.yellow_trips`
  - `curated.yellow_trips`
  - `feat.features_hour_zone`
- muestra preview `TOP 5` de cada tabla.
- sanity checks:
  - rangos de fecha (mín/max) en RAW y CURATED
  - duplicados en FEAT por (fecha, hora, zona)
  - coherencia de `trips_count` (mín/max)

Artefactos generados:
- ninguno (solo lectura).

---

## Glosario

### Organización
- **Schema**: agrupador lógico dentro de una base de datos para organizar tablas (ej: `raw`, `curated`).
- **Capa RAW**: datos crudos, sin limpieza.
- **Capa CURATED**: datos depurados y normalizados.
- **Capa FEAT**: tabla de variables (features) resumidas para análisis o modelos.
- **Pipeline**: cadena de pasos donde una capa alimenta a la siguiente.

### SQL Server / ejecución
- **SSMS**: herramienta estándar para ejecutar scripts en SQL Server.
- **GO**: separador de lotes; indica al cliente que ejecute el bloque anterior como una unidad.
- **PRINT**: salida de texto en consola para trazabilidad del flujo.

### Consultas
- **OBJECT_ID('schema.tabla','U')**: devuelve un identificador si la tabla existe, o `NULL` si no existe.
- **SELECT TOP (N)**: devuelve solo N filas para inspección rápida.
- **SELECT ... INTO**: crea una tabla nueva con el resultado del SELECT.
- **DROP TABLE**: elimina una tabla.

### Transformación / agregación
- **WHERE**: filtro de registros (control de calidad).
- **GROUP BY**: agrupa registros para calcular métricas por grupo.
- **COUNT(*)**: número de registros dentro de un grupo.
- **AVG(...)**: promedio dentro de un grupo.
- **CAST(... AS date)**: extrae solo la fecha de un datetime.
- **DATEPART(HOUR, ...)**: extrae la hora (0–23) de un datetime.
- **DATEDIFF**: calcula diferencias entre fechas (aquí se usa para duración del viaje).

### Validación
- **Sanity check**: verificación rápida para confirmar que los datos tienen sentido (rangos, duplicados, conteos).

