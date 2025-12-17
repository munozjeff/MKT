# 🔄 Sistema de Actualización Automática

## ⚠️ PROTECCIÓN DE DATOS DE USUARIO - 100% GARANTIZADA

**¡IMPORTANTE!** El sistema de actualización está diseñado para **NUNCA** tocar tus datos de usuario. Los siguientes directorios están **COMPLETAMENTE PROTEGIDOS**:

### 🔒 Directorios Protegidos (NUNCA se sobrescriben):
- ✅ `data/`, `datos/` - Datos de aplicación
- ✅ `reports/`, `informes/` - Informes generados
- ✅ `profiles/`, `perfiles/` - Perfiles de navegador
- ✅ `venv/` - Entorno virtual Python
- ✅ `logs/`, `*.log` - Archivos de registro
- ✅ `*.db`, `*.sqlite` - Bases de datos
- ✅ `.git/` - Control de versiones local

### 🛡️ Protección a Tres Niveles:
1. **Validación previa**: Verifica cada archivo/directorio antes de tocarlo
2. **Doble verificación**: Comprueba si el destino está protegido antes de sobrescribir
3. **Backup + Rollback**: Crea backup antes de actualizar y restaura si falla

> **Resultado**: Durante la actualización **SOLO** se actualizan los archivos de código fuente (.py, configuración, etc.). Todos tus datos permanecen intactos.

---

## 📋 Descripción

Tu aplicación ahora cuenta con un sistema completo de actualización automática que:
- ✅ Verifica actualizaciones al iniciar la app
- ✅ Permite buscar actualizaciones manualmente
- ✅ Descarga e instala automáticamente
- ✅ Crea backups antes de actualizar
- ✅ Reinicia la aplicación después de actualizar

---

## 🚀 Configuración Inicial

### 1. Editar `version.json`

Actualiza el archivo `version.json` en la raíz del proyecto con tus URLs reales de GitHub:

```json
{
    "version": "1.0.0",
    "build": "20251217",
    "release_date": "2025-12-17",
    "update_url": "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json",
    "download_url": "https://github.com/TU_USUARIO/TU_REPO/archive/refs/heads/main.zip"
}
```

**Reemplaza:**
- `TU_USUARIO` → Tu nombre de usuario de GitHub
- `TU_REPO` → El nombre de tu repositorio

---

### 2. Subir a GitHub

1. **Inicializar repositorio** (si no lo has hecho):
```bash
git init
git add .
git commit -m "Sistema de actualización implementado"
```

2. **Crear repositorio en GitHub**:
   - Ve a https://github.com/new
   - Crea un repositorio (público o privado)
   - Copia la URL del repositorio

3. **Conectar y subir**:
```bash
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

---

### 3. Publicar Nueva Versión

Cuando quieras lanzar una actualización:

1. **Actualiza `version.json`** con la nueva versión:
```json
{
    "version": "1.1.0",  ← INCREMENTAR AQUÍ
    "build": "20251218",
    "release_date": "2025-12-18",
    "release_notes": "- Nueva característica X\n- Corrección Y\n- Mejora Z",
    "update_url": "https://raw.githubusercontent.com/TU_USUARIO/TU_REPO/main/version.json",
    "download_url": "https://github.com/TU_USUARIO/TU_REPO/archive/refs/heads/main.zip"
}
```

2. **Commit y push**:
```bash
git add .
git commit -m "Versión 1.1.0 - [Describe los cambios]"
git push origin main
```

3. **¡Listo!** Los usuarios con la versión anterior recibirán la notificación de actualización.

---

## 🎯 Cómo Funciona

### Para el Usuario:

1. **Al abrir la app**:
   - Después de 2 segundos, verifica si hay actualizaciones
   - Si hay una nueva versión, muestra un diálogo elegante
   - El usuario puede actualizar ahora o más tarde

2. **Actualización Manual**:
   - Click en "Buscar Actualizaciones" (abajo del menú)
   - Verifica inmediatamente si hay nuevas versiones

3. **Proceso de Actualización**:
   - Descarga la nueva versión (con barra de progreso)
   - Crea backup automático de la versión actual
   - Instala la nueva versión
   - Reinicia la aplicación automáticamente

### Para el Desarrollador:

El sistema es **totalmente automático**. Solo necesitas:
1. Incrementar el número de versión en `version.json`
2. Hacer commit y push a GitHub
3. Los usuarios se actualizarán automáticamente

---

## 📁 Archivos del Sistema

```
MKT/
├── version.json                          # Configuración de versión
├── src/
│   ├── services/
│   │   └── update_service.py            # Lógica de actualización
│   └── ui/
│       ├── app.py                       # Integración en app principal
│       └── components/
│           └── update_dialog.py         # UI de actualización
```

---

## 🔒 Seguridad

El sistema incluye:
- ✅ **Backups automáticos** antes de actualizar
- ✅ **Rollback** si falla la instalación
- ✅ **Preservación de datos** (no se tocan carpetas `data`, `profiles`, `reports`)
- ✅ **Verificación de integridad** del archivo descargado

---

## 🛠️ Personalización

### Cambiar Frecuencia de Verificación

En `app.py`, línea ~30:
```python
self.after(2000, self.check_for_updates_silent)  # 2000ms = 2 segundos
```

### Desactivar Verificación Automática

Comenta la línea anterior en `app.py`.

### Agregar Notas de Versión

En `version.json`, agrega:
```json
{
    "version": "1.1.0",
    "release_notes": "- Nueva funcionalidad XYZ\n- Corrección de bug ABC"
}
```

Se mostrarán en el diálogo de actualización.

---

## 🐛 Solución de Problemas

### "No se puede verificar actualizaciones"
- ✅ Verifica tu conexión a Internet
- ✅ Asegúrate de que las URLs en `version.json` sean correctas
- ✅ El repositorio debe ser público (o el token debe tener permisos)

### "Error descargando actualización"
- ✅ Verifica que el repositorio esté accesible
- ✅ La URL de descarga debe apuntar a `/archive/refs/heads/main.zip`

### "Error instalando actualización"
- ✅ Cierra otros procesos que puedan estar usando archivos
- ✅ Verifica permisos de escritura en el directorio

---

## 📦 Distribución con PyInstaller

Si empaquetas la app con PyInstaller, el sistema de actualización:
- ✅ Detecta automáticamente si está empaquetada
- ✅ Reinicia el `.exe` correctamente
- ✅ Funciona igual que en modo desarrollo

---

## 🎉 ¡Todo Listo!

Tu sistema de actualización está completo y funcionando. Solo necesitas:
1. Configurar tus URLs de GitHub
2. Subir el código
3. ¡Los usuarios se actualizarán automáticamente!

---

## 📝 Ejemplo de Flujo Completo

```bash
# 1. Hacer cambios en el código
git add src/algún_archivo.py

# 2. Actualizar versión
# Editar version.json: "1.0.0" → "1.1.0"

# 3. Commit y push
git commit -m "v1.1.0 - Nueva funcionalidad"
git push origin main

# 4. ¡Los usuarios recibirán la actualización!
```

¿Necesitas ayuda con algo más? 🚀
