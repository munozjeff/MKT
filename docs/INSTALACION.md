# 📥 Guía de Instalación - Primera Vez

Esta guía es para usuarios que instalan el sistema **por primera vez** desde GitHub.

---

## 🎯 Método Recomendado: Instalación Automática (Windows)

### Requisitos Previos

Antes de comenzar, asegúrate de tener:
- ✅ **Windows 10/11**
- ✅ **Google Chrome** instalado
- ✅ **Conexión a Internet**

---

## 📋 Instalación Paso a Paso

### **PASO 1: Descargar el Proyecto**

#### Opción A: Descargar ZIP (Más fácil)

1. Ve a: **https://github.com/munozjeff/MKT**
2. Click en el botón verde **"Code"**
3. Click en **"Download ZIP"**
4. Extrae el archivo ZIP en una carpeta (ej: `C:\MKT`)

#### Opción B: Clonar con Git (Recomendado)

Si tienes Git instalado:

```bash
git clone https://github.com/munozjeff/MKT.git
cd MKT
```

---

### **PASO 2: Instalar Python (si no lo tienes)**

1. **Descarga Python 3.8 o superior:**
   - Ve a: https://www.python.org/downloads/
   - Descarga la última versión para Windows

2. **Durante la instalación:**
   - ✅ **MUY IMPORTANTE:** Marca la casilla **"Add Python to PATH"**
   - Click en "Install Now"

3. **Verificar instalación:**
   - Abre CMD (Símbolo del sistema)
   - Escribe: `python --version`
   - Deberías ver algo como: `Python 3.11.x`

---

### **PASO 3: Ejecutar Instalador Automático**

1. **Abre la carpeta del proyecto** donde lo descargaste

2. **Doble click en:** `install.bat`

3. **El instalador automáticamente:**
   - ✅ Verifica Python y Git (lo instala si falta)
   - ✅ Ejecuta `CrearEntorno.bat`
   - ✅ Instala todas las dependencias
   - ✅ Crea carpetas de datos
   - ✅ Verifica ChromeDriver

4. **Espera** a que termine (1-3 minutos)

---

### **PASO 4: Instalar ChromeDriver**

El instalador te indicará si necesitas ChromeDriver:

1. **Verifica tu versión de Chrome:**
   - Abre Chrome
   - Ve a: `chrome://settings/help`
   - Anota tu versión (ej: 120.0.6099.109)

2. **Descarga ChromeDriver:**
   - Ve a: https://chromedriver.chromium.org/downloads
   - Descarga la versión que coincida con tu Chrome
   - **IMPORTANTE:** Descarga "chromedriver_win32.zip"

3. **Instala ChromeDriver:**
   - Extrae el archivo `chromedriver.exe`
   - Copia `chromedriver.exe` a la carpeta del proyecto (donde está `install.bat`)

---

### **PASO 5: Ejecutar la Aplicación**

1. **Doble click en:** `run.bat`

2. **¡Listo!** La aplicación debería abrirse

---

## 🔧 Instalación Manual (Avanzado)

Si prefieres instalar manualmente:

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear directorios
mkdir data informes perfiles logs

# 5. Descargar ChromeDriver (manual)
# Ver PASO 4 arriba

# 6. Ejecutar
python src/main.py
```

---

## 🌐 Instalación en Linux/Mac

```bash
# 1. Clonar repositorio
git clone https://github.com/munozjeff/MKT.git
cd MKT

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar
source venv/bin/activate

# 4. Instalar
pip install -r requirements.txt

# 5. Crear directorios
mkdir -p data informes perfiles logs

# 6. Instalar ChromeDriver
# Linux:
sudo apt-get install chromium-chromedriver
# Mac:
brew install chromedriver

# 7. Ejecutar
python src/main.py
```

---

## ✅ Verificación de Instalación

Después de instalar, verifica que todo funcione:

### 1. Estructura de Carpetas

Deberías tener:
```
MKT/
├── venv/              ✅ Entorno virtual
├── src/               ✅ Código fuente
├── data/              ✅ (vacía al inicio)
├── informes/          ✅ (vacía al inicio)
├── perfiles/          ✅ (vacía al inicio)
├── chromedriver.exe   ✅ Driver de Chrome
└── run.bat            ✅ Ejecutable
```

### 2. Dependencias Instaladas

Ejecuta en CMD:
```bash
venv\Scripts\activate
pip list
```

Deberías ver: selenium, pandas, openpyxl, Pillow, faker, numpy, requests

### 3. Ejecutar Aplicación

```bash
run.bat
```

La aplicación debería abrir sin errores.

---

## 🆘 Solución de Problemas

### ❌ "Python no encontrado"

**Solución:**
- Reinstala Python marcando **"Add to PATH"**
- O agrega Python manualmente al PATH del sistema

### ❌ "pip no encontrado"

**Solución:**
```bash
python -m ensurepip --upgrade
```

### ❌ "Error instalando dependencias"

**Solución:**
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### ❌ "ChromeDriver no compatible"

**Solución:**
- Verifica tu versión de Chrome: `chrome://settings/help`
- Descarga ChromeDriver de la misma versión exacta
- Reemplaza el archivo chromedriver.exe

### ❌ "Error al ejecutar: ModuleNotFoundError"

**Solución:**
- Asegúrate de activar el entorno virtual primero
```bash
venv\Scripts\activate
python src/main.py
```

---

## 🔄 Actualización del Sistema

Una vez instalado, el sistema se actualiza **automáticamente**:

1. Al abrir la app, verifica si hay actualizaciones
2. Te notifica si hay una versión nueva
3. Click en "Actualizar Ahora"
4. ¡Listo! Se actualiza y reinicia solo

**También puedes** actualizar manualmente con Git:
```bash
git pull origin main
```

---

## 📦 Compartir con Otros Usuarios

Para compartir la aplicación con alguien más:

### Método 1: Enviar Link de GitHub

Simplemente envía:
```
https://github.com/munozjeff/MKT
```

Y comparte este archivo: `docs/INSTALACION.md`

### Método 2: Crear Instalador Portable (Próximamente)

Estamos trabajando en un instalador `.exe` que no requiera Python.

---

## 📞 Soporte

Si tienes problemas durante la instalación:

1. Revisa esta guía completa
2. Consulta la documentación en `docs/`
3. Contacta al desarrollador

---

**¡Bienvenido al Sistema de Marketing WhatsApp Pro!** 🎉
