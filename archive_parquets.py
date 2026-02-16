"""
archive_parquets.py

Objetivo (en español simple):
- Tomar todos los archivos .parquet que estén en:  data\raw\yellow
- Moverlos a:                                  data\raw\yellow-backup
- Dejar vacía (limpia) la carpeta yellow para que el próximo descargue empiece "en limpio".

¿Por qué ayuda?
- Si tu script de carga a SQL vuelve a recorrer los mismos .parquet una y otra vez,
  el proceso se vuelve más lento. Al moverlos a backup, solo procesa lo nuevo.

Cómo usar (ejemplos):
1) Simular sin hacer cambios:
   python archive_parquets.py --dry-run

2) Ejecutar de verdad:
   python archive_parquets.py

3) Cambiar rutas (si un día las mueves):
   python archive_parquets.py --source "data\\raw\\yellow" --backup "data\\raw\\yellow-backup"
"""

from __future__ import annotations

import argparse
import logging
import shutil
from pathlib import Path


# =========================
# CONFIGURACIÓN DE LOGS
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("parquet-archiver")


def safe_move(src_file: Path, dst_dir: Path) -> Path:
    """
    Mueve src_file a dst_dir sin pisar archivos existentes.

    Si en la carpeta destino ya existe un archivo con el mismo nombre,
    se crea uno nuevo con sufijo:  archivo.parquet -> archivo__1.parquet -> archivo__2.parquet, etc.

    Retorna la ruta final donde quedó el archivo.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)

    candidate = dst_dir / src_file.name
    if not candidate.exists():
        shutil.move(str(src_file), str(candidate))
        return candidate

    # Si ya existe, buscamos un nombre libre agregando sufijos
    stem = src_file.stem          # nombre sin extensión
    suffix = src_file.suffix      # ".parquet"
    i = 1
    while True:
        candidate = dst_dir / f"{stem}__{i}{suffix}"
        if not candidate.exists():
            shutil.move(str(src_file), str(candidate))
            return candidate
        i += 1


def archive_parquets(source_dir: Path, backup_dir: Path, dry_run: bool = False) -> int:
    """
    Función principal:
    - Busca archivos .parquet dentro de source_dir
    - Los mueve a backup_dir
    - Deja source_dir vacío de .parquet

    dry_run=True -> NO mueve nada, solo muestra qué haría.

    Retorna un código numérico:
    - 0: todo OK
    - 1: no existe carpeta source
    - 2: error moviendo algún archivo
    """
    source_dir = source_dir.resolve()
    backup_dir = backup_dir.resolve()

    logger.info(f"Carpeta origen (yellow): {source_dir}")
    logger.info(f"Carpeta backup:         {backup_dir}")
    logger.info(f"Modo simulación:        {dry_run}")

    if not source_dir.exists():
        logger.error("La carpeta origen NO existe. Revisa la ruta.")
        return 1

    # Seguridad básica: evita que alguien pase accidentalmente una ruta peligrosa como "C:\"
    # (No es infalible, pero ayuda a prevenir errores graves.)
    if len(source_dir.parts) < 3:
        logger.error("Ruta de origen demasiado corta/riesgosa. No continuaré por seguridad.")
        return 1

    parquet_files = sorted(source_dir.glob("*.parquet"))

    if not parquet_files:
        logger.info("No encontré archivos .parquet para mover. Nada que hacer.")
        return 0

    logger.info(f"Encontré {len(parquet_files)} archivo(s) .parquet para archivar.")

    moved_count = 0

    for f in parquet_files:
        try:
            if dry_run:
                logger.info(f"[DRY-RUN] Movería: {f.name}  ->  {backup_dir}")
            else:
                final_path = safe_move(f, backup_dir)
                logger.info(f"Movido: {f.name}  ->  {final_path.name}")
            moved_count += 1
        except Exception as e:
            logger.exception(f"Error moviendo {f.name}: {e}")
            return 2

    logger.info(f"Listo. Procesé {moved_count} archivo(s).")
    logger.info("La carpeta yellow queda limpia (sin los .parquet movidos).")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mueve .parquet de yellow a yellow-backup y limpia yellow.")
    parser.add_argument("--source", default=r"data\raw\yellow", help="Ruta de la carpeta origen (por defecto: data\\raw\\yellow)")
    parser.add_argument("--backup", default=r"data\raw\yellow-backup", help="Ruta de la carpeta backup (por defecto: data\\raw\\yellow-backup)")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin mover nada (solo muestra lo que haría).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = Path(args.source)
    backup_dir = Path(args.backup)
    return archive_parquets(source_dir, backup_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
