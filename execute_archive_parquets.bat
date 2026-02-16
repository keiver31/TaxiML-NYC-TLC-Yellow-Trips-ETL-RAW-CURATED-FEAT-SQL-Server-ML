@echo off
REM ============================================
REM archive_parquets.bat
REM Ejecuta el script que mueve los .parquet
REM de data\raw\yellow a data\raw\yellow-backup
REM ============================================

REM (Opcional) Ir a la carpeta donde está este .bat
cd /d "%~dp0"

REM Ejecutar el script (ejecución real)
python archive_parquets.py

REM Pausa para que veas el resultado antes de que se cierre la ventana
pause
