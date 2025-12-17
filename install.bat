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

REM ==========================================
REM PASO 2.5: CLONAR O ACTUALIZAR REPOSITORIO
REM ==========================================
echo.
echo [3/5] ☁️ Obteniendo código fuente...

REM Verificar si estamos DENTRO del proyecto (si existe main.py o src)
if exist src\main.py (
    echo   Estamos dentro de la carpeta del proyecto.
    echo   Actualizando código...
    git pull
) else (
    REM Verificar si la carpeta MKT ya existe en el directorio actual
    if exist MKT\src\main.py (
        echo   Carpeta MKT encontrada. Entrando...
        cd MKT
        git pull
    ) else (
        echo   Clonando repositorio desde GitHub...
        git clone https://github.com/munozjeff/MKT.git
        
        if errorlevel 1 (
            echo ❌ ERROR: No se pudo clonar el repositorio.
            echo Verifique su conexión a internet.
            pause
            exit /b 1
        )
        
        echo   Entrando en carpeta MKT...
        cd MKT
    )
)

REM ==========================================
REM PASO 3: CONFIGURAR ENTORNO
REM ==========================================
echo.
echo [4/5] 📦 Configurando entorno y librerías...

if exist CrearEntorno.bat (
    call CrearEntorno.bat
    if errorlevel 1 (
        echo ❌ ERROR: Falló la configuración del entorno
        pause
        exit /b 1
    )
) else (
    echo ❌ ERROR CRÍTICO: No se encontró CrearEntorno.bat
    echo El repositorio no se descargó correctamente.
    pause
    exit /b 1
)

REM ==========================================
REM PASO 4: DIRECTORIOS Y EXTRAS
REM ==========================================
echo.
echo [5/5] 📁 Verificando directorios y drivers...

if not exist data mkdir data
if not exist informes mkdir informes
if not exist perfiles mkdir perfiles
if not exist logs mkdir logs
echo ✅ Directorios verificados

REM Verificar ChromeDriver
if not exist "chromedriver.exe" (
    echo.
    echo ⚠️  Falta ChromeDriver
    echo.
    echo Por favor descarga ChromeDriver que coincida con tu Chrome
    echo y colócalo en esta carpeta:
    echo %CD%
    echo.
    echo Descarga: https://chromedriver.chromium.org/downloads
) else (
    echo ✅ ChromeDriver encontrado
)

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                  ✅ INSTALACIÓN COMPLETADA                    ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo 🎉 Todo listo!
echo.
echo 👉 Para iniciar:
echo    Ejecuta el archivo: run.bat
echo    (Está dentro de la carpeta MKT si acabas de instalar)
echo.
pause
