# CARGUE DE ARCHIVOS .PARQUET A SQL SERVER (RAW.YELLOW_TRIPS) — PYTHON

Archivo: `load_parquet_to_sqlserver.py`

Importante:
- Este script toma **muchos archivos `.parquet`** (por ejemplo, los viajes de taxi) desde una carpeta y los **carga a SQL Server** en la tabla **`raw.yellow_trips`**.
- El cargue es **archivo por archivo**. Por cada archivo:
  1) lo lee a una “tabla en memoria”
  2) valida/acomoda columnas y tipos de dato
  3) agrega una columna para saber el origen (**`source_file`**)
  4) inserta las filas en SQL Server
  5) hace **commit** (guarda los cambios) de ese archivo
- Si la tabla **no existe**, el script intenta **crearla** con la estructura esperada.
- El script **NO borra** la tabla ni elimina datos existentes: **si lo ejecutas dos veces con los mismos archivos, podrías duplicar datos**.

---

## ¿Para qué sirve?

Cuando ya descargaste datos en `.parquet` (por ejemplo, `yellow_tripdata_2024-01.parquet`) y quieres tenerlos en una base de datos SQL para:
- Consultarlos con SQL
- Limpiarlos por capas (raw → curated)
- Crear variables (features)
- Entrenar modelos (ML)
- Construir reportes (Power BI)

---

## Qué entra y qué sale

### Entradas
- **Carpeta** con archivos `.parquet` (configurada en `PARQUET_DIR`)
- **SQL Server** accesible (configuración en `SERVER`, `DB`, `USER`, `PWD`)

### Salida
- Tabla en SQL Server: **`raw.yellow_trips`** con todas las filas insertadas
- Consola: mensajes tipo `Cargando: ...` y `OK -> filas: ...`

---

## Requisitos (antes de ejecutar)

### Python
Instala (mínimo) lo siguiente:
- `pandas`
- `numpy`
- `pyodbc`

Y MUY importante para leer `.parquet`:
- `pyarrow` **o** `fastparquet`

Comando sugerido:
- `pip install pandas numpy pyodbc pyarrow`

### SQL Server
- Tener acceso a SQL Server (instancia correcta y credenciales correctas)
- Tener instalado el driver:
  - **ODBC Driver 17 for SQL Server** (o uno compatible)

### Esquema `raw`
El script crea la tabla `raw.yellow_trips` si no existe, **pero asume que el esquema `raw` ya existe**.
- Si `raw` no existe, SQL Server puede fallar con error de esquema.

> Recomendación: crea el esquema una vez:
> `CREATE SCHEMA raw;`

---

## Configuración rápida (lo que sí o sí debes ajustar)

En la sección **1) CONFIGURACIÓN**:

- `SERVER`: nombre del equipo e instancia  
  Ejemplo: `DESKTOP-5VDFT83\SQLEXPRESS`

- `DB`: base de datos  
  Ejemplo: `TaxiML`

- `USER` y `PWD`: usuario y contraseña

- `PARQUET_DIR`: carpeta donde están los `.parquet`  
  Ejemplo: `C:\...\data\raw\yellow`

- `TABLE`: tabla destino  
  Ejemplo: `raw.yellow_trips`

> Nota de seguridad (friendly pero importante):
> - Evita dejar la contraseña real escrita en el script si lo vas a subir a GitHub.
> - Idealmente usa variables de entorno o un archivo `.env` que NO subas al repo.

---

## Cómo funciona el script (por secciones)

### 1) Configuración
**Qué hace:**
- Define parámetros básicos: conexión a SQL, carpeta de entrada, tabla destino.

**Por qué importa:**
- Si algo está mal aquí (ruta o credenciales), nada más funcionará.

---

### 2) Conexión a la base de datos (SQL Server)
**Qué hace:**
- Abre una conexión con `pyodbc` usando un driver ODBC.
- Deja `autocommit = False` para que tú “guardes” con `conn.commit()` cuando toque.

**Qué significa en la práctica:**
- El script puede controlar cuándo se guardan los cambios.
- Si algo falla a mitad, puedes evitar que queden datos “a medias”.

**Detalle del cifrado:**
- `Encrypt=yes`: intenta cifrar la conexión.
- `TrustServerCertificate=yes`: confía en el certificado sin validarlo (útil en local/lab; en producción se revisa mejor).

---

### 3) `ensure_table(cursor)` — asegurar tabla destino
**Qué hace:**
- Le pregunta a SQL Server: “¿ya existe `raw.yellow_trips`?”
- Si **NO existe**, la crea con columnas y tipos listos para recibir los datos.

**Qué NO hace:**
- No borra la tabla si ya existe.
- No altera la tabla si ya existe con una estructura distinta.

---

### 4) `prep_df(df, source_file)` — preparar datos antes de insertar
Esta es la parte más importante para que el cargue sea estable.

**Qué hace:**
1) Define el listado de columnas oficiales (`cols`) y su orden.
2) Si falta alguna columna en el parquet, la crea con `None` (que en SQL será `NULL`).
3) Reordena y se queda solo con esas columnas.
4) Convierte tipos de dato:
   - Fechas → datetime
   - Enteros → `Int64` de pandas (permite nulos)
   - Numéricos → float/numérico
   - Texto → string
5) Agrega `source_file` para saber de qué archivo salió cada fila.

**Por qué importa:**
- Los `.parquet` a veces cambian de versión (traen más/menos columnas).
- `pandas` maneja nulos y tipos de una forma distinta a SQL Server.
- Esta función “normaliza” todo para que `pyodbc` pueda insertar.

---

### 5) `to_py(x)` — convertir valores “raros” a valores “normales”
**Qué hace:**
- Convierte tipos especiales de pandas/numpy a tipos nativos de Python:
  - `pandas.Timestamp` → `datetime` de Python
  - `Int64 nullable` / `NA` → `None`
  - `np.integer` → `int`
  - `np.floating` → `float`

**Por qué importa:**
- `pyodbc` a veces no sabe insertar directamente tipos internos de pandas.
- `None` es la forma estándar de decir **NULL** en SQL.

---

### 6) `insert_df(cursor, df, batch_size=5000)` — insertar por lotes
**Qué hace:**
- Construye un `INSERT INTO ... VALUES (?, ?, ?...)` (parametrizado).
- Convierte el DataFrame en lista de filas (tuplas).
- Inserta en lotes de `batch_size` (por defecto 5000).
- Activa `cursor.fast_executemany = True` para que sea mucho más rápido.

**Por qué importa:**
- Insertar millones de filas una por una es lento.
- Por lotes es más rápido y más estable.

---

### 7) `main()` — el “director de orquesta”
**Qué hace en orden:**
1) Abre cursor
2) Llama `ensure_table()` y hace `commit()` (por si creó la tabla)
3) Busca todos los `.parquet` dentro de `PARQUET_DIR`
4) Por cada archivo:
   - lee parquet → `df`
   - prepara df → `prep_df`
   - inserta → `insert_df`
   - guarda cambios → `conn.commit()`
5) Cierra cursor y conexión
6) Imprime `Listo: cargado a raw.yellow_trips`

**Idea clave:**
- Se hace `commit()` **por archivo**, lo que ayuda a:
  - Manejar volúmenes grandes
  - Si un archivo falla, los anteriores ya quedaron guardados

---

## Cómo ejecutarlo

1) Verifica que tienes `.parquet` en la carpeta configurada (`PARQUET_DIR`)
2) Ejecuta:
- `python TU_SCRIPT.py`

Salida esperada (ejemplo):
- `Cargando: yellow_tripdata_2024-01.parquet`
- `OK -> filas: 3000000`
- ...
- `Listo: cargado a raw.yellow_trips`

---

## Posibles problemas típicos (y qué significan)

- **“No encontré .parquet en …”**
  - La ruta `PARQUET_DIR` no tiene archivos o está mal escrita.

- **Error de driver ODBC**
  - No tienes instalado “ODBC Driver 17 for SQL Server” o el nombre no coincide.

- **Login failed / permisos**
  - Usuario/clave incorrectos o permisos insuficientes.

- **Error con schema `raw`**
  - El esquema no existe. Debes crearlo una vez en SQL Server.

- **Duplicados**
  - Si ejecutas el script dos veces con los mismos archivos, insertará dos veces.
  - Solución típica: truncar tabla antes, o implementar control por `source_file`.

---

## Glosario (conceptos técnicos, explicado fácil)

### Archivos y datos
- **`.parquet`**: Formato de archivo de datos muy eficiente (pesa menos y se lee rápido). Ideal para analítica.
- **DataFrame**: Tabla en memoria (piénsalo como una hoja de Excel dentro de Python).

### Librerías (Python)
- **pandas**: Librería para leer, transformar y analizar tablas (DataFrames).
- **numpy**: Librería para cálculos numéricos y tipos de datos numéricos (útil para grandes volúmenes).

### Base de datos (SQL Server)
- **SQL Server**: Base de datos de Microsoft donde guardas tablas y haces consultas con SQL.
- **Esquema (schema)**: “Carpeta” dentro de la base de datos para organizar tablas (ej: `raw`, `curated`).
- **`raw`**: Capa/área donde se guardan datos “tal cual llegan”, sin muchas transformaciones.

### Conexión y ejecución de SQL
- **Cursor**: Objeto que ejecuta instrucciones SQL desde Python (SELECT, INSERT, CREATE TABLE, etc.).
- **Transacción**: Grupo de operaciones que se guardan juntas para evitar datos a medias si algo falla.
- **`commit()`**: Acción que confirma/guarda los cambios de la transacción en la base de datos.
- **`autocommit=False`**: Significa que nada se guarda automáticamente; el script decide cuándo guardar con `commit()`.

### Inserciones masivas (cargue rápido)
- **NULL**: Valor “vacío” en SQL. En Python normalmente se representa con `None`.
- **Insert por lotes (batch)**: Insertar filas en grupos (ej: 5000 a la vez) para que sea más rápido y estable.
- **SQL parametrizado (`?`)**: Forma segura de enviar valores al SQL sin pegarlos como texto (reduce errores y mejora estabilidad).
- **`fast_executemany`**: Opción de `pyodbc` que acelera muchísimo inserciones masivas en SQL Server.

### Nulos en pandas
- **NaT / NA**: Valores nulos especiales de pandas (NaT = fecha nula, NA = dato nulo) que el script convierte a `NULL` en SQL.

### Trazabilidad
- **Trazabilidad (`source_file`)**: Columna extra que guarda el nombre del archivo origen, para poder rastrear de dónde salió cada fila.

---

## Resumen 

Este script es un “puente” que toma archivos `.parquet` de una carpeta, los organiza para que no fallen, y los guarda en SQL Server en una tabla llamada `raw.yellow_trips`, dejando además la huella de qué archivo trajo cada fila.

