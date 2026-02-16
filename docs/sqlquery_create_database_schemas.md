# Creación de base de datos y schemas (TaxiML)

Archivo asociado: `SQLQuery_Create_Database_Schemas.sql`

Este script inicializa el entorno de trabajo en SQL Server creando una base de datos y los schemas necesarios para organizar el pipeline de datos por etapas (crudo → limpio → features → modelo).

---

## Propósito

- Crear la base de datos **`TaxiML`** si aún no existe.
- Definir la estructura mínima de organización mediante cuatro schemas:
  - `raw`
  - `curated`
  - `feat`
  - `ml`

El script es idempotente: puede ejecutarse varias veces sin duplicar objetos, ya que valida existencia antes de crear.

---

## Estructura lógica resultante

Base de datos:
- `TaxiML`

Schemas (organización por capas):
- `raw`     → datos crudos tal cual llegan desde fuentes externas (normalmente Python).
- `curated` → datos limpios listos para análisis.
- `feat`    → tablas con variables calculadas (features) para modelos.
- `ml`      → salida de modelos: predicciones, métricas y versionamiento (cuando aplique).

---

## Qué hace el script (por bloques)

### 1) Creación de la base de datos

- Verifica si existe `TaxiML` usando `DB_ID('TaxiML')`.
- Si no existe, ejecuta `CREATE DATABASE TaxiML`.

Resultado:
- `TaxiML` queda creada o confirmada como existente.

---

### 2) Selección del contexto de trabajo

- Ejecuta `USE TaxiML` para que las siguientes instrucciones se apliquen dentro de esa base.

Resultado:
- El script opera sobre la base correcta.

---

### 3) Creación de schemas

Para cada schema (`raw`, `curated`, `feat`, `ml`):
- Verifica existencia en `sys.schemas`.
- Si no existe, lo crea con `CREATE SCHEMA ...` ejecutado mediante `EXEC(...)`.

Resultado:
- Los cuatro schemas quedan creados o confirmados como existentes.

---

## Artefactos creados

- Base de datos: `TaxiML`
- Schemas:
  - `raw`
  - `curated`
  - `feat`
  - `ml`

---

## Glosario

- **Base de datos**: contenedor principal donde se almacenan tablas, vistas y otros objetos.
- **Schema**: agrupador lógico dentro de la base de datos para organizar objetos (similar a una carpeta).
- **Idempotente**: se puede ejecutar varias veces sin cambiar el resultado final ni duplicar objetos.
- **`DB_ID()`**: función que retorna el identificador de una base de datos si existe; si no, retorna `NULL`.
- **`sys.schemas`**: vista del sistema que lista los schemas existentes en la base de datos.
- **`EXEC()`**: ejecuta un comando SQL escrito como texto (string).
- **`GO`**: separador de lotes; indica al cliente (SSMS) que ejecute el bloque anterior.

