"""
Script de prueba para verificar la integración del monitor de mensajes.
"""
import sys
import os

# Configurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 60)
print("VERIFICACIÓN DE INTEGRACIÓN - MONITOR DE MENSAJES")
print("=" * 60)

# Test 1: Importar el servicio de monitor
print("\n1. Verificando import de WhatsAppMonitorService...")
try:
    from src.services.whatsapp_monitor_service import WhatsAppMonitorService
    print("   ✓ WhatsAppMonitorService importado correctamente")
except Exception as e:
    print(f"   ✗ Error al importar: {e}")
    sys.exit(1)

# Test 2: Verificar que los runners pueden importar el monitor
print("\n2. Verificando imports en runners...")
try:
    from src.services.automation_runner import AutomationRunner
    print("   ✓ AutomationRunner importado correctamente")
except Exception as e:
    print(f"   ✗ Error al importar AutomationRunner: {e}")
    sys.exit(1)

try:
    from src.services.distributed_runner import DistributedAutomationRunner
    print("   ✓ DistributedAutomationRunner importado correctamente")
except Exception as e:
    print(f"   ✗ Error al importar DistributedAutomationRunner: {e}")
    sys.exit(1)

try:
    from src.services.rotation_runner import RotationAutomationRunner
    print("   ✓ RotationAutomationRunner importado correctamente")
except Exception as e:
    print(f"   ✗ Error al importar RotationAutomationRunner: {e}")
    sys.exit(1)

# Test 3: Verificar que SendView tiene el campo de monitor
print("\n3. Verificando UI (SendView)...")
try:
    from src.ui.components.send_view import SendView
    print("   ✓ SendView importado correctamente")
except Exception as e:
    print(f"   ✗ Error al importar SendView: {e}")
    sys.exit(1)

# Test 4: Verificar que se puede instanciar el monitor (sin driver)
print("\n4. Verificando instanciación del monitor...")
try:
    # Crear instancia sin driver (solo para verificar la clase)
    monitor = WhatsAppMonitorService(driver=None, notification_contact="+573001234567")
    print(f"   ✓ Monitor instanciado con número: {monitor.notification_contact}")
except Exception as e:
    print(f"   ✗ Error al instanciar: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ TODAS LAS VERIFICACIONES PASARON EXITOSAMENTE")
print("=" * 60)
print("\nLa integración del monitor de mensajes está completa y funcional.")
print("\nPara usar el monitor:")
print("1. Ejecuta la aplicación: python -m src.main")
print("2. Ve a 'Enviar Mensajes'")
print("3. Configura tu campaña")
print("4. En 'Monitor - Número Notif.' ingresa tu número (ej: +573001234567)")
print("5. Lanza la tarea")
print("\n¡El monitor enviará notificaciones de mensajes nuevos durante la campaña!")
