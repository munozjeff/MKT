@echo off
echo Configurando entorno virtual...
cd /d "%~dp0venv\Scripts"
call activate.bat
echo Entorno virtual activado.

echo Ejecutando la aplicación...
python "%~dp0MKT.py"
echo Aplicación ejecutada.

pause
