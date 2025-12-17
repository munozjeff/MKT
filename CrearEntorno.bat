@echo off
:: Nombre del entorno virtual
set ENV_NAME=venv

:: Crear el entorno virtual
python -m venv %ENV_NAME%

:: Activar el entorno virtual
call %ENV_NAME%\Scripts\activate.bat

:: Instalar bibliotecas
pip install -r requirements.txt

:: Confirmar activación e instalación
echo El entorno virtual %ENV_NAME% ha sido creado y activado.
echo Las bibliotecas selenium y pandas han sido instaladas.
