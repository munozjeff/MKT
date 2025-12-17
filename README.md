# Sistema de Marketing WhatsApp Pro

Versión reestructurada y profesional del sistema de automatización MKT.

## Características Nuevas
- **Arquitectura Modular**: Código organizado y escalable.
- **Gestión de Perfiles**: Soporte para múltiples navegadores concurrentes con persistencia de sesión.
- **Ejecución Paralela**: Posibilidad de lanzar múltiples tareas de envío simultáneas.
- **Interfaz Mejorada**: Gestión separada de contactos, campañas y navegadores.

## Estructura del Proyecto
- `src/`: Código fuente
    - `config/`: Configuraciones
    - `models/`: Modelos de datos
    - `services/`: Lógica de negocio (WhatsApp, Browser, etc.)
    - `ui/`: Interfaz gráfica
    - `utils/`: Utilidades
- `data/`: Datos persistentes (perfiles, campañas, contactos)
- `informes/`: Reportes de envío

## Instalación
1. Asegúrese de tener Python instalado.
2. Instale dependencias: `pip install -r requirements.txt` (o use el entorno virtual existente).

## Uso
Ejecute el archivo `Iniciar_Nuevo_MKT.bat` o corra:
```bash
python src/main.py
```

## Guía Rápida
1. **Navegadores**: Vaya a la pestaña "Navegadores" y cree perfiles (ej: "Ventas", "Soporte"). Puede abrir el navegador manualmente para escanear el QR.
2. **Campañas**: Cree sus mensajes predeterminados en la pestaña "Campañas".
3. **Enviar**:
    - Seleccione un perfil libre.
    - Seleccione una campaña y un archivo Excel.
    - Configure intervalos.
    - Haga clic en "LANZAR TAREA".
    - Puede configurar y lanzar otra tarea con otro perfil mientras la primera se ejecuta.

