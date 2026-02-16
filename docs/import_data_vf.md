# IMPORTACIÓN DE DATOS DE RECORRIDOS (YELLOW TRIPDATA) - PYTHON

Archivo: `import_data_vf.py`


Importante: 
- El script import_data.py,  **descarga archivos `.parquet` por mes** desde una URL base (BASE) y los guarda en **`data/raw/yellow/`**.
- El script **lee la configuración desde `entrada.txt`** (BASE + meses en formato `YYYY-MM`).
- El script genera un **log** en **`logs/log_descargas.txt`** con el resultado de cada descarga (OK / FAIL / SKIP).
- Para que las rutas funcionen como están en el código, se recomienda **ejecutar el script desde la carpeta base del proyecto** (donde está `entrada.txt`).

Siguiendo el orden correcto, se pueden realizar los ajustes correspondientes para la configuración y ejecución del script.

## Manual Paso a Paso(Ejecución Script de Descarga)

#### 1. Prerrequisitos

- Tener instalado **Python 3.x**.
- Instalar dependencias requeridas:
- `requests` (descargas HTTP)
- `tqdm` (barra de progreso)

Comando sugerido:
- `pip install requests tqdm`

#### 2. Ubicación sugerida del script

- Guardar el archivo Python en una ruta como:
- `scripts/Download_Yellow_Tripdata.py`

> Nota: Si lo guardas en otro lugar, no pasa nada, pero asegúrate de ejecutarlo desde la raíz del proyecto o ajustar rutas.

#### 3. Crear/Configurar el archivo `entrada.txt`

- En la raíz del proyecto, crear el archivo `entrada.txt`.
- El archivo debe contener:
- Una línea con `BASE=...` (URL donde están los `.parquet`)
- Uno o más periodos `YYYY-MM`
- Puedes poner varios meses en una misma línea separados por `;`
- Las líneas vacías o que empiezan por `#` se ignoran (comentarios)

Ejemplo de `entrada.txt`:

BASE=https://TU_URL_BASE_SIN_SLASH_FINAL
2024-01;2024-02;2024-03
#### También puedes escribir meses en varias líneas:
2024-04
2024-05

#### 4. Estructura de salida (carpetas y archivos)

- El script crea automáticamente (si no existen):
- Carpeta de datos: `data/raw/yellow/`
- Carpeta de logs: `logs/`

Archivos generados:
- Descargas: `data/raw/yellow/yellow_tripdata_YYYY-MM.parquet`
- Log: `logs/log_descargas.txt`

#### 5. Ejecución del script

- Desde la raíz del proyecto, ejecutar:

- `python scripts/Download_Yellow_Tripdata.py`

(ajusta la ruta si el script se llama distinto o está en otra carpeta)

#### 6. Validación del proceso

- Validar que existan archivos en:
- `data/raw/yellow/`

Ejemplo de nombres esperados:
- `yellow_tripdata_2024-01.parquet`
- `yellow_tripdata_2024-02.parquet`

- Validar el log en:
- `logs/log_descargas.txt`

Ejemplo de registros esperados (puede variar el timestamp):
[2026-02-10 10:00:00] 2024-01 | yellow_tripdata_2024-01.parquet | OK | Descargado
[2026-02-10 10:00:30] 2024-02 | yellow_tripdata_2024-02.parquet | FAIL | 404 Client Error: Not Found ...
[2026-02-10 10:01:00] 2024-03 | yellow_tripdata_2024-03.parquet | SKIP | Ya existía

#### 7. Consideraciones importantes del comportamiento del script

- Si un archivo **ya existe** y tiene tamaño > 0, el script:
- **NO lo vuelve a descargar**
- Registra `SKIP` en el log

- Si la descarga falla (timeout, 404, etc.):
- Registra `FAIL` con el error en el log
- Continúa con el siguiente mes

- Las descargas se hacen por “pedacitos” (stream) y se muestra una barra de progreso.

