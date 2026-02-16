from pathlib import Path
from datetime import datetime
import requests
from tqdm import tqdm

# ====================================
# 1) LEEMOS EL ARCHIVO TXT
# ====================================


def leer_config(ruta_txt: str):
    """
    
    Esta función lee el archivo entrada.txt y saca:
    - BASE (la web donde están los archivos)
    - lista de meses (YYYY-MM)
    """
    
    base = None  #Aquí guardamos la BASE
    periodos= []  #Aquí guardamos los meses (ej:"2024-01")
    
    
    lineas = Path(ruta_txt).read_text(encoding="utf-8").splitlines()
    
    for linea in lineas:
        
        linea = linea.strip()   #Quitamos espacios al inicio/fin
        
        
        if not linea or linea.startswith("#"):
            #Si la linea está vacia o es comentario, la ignoramos
            continue
        
        
        #Si la línea tiene "BASE=..."
        if linea.upper().startswith("BASE="):
            base = linea.split("=",1)[1].strip().rstrip("/")
            continue
        
        #Si no era BASE, entonces asumimos que son meses
        #Puede venir "2024-01;2024-02"
        partes = [p.strip() for p in linea.split(";") if p.strip()]
        for p in partes:
            periodos.append(p)
            
    if base is None:
        raise ValueError("En el txt falta la línea BASE=...")

    if len(periodos) == 0:
        raise ValueError("En el txt no encontré meses (ej: 2024-01)")

    # Quitamos repetidos sin complicarnos mucho
    periodos_sin_repetir = []
    for p in periodos:
        if p not in periodos_sin_repetir:
            periodos_sin_repetir.append(p)

    return base, periodos_sin_repetir

# ==================================
# 2) CONSTRUIMOS LA URL DEL ARCHIVO
# ==================================

def construir_url(base: str, periodo: str):
    """
    Si periodo = "2024-01", construimos:
    https://.../yellow_tripdata_2024-01.parquet
    """
    return f"{base}/yellow_tripdata_{periodo}.parquet"


# ==================================
# 3) ESCRIBIMOS EN EL ARCHIVO DE LOG
# ==================================

def escribir_log(ruta_log: Path, mensaje: str):
    """
    Escribimos una línea en el log (como un diario de lo que pasó).
    """
    ruta_log.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_log, "a", encoding="utf-8") as f:
        f.write(mensaje + "\n")
        
        
# ==================================
# 4) DESCARGAMOS UN ARCHIVO
# ==================================

def descargar(url: str, salida: Path, ruta_log: Path, periodo: str):
    """
    Descarga el archivo de 'url' y lo guarda en 'salida'.
    También registra lo que pasó en el log.
    """
    nombre = salida.name
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Si ya existe, no lo bajamos otra vez
    if salida.exists() and salida.stat().st_size > 0:
        escribir_log(ruta_log, f"[{ahora}] {periodo} | {nombre} | SKIP | Ya existía")
        print(f"Ya existe: {nombre}")
        return

    # Bajamos en modo "stream" (por pedacitos)
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()  # Si hay error (ej 404), aquí explota

            total = int(r.headers.get("content-length", 0))

            # Creamos carpeta si no existe
            salida.parent.mkdir(parents=True, exist_ok=True)

            # Guardamos con barra de progreso
            with open(salida, "wb") as f, tqdm(
                total=total if total > 0 else None,
                unit="B",
                unit_scale=True,
                desc=nombre
            ) as pbar:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

        ahora_ok = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        escribir_log(ruta_log, f"[{ahora_ok}] {periodo} | {nombre} | OK | Descargado")
        print(f"OK: {nombre}")

    except Exception as e:
        ahora_fail = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        escribir_log(ruta_log, f"[{ahora_fail}] {periodo} | {nombre} | FAIL | {e}")
        print(f"FAIL: {nombre} -> {e}")


# =========================
# 5) PROGRAMA PRINCIPAL
# =========================

def main():
    # 1) Archivo que tú editas
    archivo_entrada = "entrada.txt"

    # 2) Carpeta donde se guardan los archivos
    carpeta_salida = Path("data/raw/yellow")

    # 3) Archivo log (el diario)
    archivo_log = Path("logs/log_descargas.txt")

    # Leemos BASE y meses desde el txt
    base, periodos = leer_config(archivo_entrada)

    # Escribimos que empezamos
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    escribir_log(archivo_log, f"\n=== INICIO {inicio} | BASE={base} | N={len(periodos)} ===")

    # Descargamos cada mes
    for periodo in periodos:
        url = construir_url(base, periodo)
        salida = carpeta_salida / f"yellow_tripdata_{periodo}.parquet"
        descargar(url, salida, archivo_log, periodo)

    # Escribimos que terminamos
    fin = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    escribir_log(archivo_log, f"=== FIN {fin} ===\n")


if __name__ == "__main__":
    main()