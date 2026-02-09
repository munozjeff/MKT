"""
Servicio de monitoreo de mensajes nuevos en WhatsApp.
Adaptado para integrarse con el sistema de marketing.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime


class WhatsAppMonitorService:
    """Servicio para monitorear mensajes nuevos en WhatsApp y enviar notificaciones."""
    
    def __init__(self, driver, notification_contact=None, profile_name="Desconocido"):
        """
        Inicializa el servicio de monitoreo.
        
        Args:
            driver: Instancia de Selenium WebDriver ya inicializada
            notification_contact: Número de teléfono para enviar notificaciones (formato: +573001234567)
            profile_name: Nombre del perfil de navegador que se está usando
        """
        self.driver = driver
        self.notification_contact = notification_contact
        self.profile_name = profile_name
        self.wait = WebDriverWait(self.driver, 10)
        self.last_chats = []  # Para detectar nuevos chats

    # ... (rest of the file until enviar_notificacion)

    def enviar_notificacion(self, chat_info, whatsapp_service):
        """
        Envía una notificación al contacto predefinido usando whatsapp_service.
        
        Args:
            chat_info: Diccionario con información del chat
            whatsapp_service: Instancia de WhatsAppService para enviar el mensaje
        """
        if not self.notification_contact:
            print("[Monitor] No hay número de notificación configurado")
            return False
        
        try:
            # Asegurar que el número tenga el formato correcto
            numero_notif = self.notification_contact
            if not numero_notif.startswith('+'):
                numero_notif = '+' + numero_notif
                print(f"[Monitor] Número ajustado a formato internacional: {numero_notif}")
            
            # Formatear el mensaje de notificación (formato exacto del monitor funcional)
            mensaje = f"""Perfil: {self.profile_name}
Nombre: {chat_info['nombre']}
Hora: {chat_info['hora']}
Preview: {chat_info['preview']}
Detectado: {chat_info['timestamp']}"""

            print(f"[Monitor] 📤 Enviando notificación sobre: {chat_info['nombre']}")
            print(f"[Monitor] Número destino: {numero_notif}")
            
            # PASO 1: Click en "Nuevo chat"
            print("[Monitor] Paso 1/5: Abriendo 'Nuevo chat'...")
            # La función click_new_chat no retorna valor (void), así que no verificamos resultado
            whatsapp_service.click_new_chat()
            print("[Monitor] ✓ 'Nuevo chat' abierto (asumiendo éxito)")
            
            # PASO 2: Buscar el contacto
            print(f"[Monitor] Paso 2/5: Buscando contacto {numero_notif}...")
            if not whatsapp_service.search_contact(numero_notif):
                print("[Monitor] ✗ Error al buscar contacto")
                whatsapp_service.go_back()
                return False
            print("[Monitor] ✓ Contacto buscado")
            
            # PASO 3: Verificar si tiene WhatsApp
            print("[Monitor] Paso 3/5: Verificando WhatsApp...")
            exists, has_wa, err = whatsapp_service.check_contact_exists()
            if not exists or not has_wa:
                print(f"[Monitor] ✗ Contacto no válido: {err}")
                whatsapp_service.go_back()
                return False
            print("[Monitor] ✓ Contacto validado")
                
            # PASO 4: Abrir chat
            print("[Monitor] Paso 4/5: Abriendo chat...")
            if not whatsapp_service.open_chat():
                print("[Monitor] ✗ Error al abrir chat")
                whatsapp_service.go_back()
                return False
            print("[Monitor] ✓ Chat abierto")
            
            # PASO 5: Enviar mensaje
            print("[Monitor] Paso 5/5: Enviando mensaje...")
            
            # Limpiar mensaje de caracteres problemáticos
            mensaje_limpio = self.limpiar_mensaje(mensaje)
            
            if whatsapp_service.send_text_message(mensaje_limpio):
                print("[Monitor] ✓ Notificación enviada correctamente")
                
                # Esperar confirmación de envío
                time.sleep(2)
                
                # Cerrar el chat y volver a la lista
                whatsapp_service.close_chat()
                
                # Pausa adicional para asegurar que WhatsApp esté listo
                time.sleep(2)
                
                return True
            else:
                print("[Monitor] ✗ Error al enviar texto")
                whatsapp_service.close_chat()
                return False
                
        except Exception as e:
            print(f"[Monitor] ❌ Error en proceso de notificación: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def obtener_chats_no_leidos(self):
        """Detecta y obtiene información de los chats con mensajes no leídos."""
        try:
            # Esperar a que cargue la lista de chats (timing igual al monitor funcional)
            time.sleep(2)
            
            # Buscar todos los chats con badge de mensajes no leídos
            chats_no_leidos = self.driver.find_elements(
                By.CSS_SELECTOR,
                'div[role="row"]'
            )
            
            print(f"[Monitor] Total de elementos 'row' encontrados: {len(chats_no_leidos)}")
            
            chats_detectados = []
            
            for idx, chat in enumerate(chats_no_leidos):
                try:
                    # Buscar el badge de mensajes no leídos dentro del chat
                    badge = chat.find_element(
                        By.CSS_SELECTOR,
                        'span[aria-label*="mensaje"][aria-label*="no leído"]'
                    )
                    
                    if badge:
                        # Extraer información del chat
                        try:
                            # Nombre del chat
                            nombre_elem = chat.find_element(
                                By.CSS_SELECTOR,
                                'span[dir="auto"][title]'
                            )
                            nombre = nombre_elem.get_attribute('title')
                            
                            # Número de mensajes no leídos
                            num_mensajes = badge.get_attribute('aria-label')
                            
                            # Vista previa del último mensaje
                            try:
                                preview_elem = chat.find_element(
                                    By.CSS_SELECTOR,
                                    'span.x78zum5.x1cy8zhl[title]'
                                )
                                preview = preview_elem.get_attribute('title')
                                
                                if not preview:
                                    preview = preview_elem.text
                            except:
                                try:
                                    preview_elem = chat.find_element(
                                        By.CSS_SELECTOR,
                                        'span.x1iyjqo2.x6ikm8r.x10wlt62.x1n2onr6[dir="ltr"]'
                                    )
                                    preview = preview_elem.text
                                except:
                                    preview = "No disponible"
                            
                            # Hora del último mensaje
                            try:
                                hora_elem = chat.find_element(
                                    By.CSS_SELECTOR,
                                    'span.x140p0ai.x1gufx9m.x1s928wv'
                                )
                                hora = hora_elem.text
                            except:
                                hora = "No disponible"
                            
                            chat_info = {
                                'nombre': nombre,
                                'mensajes_no_leidos': num_mensajes,
                                'preview': preview[:50] + '...' if len(preview) > 50 else preview,
                                'hora': hora,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'elemento': chat  # Guardar referencia al elemento del chat
                            }
                            
                            chats_detectados.append(chat_info)
                            print(f"[Monitor] Chat no leído detectado: {nombre} - {num_mensajes}")
                            
                        except Exception as e:
                            # Si no se puede extraer toda la info, continuar
                            print(f"[Monitor] Error al extraer info del chat {idx}: {e}")
                            continue
                            
                except NoSuchElementException:
                    # Este chat no tiene mensajes no leídos, continuar
                    continue
            
            print(f"[Monitor] Total de chats no leídos detectados: {len(chats_detectados)}")
            return chats_detectados
            
        except Exception as e:
            print(f"[Monitor] Error al obtener chats: {e}")
            return []
    
    def detectar_nuevos_chats(self, chats_actuales):
        """
        Detecta qué chats son nuevos comparando con la última revisión.
        
        Args:
            chats_actuales: Lista de chats detectados actualmente
            
        Returns:
            Lista de chats nuevos
        """
        print(f"[Monitor] Chats actuales: {[c['nombre'] for c in chats_actuales]}")
        print(f"[Monitor] Chats anteriores: {self.last_chats}")
        
        # Si es la primera vez, TODOS son nuevos y SÍ los notificamos
        if not self.last_chats:
            self.last_chats = [chat['nombre'] for chat in chats_actuales]
            print(f"[Monitor] Primera revisión - Notificando todos los {len(chats_actuales)} chats no leídos encontrados")
            return chats_actuales  # Devolver TODOS los chats para notificar
        
        # Detectar chats que no estaban en la lista anterior
        nombres_anteriores = set(self.last_chats)
        chats_nuevos = [chat for chat in chats_actuales if chat['nombre'] not in nombres_anteriores]
        
        if chats_nuevos:
            print(f"[Monitor] ¡Chats nuevos detectados!: {[c['nombre'] for c in chats_nuevos]}")
        else:
            print(f"[Monitor] No hay chats nuevos")
        
        # Actualizar la lista
        self.last_chats = [chat['nombre'] for chat in chats_actuales]
        
        return chats_nuevos
    
    def marcar_chat_como_leido(self, chat_info):
        """
        Hace clic sobre el chat para abrirlo y marcarlo como leído.
        
        Args:
            chat_info: Diccionario con información del chat (incluye 'elemento')
        
        Returns:
            True si se pudo abrir el chat, False en caso contrario
        """
        try:
            elemento_chat = chat_info.get('elemento')
            if not elemento_chat:
                print(f"[Monitor] ⚠ No se encontró elemento del chat para marcar como leído")
                return False
            
            print(f"[Monitor] Haciendo clic en chat '{chat_info['nombre']}' para marcarlo como leído...")
            
            # Hacer clic en el elemento del chat
            elemento_chat.click()
            time.sleep(1)  # Esperar que se abra el chat
            
            print(f"[Monitor] ✓ Chat '{chat_info['nombre']}' abierto y marcado como leído")
            
            # Cerrar el chat (presionar ESC)
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"[Monitor] Error al marcar chat como leído: {e}")
            return False
    
    def limpiar_mensaje(self, mensaje):
        """
        Limpia caracteres especiales del mensaje que pueden causar problemas en Selenium.
        
        Args:
            mensaje: Texto del mensaje a limpiar
            
        Returns:
            Mensaje limpio y seguro para Selenium
        """
        import re
        
        # Eliminar emojis específicos que causan problemas
        mensaje_limpio = re.sub(r'[\U00010000-\U0010ffff]', '', mensaje)
        
        return mensaje_limpio.strip()
    
    def enviar_notificacion(self, chat_info, whatsapp_service):
        """
        Envía una notificación al contacto predefinido usando whatsapp_service.
        
        Args:
            chat_info: Diccionario con información del chat
            whatsapp_service: Instancia de WhatsAppService para enviar el mensaje
        """
        if not self.notification_contact:
            print("[Monitor] No hay número de notificación configurado")
            return False
        
        try:
            # Asegurar que el número tenga el formato correcto
            numero_notif = self.notification_contact
            if not numero_notif.startswith('+'):
                numero_notif = '+' + numero_notif
                print(f"[Monitor] Número ajustado a formato internacional: {numero_notif}")
            
            # Formatear el mensaje de notificación (formato exacto del monitor funcional)
            mensaje = f"""Perfil: {self.profile_name}
Nombre: {chat_info['nombre']}
Hora: {chat_info['hora']}
Preview: {chat_info['preview']}
Detectado: {chat_info['timestamp']}"""
            
            # Limpiar caracteres especiales del mensaje
            mensaje_limpio = self.limpiar_mensaje(mensaje)
            
            print(f"\n[Monitor] 📤 Enviando notificación sobre: {chat_info['nombre']}")
            print(f"[Monitor] Número destino: {numero_notif}")
            
            # PASO 1: Click en "Nuevo chat"
            print("[Monitor] Paso 1/5: Abriendo 'Nuevo chat'...")
            # La función click_new_chat no retorna valor (void), así que no verificamos resultado
            whatsapp_service.click_new_chat()
            print("[Monitor] ✓ 'Nuevo chat' abierto (asumiendo éxito)")
            
            # PASO 2: Buscar el contacto
            print(f"[Monitor] Paso 2/5: Buscando contacto {numero_notif}...")
            if not whatsapp_service.search_contact(numero_notif):
                print("[Monitor] ✗ Error al buscar contacto")
                whatsapp_service.go_back()
                return False
            print("[Monitor] ✓ Contacto buscado")
            
            # PASO 3: Verificar que el contacto existe
            print("[Monitor] Paso 3/5: Verificando existencia del contacto...")
            found, has_whatsapp, error_msg = whatsapp_service.check_contact_exists()
            
            if not found or not has_whatsapp:
                print(f"[Monitor] ✗ El contacto no fue encontrado o no tiene WhatsApp: {error_msg}")
                whatsapp_service.go_back()
                return False
            print("[Monitor] ✓ Contacto verificado")
            
            # PASO 4: Abrir el chat
            print("[Monitor] Paso 4/5: Abriendo chat...")
            if not whatsapp_service.open_chat():
                print("[Monitor] ✗ Error al abrir el chat")
                whatsapp_service.go_back()
                return False
            print("[Monitor] ✓ Chat abierto")
            
            # PASO 5: Enviar el mensaje
            print("[Monitor] Paso 5/5: Enviando mensaje...")
            if not whatsapp_service.send_text_message(mensaje_limpio):
                print("[Monitor] ✗ Error al enviar mensaje de texto")
                return False
            
            # Enviar el mensaje (presionar Enter)
            if not whatsapp_service.send_message_simple():
                print("[Monitor] ✗ Error al enviar mensaje")
                return False
            
            print("[Monitor] ✓ Notificación enviada correctamente")
            
            # Esperar confirmación de envío
            time.sleep(2)
            
            # Cerrar el chat y volver a la lista
            whatsapp_service.close_chat()
            
            # Pausa adicional para asegurar que WhatsApp esté listo
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"[Monitor] ❌ Error al enviar notificación: {e}")
            import traceback
            traceback.print_exc()
            # Intentar volver a la lista principal
            try:
                whatsapp_service.go_back()
            except:
                pass
            return False
    
    def monitorear_y_notificar(self, whatsapp_service, max_time=5):
        """
        Monitorea mensajes nuevos y envía notificaciones si los hay.
        Esta función está diseñada para ser llamada antes de cada envío.
        
        Args:
            whatsapp_service: Instancia de WhatsAppService
            max_time: Tiempo máximo en segundos para el monitoreo (default: 5)
            
        Returns:
            Tiempo usado en el monitoreo (en segundos)
        """
        if not self.notification_contact:
            print("[Monitor] Monitor deshabilitado (sin número de notificación)")
            return 0  # Monitor deshabilitado
        
        print(f"\n[Monitor] ═══════════════════════════════════════")
        print(f"[Monitor] Iniciando monitoreo de mensajes nuevos")
        print(f"[Monitor] Número de notificaciones: {self.notification_contact}")
        print(f"[Monitor] Tiempo máximo: {max_time}s")
        print(f"[Monitor] ═══════════════════════════════════════")
        
        start_time = time.time()
        
        try:
            # Obtener chats no leídos
            print("[Monitor] Buscando chats no leídos...")
            chats = self.obtener_chats_no_leidos()
            
            # Detectar nuevos chats
            print("[Monitor] Analizando chats nuevos...")
            chats_nuevos = self.detectar_nuevos_chats(chats)
            
            if chats_nuevos:
                print(f"\n[Monitor] 🆕 Se detectaron {len(chats_nuevos)} chat(s) nuevo(s)")
                
                for idx, chat in enumerate(chats_nuevos, 1):
                    # Verificar si aún tenemos tiempo
                    elapsed = time.time() - start_time
                    if elapsed >= max_time:
                        print(f"[Monitor] ⏱ Tiempo de monitoreo agotado, omitiendo notificaciones restantes")
                        break
                    
                    print(f"\n[Monitor] Procesando notificación {idx}/{len(chats_nuevos)}...")
                    
                    # PASO 1: Marcar el chat como leído haciendo clic sobre él
                    if not self.marcar_chat_como_leido(chat):
                        print(f"[Monitor] ⚠ No se pudo marcar como leído, continuando con notificación...")
                    
                    # PASO 2: Enviar notificación
                    resultado = self.enviar_notificacion(chat, whatsapp_service)
                    if resultado:
                        print(f"[Monitor] ✅ Notificación {idx} enviada exitosamente")
                    else:
                        print(f"[Monitor] ❌ Falló notificación {idx}")
            else:
                print("[Monitor] ℹ️ No hay mensajes nuevos para notificar")
            
        except Exception as e:
            print(f"[Monitor] ❌ Error en monitoreo: {e}")
            import traceback
            traceback.print_exc()
        
        # Retornar el tiempo usado
        elapsed_time = time.time() - start_time
        print(f"\n[Monitor] ═══════════════════════════════════════")
        print(f"[Monitor] Monitoreo completado en {elapsed_time:.2f}s")
        print(f"[Monitor] ═══════════════════════════════════════\n")
        return elapsed_time

