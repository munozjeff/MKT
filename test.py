import time
import sys
import os

# Asegurar que podemos importar los módulos de src
# Add the current directory to sys.path so we can import from src
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from src.services.whatsapp_service import WhatsAppService
from src.services.whatsapp_monitor_service import WhatsAppMonitorService

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("=== TEST INDEPENDIENTE DE WHATSAPP ===")
    print("Iniciando servicio...")
    
    # 1. Inicializar Servicio
    wa_service = WhatsAppService()
    
    # Usar un perfil temporal para pruebas o el default
    # Si se pasa None, usa un perfil temporal nueva cada vez (requiere escaneo)
    # Si quieres persistencia en pruebas, usa un path fijo
    profile_path = os.path.join(os.getcwd(), "data", "perfiles", "TEST_PROFILE")
    if not os.path.exists(profile_path):
        os.makedirs(profile_path)
        
    print(f"Usando perfil de prueba en: {profile_path}")
    
    if not wa_service.initialize_driver(profile_path):
        print("Error al iniciar el driver. Saliendo.")
        return

    print("\nEsperando inicio de sesión...")
    print("Por favor, escanea el código QR si es necesario.")
    
    # Esperar hasta que esté logueado
    while not wa_service.is_logged_in():
        time.sleep(2)
        
    print("\n✅ Sesión iniciada correctamente!")
    
    monitor = None
    
    while True:
        clear_screen()
        print("=== MENÚ DE PRUEBAS ===")
        print("1. Enviar Mensaje de Prueba")
        print("2. Activar Modo Lectura (Monitor)")
        print("3. Salir")
        
        opcion = input("\nSeleccione una opción: ")
        
        if opcion == "1":
            phone = input("Ingrese número (con código de país, ej 573001234567): ")
            msg = input("Ingrese mensaje: ")
            
            print(f"Enviando a {phone}...")
            
            wa_service.click_new_chat()
            if wa_service.search_contact(phone):
                exists, has_wa, _ = wa_service.check_contact_exists()
                if has_wa:
                    wa_service.open_chat()
                    wa_service.send_text_message(msg)
                    wa_service.send_message_simple()
                    wa_service.close_chat()
                    print("✅ Mensaje enviado.")
                else:
                    print("❌ El número no tiene WhatsApp.")
                    wa_service.go_back()
            else:
                print("❌ No se pudo encontrar el contacto.")
                
            input("\nPresione Enter para continuar...")
            
        elif opcion == "2":
            contact_notif = input("Ingrese número/nombre para recibir notificaciones: ")
            if not contact_notif:
                print("Debe ingresar un contacto para probar el flujo completo.")
                time.sleep(1)
                continue
            
            auto_reply_msg = input("Ingrese mensaje de Auto-Respuesta (o Enter para desactivar): ")
            if not auto_reply_msg:
                auto_reply_msg = None
                
            monitor = WhatsAppMonitorService(wa_service.driver, contact_notif, "TEST_PROFILE")
            
            print("\n=== MODO LECTURA ACTIVO ===")
            print(f"Notificando a: {contact_notif}")
            if auto_reply_msg:
                print(f"Auto-Respuesta: ACTIVADA ('{auto_reply_msg}')")
            print("Presione Ctrl+C para detener y volver al menú.")
            
            try:
                while True:
                    # Ejecutar el flujo completo: Detectar -> Marcar Leído -> (Auto-Responder) -> Notificar
                    monitor.monitorear_y_notificar(wa_service, max_time=10, auto_reply_text=auto_reply_msg)
                    
                    # Pequeña pausa entre ciclos
                    print("Esperando 5 segundos...")
                    time.sleep(5)
            except KeyboardInterrupt:
                print("\nModo lectura detenido.")
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nModo lectura detenido.")
                time.sleep(1)
                
        elif opcion == "3":
            print("Cerrando navegador...")
            wa_service.close()
            break
        else:
            print("Opción inválida.")
            time.sleep(1)

if __name__ == "__main__":
    main()
