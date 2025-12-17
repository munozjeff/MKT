@echo off
chcp 65001 > nul
echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║   📱 INSTALADOR - Sistema de Marketing WhatsApp Pro          ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo 🚀 Iniciando instalación automática...
echo.

REM Verificar si Python está instalado
echo [1/5] ⏳ Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado
    echo.
    echo 👉 Por favor instala Python 3.8 o superior desde:
    echo    https://www.python.org/downloads/
    echo.
    echo    ⚠️  IMPORTANTE: Durante la instalación marca la opción
    echo        "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo ✅ Python encontrado
python --version

REM Verificar si Git está instalado
echo.
echo [2/5] ⏳ Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Git no encontrado. Intentando instalar automáticamente...
    
    rem Verificar si existe Winget
    winget --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ No se encontró Winget. Debes instalar Git manualmente.
        echo 👉 Descarga: https://git-scm.com/download/win
        pause
        exit /b 1
    )
    
    echo 📥 Instalando Git via Winget...
    echo Pulsa SI si Windows pide permisos de administrador.
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    
    if errorlevel 1 (
        echo ❌ Error instalando Git.
        pause
        exit /b 1
    )
    
    echo ✅ Git instalado correctamente.
    echo ⚠️  IMPORTANTE: Cierre esta ventana y vuelva a ejecutar install.bat
    echo    para que los cambios surtan efecto.
    pause
    exit /b 0
)
echo ✅ Git encontrado
git --version

REM Ejecutar script de configuración del entorno
echo.
echo [3/5] 📦 Configurando entorno y librerías...
if exist CrearEntorno.bat (
    call CrearEntorno.bat
    if errorlevel 1 (
        echo ❌ ERROR: Falló la configuración del entorno
        pause
        exit /b 1
    )
) else (
    echo ❌ ERROR: No se encontró el archivo CrearEntorno.bat
    echo Asegúrate de estar en la carpeta correcta.
    pause
    exit /b 1
)

REM Crear directorios necesarios
echo.
echo [4/5] 📁 Creando directorios de datos...
if not exist data mkdir data
if not exist informes mkdir informes
if not exist perfiles mkdir perfiles
if not exist logs mkdir logs
echo ✅ Directorios creados

REM Verificar ChromeDriver
echo.
echo ⏳ Verificando ChromeDriver...
if not exist "chromedriver.exe" (
    echo.
    echo ⚠️  IMPORTANTE: ChromeDriver no encontrado
    echo.
    echo 📋 Para usar el sistema necesitas ChromeDriver:
    echo.
    echo 1. Ve a: https://chromedriver.chromium.org/downloads
    echo 2. Descarga la versión que coincida con tu Chrome
    echo 3. Extrae chromedriver.exe en esta carpeta:
    echo    %CD%
    echo.
) else (
    echo ✅ ChromeDriver encontrado
)

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                  ✅ INSTALACIÓN COMPLETADA                    ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 El sistema está listo para usar
echo.
echo 📝 PRÓXIMOS PASOS:
echo.
echo 1. Si no tienes ChromeDriver, descárgalo e instálalo
echo 2. Ejecuta el sistema con: run.bat
echo    o directamente: venv\Scripts\python.exe src\main.py
echo.
echo 📖 Para más información, consulta el README.md
echo.
pause
