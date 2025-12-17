# 📱 Sistema de Marketing WhatsApp Pro

Sistema automatizado para envío masivo de mensajes por WhatsApp Web con gestión de campañas, contactos y perfiles de navegador.

## ✨ Características Principales

### 🎯 Gestión de Campañas
- ✅ Campañas predeterminadas y personalizadas
- ✅ Soporte para variables dinámicas en mensajes
- ✅ Fallback automático si faltan variables
- ✅ Adjuntar imágenes a campañas
- ✅ Plantillas de mensajes anti-spam

### 👥 Gestión de Contactos
- ✅ Importación desde Excel
- ✅ Contactos alternativos (reintento automático)
- ✅ Validación de números
- ✅ Detección automática de WhatsApp

### 🌐 Navegadores
- ✅ Múltiples perfiles de navegador
- ✅ Gestión de sesiones de WhatsApp Web
- ✅ Modo individual y distribuido
- ✅ Bloqueo de perfiles en uso

### 📊 Envío de Mensajes
- ✅ Modo individual o distribuido
- ✅ Intervalos configurables entre mensajes
- ✅ Pausas programadas
- ✅ Modo anti-spam
- ✅ Envío de facturas (PDFs)
- ✅ Reintento con contactos alternativos
- ✅ Informes automáticos de envío

### 🔄 Sistema de Actualización Automática
- ✅ Verificación automática al inicio
- ✅ Descarga e instalación automática
- ✅ Protección total de datos de usuario
- ✅ Backup y rollback automático
- ✅ Actualización sin pérdida de datos

## 🚀 Instalación

### Requisitos
- Python 3.8 o superior
- Google Chrome
- ChromeDriver

### Pasos

1. **Clonar el repositorio:**
```bash
git clone https://github.com/TU_USUARIO/MKT.git
cd MKT
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Ejecutar la aplicación:**
```bash
python src/main.py
```

## 📖 Uso

### 1. Configurar Navegadores
- Crear perfiles de navegador
- Iniciar sesión en WhatsApp Web en cada perfil

### 2. Importar Contactos
- Subir archivo Excel con columnas: `Celular`, `Nombre`, `Contacto_1`, `Contacto_2`, etc.
- El sistema detectará automáticamente las variables

### 3. Crear Campañas
- Crear campañas con variables: `[nombre]`, `[empresa]`, etc.
- Opcionalmente agregar imágenes

### 4. Enviar Mensajes
- Seleccionar tipo de campaña
- Elegir perfil(es) de navegador
- Configurar intervalos y pausas
- ¡Iniciar envío!

## 🔒 Protección de Datos

El sistema protege completamente tus datos locales:
- `data/`, `datos/` - Datos de aplicación
- `reports/`, `informes/` - Informes
- `profiles/`, `perfiles/` - Perfiles de navegador
- Bases de datos locales

**Nunca se suben a GitHub ni se sobrescriben en actualizaciones.**

## 🛠️ Tecnologías

- **Python 3.x** - Lenguaje principal
- **Tkinter** - Interfaz gráfica
- **Selenium** - Automatización de navegador
- **Pandas** - Procesamiento de datos
- **Requests** - Sistema de actualización

## 📝 Estructura del Proyecto

```
MKT/
├── src/
│   ├── config/          # Configuración
│   ├── models/          # Modelos de datos
│   ├── services/        # Lógica de negocio
│   ├── ui/              # Interfaz de usuario
│   ├── utils/           # Utilidades
│   └── main.py          # Punto de entrada
├── data/                # Datos (no versionado)
├── reports/             # Informes (no versionado)
├── profiles/            # Perfiles navegador (no versionado)
├── docs/                # Documentación
├── version.json         # Información de versión
├── requirements.txt     # Dependencias
└── README.md           # Este archivo
```

## 🔄 Actualizaciones

El sistema incluye actualización automática:
- Verifica nuevas versiones al inicio
- Descarga e instala automáticamente
- Reinicia la aplicación
- **100% seguro** - No toca datos de usuario

Para más información: [docs/ACTUALIZACIONES.md](docs/ACTUALIZACIONES.md)

## 📄 Licencia

Este proyecto es privado y de uso personal.

## 👨‍💻 Autor

**Eivar**

---

**⚠️ Importante**: Este sistema está diseñado para uso ético y legal. Respeta las políticas de WhatsApp y las leyes de tu país.
