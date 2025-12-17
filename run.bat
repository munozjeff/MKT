@echo off
chcp 65001 > nul
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║   📱 Sistema de Marketing WhatsApp Pro                       ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Verificar si el entorno virtual existe
if not exist venv (
    echo ❌ ERROR: Entorno virtual no encontrado
    echo.
    echo 👉 Ejecuta primero: install.bat
    echo.
    pause
    exit /b 1
)

REM Activar entorno virtual y ejecutar
echo 🚀 Iniciando aplicación...
echo.
call venv\Scripts\activate.bat
python src\main.py

REM Si hay error, pausar para ver el mensaje
if errorlevel 1 (
    echo.
    echo ❌ La aplicación terminó con errores
    echo.
    pause
)
