# TEST DE CONEXIÓN Y CARGA INICIAL A SQL SERVER (PYODBC)

Archivo: `db_test.py`


Importante:
- Este script sirve como **prueba rápida** para validar que:
  - Tu **SQL Server** responde.
  - El **usuario/contraseña** funcionan.
  - El **driver ODBC** está instalado y el string de conexión está correcto.
- Aunque en este snippet no se cargan `.parquet`, este test es el **paso previo obligatorio** antes de intentar importar los archivos `.parquet` a SQL Server.

Siguiendo el orden correcto, se pueden realizar los ajustes correspondientes para la configuración y ejecución del script.

---

## Manual Paso a Paso (Test de Conexión a SQL Server)

### 1. Prerrequisitos

- Tener instalado **Python 3.x**
- Instalar dependencia:
- `pyodbc`

Comando sugerido:
- `pip install pyodbc`

- Tener instalado el driver:
- **ODBC Driver 17 for SQL Server** (o uno compatible, si cambias el nombre en el connection string)

> Nota: Si el driver no existe con ese nombre en tu máquina, el script fallará al conectar.

---

### 2. Ubicación sugerida del script

- Guardar el archivo Python en una ruta como:
- `scripts/Test_Conexion_SQLServer.py`

> Nota: Puedes ubicarlo donde quieras, pero es buena práctica centralizar scripts en `scripts/`.

---

### 3. Configuración del script (variables)

Dentro del código debes ajustar:

- `server`: nombre del servidor / instancia  
  Ejemplo:
  - `DESKTOP-5VDFT83\SQLEXPRESS`

- `database`: nombre de la base de datos  
  Ejemplo:
  - `TaxiML`

- `username` / `password`: credenciales del usuario SQL  
  Ejemplo:
  - `user_daemon`
  - `PASSWORD`

> Importante:
> - Este método usa autenticación SQL (usuario/contraseña).
> - Si tu SQL Server está con autenticación Windows, este script se debe adaptar.

---

### 4. Ejecución del test

Desde la raíz del proyecto (o donde estés trabajando), ejecutar:

- `python scripts/Test_Conexion_SQLServer.py`

---

### 5. Resultado esperado

- Si todo está bien, el script imprime:

(1,)

Esto significa:
- Conectó correctamente
- Ejecutó `SELECT 1;`
- Recibió respuesta del motor

---

### 6. Errores comunes y qué revisar

#### Error: “Data source name not found…”
- Causa típica: No tienes instalado el driver ODBC 17 o el nombre no coincide.
- Acción: validar en tu equipo qué drivers ODBC existen y ajustar:
- `DRIVER={ODBC Driver 17 for SQL Server};`

#### Error: “Login failed for user…”
- Causa típica: usuario/clave incorrectos o el usuario no tiene permisos.
- Acción: validar credenciales y permisos en SQL Server.

#### Error: “Cannot open database…”
- Causa típica: la BD no existe, está mal escrita o el usuario no tiene acceso.
- Acción: validar que exista `TaxiML` y que el usuario tenga permisos.

#### Error: “Named Pipes Provider… / Error 40…”
- Causa típica: instancia incorrecta, SQL Server apagado, o configuración de red.
- Acción: validar que el servicio esté arriba y que `SQLEXPRESS` sea la instancia correcta.

---

## Siguiente paso

Cuando este test funcione (te dé `(1,)`), ya puedes pasar al script que:
- Lee los `.parquet`
- Crea tablas/estructuras destino
- Inserta/carga los registros en SQL Server (por lotes o usando un método masivo)

