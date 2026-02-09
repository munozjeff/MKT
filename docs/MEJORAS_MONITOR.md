# 🔧 Mejoras al Monitor de Mensajes - Depuración

## Problema Reportado

El usuario reportó que:
1. ❌ El monitor nunca detectaba mensajes nuevos
2. ❌ No se enviaban notificaciones al número configurado

## Mejoras Implementadas

### 1. **Logs de Depuración Detallados**

Se agregaron logs en cada paso del proceso para facilitar la depuración:

```
[Monitor] ═══════════════════════════════════════
[Monitor] Iniciando monitoreo de mensajes nuevos
[Monitor] Número de notificaciones: 3217166019
[Monitor] Tiempo máximo: 5s
[Monitor] ═══════════════════════════════════════
[Monitor] Buscando chats no leídos...
[Monitor] Total de elementos 'row' encontrados: 25
[Monitor] Chat no leído detectado: Juan Pérez - 1 mensaje
[Monitor] Total de chats no leídos detectados: 3
[Monitor] Chats actuales: ['Juan Pérez', 'María García', 'Pedro López']
[Monitor] Chats anteriores: []
[Monitor] Primera revisión - Estableciendo línea base con 3 chats
[Monitor] No hay mensajes nuevos para notificar
[Monitor] ═══════════════════════════════════════
[Monitor] Monitoreo completado en 2.35s
[Monitor] ═══════════════════════════════════════
```

### 2. **Selectores CSS Mejorados**

Se agregaron **selectores alternativos** para detectar badges de mensajes no leídos:

```python
# Selector principal
'span[aria-label*="mensaje"][aria-label*="no leído"]'

# Selector alternativo 1
'span[data-icon="unread-count"]'

# Selector alternativo 2
'span.x1c4vz4f.x2lah0s'
```

### 3. **Validación de Formato de Número**

Se agregó validación automática para agregar el `+` si falta:

```python
numero_notif = self.notification_contact
if not numero_notif.startswith('+'):
    numero_notif = '+' + numero_notif
    print(f"[Monitor] Número ajustado a formato internacional: {numero_notif}")
```

**Ejemplo:**
- Entrada: `3217166019`
- Salida: `+3217166019`

### 4. **Logs en Envío de Notificaciones**

Cada paso del envío de notificación ahora tiene logs:

```
[Monitor] 📤 Enviando notificación sobre: Juan Pérez
[Monitor] Número destino: +3217166019
[Monitor] Paso 1/5: Abriendo 'Nuevo chat'...
[Monitor] ✓ 'Nuevo chat' abierto
[Monitor] Paso 2/5: Buscando contacto +3217166019...
[Monitor] ✓ Contacto buscado
[Monitor] Paso 3/5: Verificando existencia del contacto...
[Monitor] ✓ Contacto verificado
[Monitor] Paso 4/5: Abriendo chat...
[Monitor] ✓ Chat abierto
[Monitor] Paso 5/5: Enviando mensaje...
[Monitor] ✓ Notificación enviada correctamente
[Monitor] ✅ Notificación 1 enviada exitosamente
```

### 5. **Mejor Manejo de Errores**

Se agregó `traceback` completo en caso de errores:

```python
except Exception as e:
    print(f"[Monitor] ❌ Error en monitoreo: {e}")
    import traceback
    traceback.print_exc()
```

### 6. **Información de Chats Detectados**

Ahora se muestra información detallada de los chats:

```python
print(f"[Monitor] Chats actuales: {[c['nombre'] for c in chats_actuales]}")
print(f"[Monitor] Chats anteriores: {self.last_chats}")
```

## Cómo Usar las Mejoras

### 1. Ejecutar la Aplicación

```bash
python -m src.main
```

### 2. Configurar el Monitor

En el campo **"Monitor - Número Notif."** puedes usar cualquiera de estos formatos:

✅ `+573217166019` (recomendado)  
✅ `573217166019` (se agregará el + automáticamente)  
✅ `3217166019` (se agregará el +)

### 3. Revisar los Logs

Ahora verás información detallada en la consola:

- **Total de chats encontrados**
- **Chats no leídos detectados**
- **Chats nuevos vs anteriores**
- **Cada paso del envío de notificación**
- **Resultado de cada notificación**

## Diagnóstico de Problemas

### Si no detecta chats no leídos:

Revisa los logs:
```
[Monitor] Total de elementos 'row' encontrados: X
[Monitor] Total de chats no leídos detectados: 0
```

**Posibles causas:**
- Los selectores CSS han cambiado en WhatsApp Web
- No hay chats con mensajes no leídos
- WhatsApp Web no ha cargado completamente

### Si no detecta chats nuevos:

Revisa los logs:
```
[Monitor] Chats actuales: ['Juan', 'María']
[Monitor] Chats anteriores: ['Juan', 'María']
[Monitor] No hay chats nuevos
```

**Explicación:**
- En la **primera revisión**, se establece la línea base (no se notifica)
- En revisiones posteriores, solo se notifican chats que **no estaban antes**

### Si falla el envío de notificación:

Revisa en qué paso falla:
```
[Monitor] Paso 1/5: Abriendo 'Nuevo chat'...
[Monitor] ✗ Error al abrir 'Nuevo chat'
```

**Posibles causas:**
- El número no tiene WhatsApp
- El número está en formato incorrecto
- Problemas de conexión
- WhatsApp Web no responde

## Ejemplo de Ejecución Exitosa

```
[Monitor] ═══════════════════════════════════════
[Monitor] Iniciando monitoreo de mensajes nuevos
[Monitor] Número de notificaciones: 3217166019
[Monitor] Tiempo máximo: 5s
[Monitor] ═══════════════════════════════════════

[Monitor] Buscando chats no leídos...
[Monitor] Total de elementos 'row' encontrados: 25
[Monitor] Chat no leído detectado: Cliente Nuevo - 1 mensaje no leído
[Monitor] Total de chats no leídos detectados: 1

[Monitor] Analizando chats nuevos...
[Monitor] Chats actuales: ['Cliente Nuevo']
[Monitor] Chats anteriores: []
[Monitor] Primera revisión - Estableciendo línea base con 1 chats

[Monitor] ℹ️ No hay mensajes nuevos para notificar

[Monitor] ═══════════════════════════════════════
[Monitor] Monitoreo completado en 1.85s
[Monitor] ═══════════════════════════════════════

--- SEGUNDA EJECUCIÓN (con mensaje nuevo) ---

[Monitor] ═══════════════════════════════════════
[Monitor] Iniciando monitoreo de mensajes nuevos
[Monitor] Número de notificaciones: 3217166019
[Monitor] Tiempo máximo: 5s
[Monitor] ═══════════════════════════════════════

[Monitor] Buscando chats no leídos...
[Monitor] Total de elementos 'row' encontrados: 25
[Monitor] Chat no leído detectado: Cliente Nuevo - 1 mensaje no leído
[Monitor] Chat no leído detectado: Otro Cliente - 1 mensaje no leído
[Monitor] Total de chats no leídos detectados: 2

[Monitor] Analizando chats nuevos...
[Monitor] Chats actuales: ['Cliente Nuevo', 'Otro Cliente']
[Monitor] Chats anteriores: ['Cliente Nuevo']
[Monitor] ¡Chats nuevos detectados!: ['Otro Cliente']

[Monitor] 🆕 Se detectaron 1 chat(s) nuevo(s)

[Monitor] Procesando notificación 1/1...

[Monitor] 📤 Enviando notificación sobre: Otro Cliente
[Monitor] Número destino: +3217166019
[Monitor] Paso 1/5: Abriendo 'Nuevo chat'...
[Monitor] ✓ 'Nuevo chat' abierto
[Monitor] Paso 2/5: Buscando contacto +3217166019...
[Monitor] ✓ Contacto buscado
[Monitor] Paso 3/5: Verificando existencia del contacto...
[Monitor] ✓ Contacto verificado
[Monitor] Paso 4/5: Abriendo chat...
[Monitor] ✓ Chat abierto
[Monitor] Paso 5/5: Enviando mensaje...
[Monitor] ✓ Notificación enviada correctamente
[Monitor] ✅ Notificación 1 enviada exitosamente

[Monitor] ═══════════════════════════════════════
[Monitor] Monitoreo completado en 3.42s
[Monitor] ═══════════════════════════════════════
```

## Próximos Pasos

1. **Ejecuta la aplicación** con las mejoras
2. **Revisa los logs detallados** en la consola
3. **Comparte los logs** si sigues teniendo problemas
4. Los logs te dirán exactamente dónde está fallando el proceso

## Archivos Modificados

- `src/services/whatsapp_monitor_service.py` - Todas las mejoras aplicadas
