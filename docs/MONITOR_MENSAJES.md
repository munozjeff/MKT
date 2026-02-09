# Monitor de Mensajes Nuevos - Sistema de Marketing WhatsApp

## Descripción

Se ha implementado un sistema de monitoreo de mensajes nuevos que se integra con el sistema de marketing por WhatsApp. Esta funcionalidad permite detectar y notificar sobre mensajes entrantes durante las campañas de envío.

## Características

### 1. **Monitoreo Automático**
- El monitor se ejecuta **antes de cada envío** de mensaje
- Detecta chats con mensajes no leídos
- Identifica mensajes nuevos comparando con la última revisión
- Envía notificaciones al número configurado

### 2. **Integración con Tiempos de Envío**
- El tiempo usado en el monitoreo se **resta del intervalo** configurado
- Mantiene el timing total de la campaña sin alteraciones
- Tiempo máximo de monitoreo: 5 segundos o la mitad del intervalo (lo que sea menor)

### 3. **Configuración Flexible**
- **Campo en UI**: "Monitor - Número Notif."
- **Formato**: +573001234567 (código de país + número)
- **Deshabilitación**: Dejar el campo vacío desactiva el monitor

### 4. **Compatibilidad**
- Funciona en **todos los modos de envío**:
  - Individual
  - Distribuido
  - Rotación

## Uso

### Configurar el Monitor

1. En la ventana de configuración de envío, localiza el campo **"Monitor - Número Notif."**
2. Ingresa el número de WhatsApp donde deseas recibir las notificaciones (ej: +573001234567)
3. Si dejas el campo vacío, el monitor estará deshabilitado

### Formato de Notificaciones

Las notificaciones incluyen:
```
🔔 NUEVO MENSAJE DETECTADO

Nombre: [Nombre del contacto]
Hora: [Hora del mensaje]
Preview: [Vista previa del mensaje]
Detectado: [Timestamp de detección]
```

### Ejemplo de Configuración

```
Modo de Envío: Individual
Perfil: MiPerfil
Archivo Excel: contactos.xlsx
Tipo de Mensaje: Texto
Tipo de Campaña: Predeterminada
Campaña: Campaña de Ventas
Intervalo (seg): 50
Pausa cada N mensajes: 10
Monitor - Número Notif.: +573001234567  ← Aquí configuras el número
```

## Funcionamiento Técnico

### Flujo de Monitoreo

1. **Antes de cada envío**:
   - Se ejecuta el monitoreo (máx 5 segundos)
   - Se detectan chats no leídos
   - Se comparan con la lista anterior
   - Se envían notificaciones de mensajes nuevos

2. **Ajuste de Timing**:
   - Tiempo de monitoreo: 2.5 segundos
   - Intervalo configurado: 50 segundos
   - Intervalo ajustado: 50 - 2.5 = 47.5 segundos
   - **Total**: 50 segundos (como se configuró)

### Archivos Modificados

1. **`src/services/whatsapp_monitor_service.py`** (NUEVO)
   - Servicio de monitoreo adaptado para el sistema

2. **`src/ui/components/send_view.py`**
   - Agregado campo de entrada para número de notificaciones
   - Pasa el número a la configuración de los runners

3. **`src/services/automation_runner.py`**
   - Inicializa el monitor después del login
   - Ejecuta monitoreo antes de cada envío
   - Ajusta intervalos de espera

4. **`src/services/distributed_runner.py`**
   - Cada worker tiene su propio monitor
   - Monitoreo independiente por perfil

5. **`src/services/rotation_runner.py`**
   - Monitoreo integrado en rotación de perfiles
   - Respeta cooldowns y límites

## Ventajas

✅ **No interrumpe el flujo**: El monitoreo se ejecuta en el tiempo de espera  
✅ **Notificaciones inmediatas**: Recibes alertas de mensajes importantes  
✅ **Flexible**: Puedes activarlo/desactivarlo según necesites  
✅ **Compatible**: Funciona en todos los modos de envío  
✅ **Eficiente**: Tiempo máximo limitado para no afectar la campaña  

## Notas Importantes

- El monitor solo detecta mensajes **nuevos** (que no estaban en la revisión anterior)
- En la primera revisión, no se envían notificaciones (se establece la línea base)
- Los emojis problemáticos se eliminan automáticamente de las notificaciones
- El número de notificaciones debe incluir el código de país (ej: +57 para Colombia)

## Ejemplo de Salida en Consola

```
📱 Monitor de mensajes activado - Notificaciones a: +573001234567
[1/100] Enviando a +573009876543...
⏱ Tiempo de monitoreo: 1.2s
🆕 Se detectaron 1 chat(s) nuevo(s)
📤 Enviando notificación sobre: Juan Pérez
  ✓ Notificación enviada correctamente
[2/100] Enviando a +573009876544...
```

## Soporte

Para cualquier duda o problema con el monitor de mensajes, verifica:
1. El número de notificaciones está en formato correcto (+código_país + número)
2. El número tiene WhatsApp activo
3. El perfil de WhatsApp está correctamente logueado
