"""
Ejecutor de automatización de envíos.
Encapsula la lógica del bucle de envío para una tarea específica.
"""
import time
import random
import threading
from datetime import datetime
from .whatsapp_service import WhatsAppService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables
from ..models.campaign import Campaign

class AutomationRunner:
    """Ejecuta una tarea de envío de mensajes en un hilo separado."""
    
    def __init__(self, browser_profile, config, phone_numbers, user_data=None, contact_data=None, campaign=None, fallback_campaign=None, progress_callback=None, completion_callback=None):
        self.profile = browser_profile
        self.config = config
        self.phone_numbers = phone_numbers
        self.user_data = user_data or {}
        self.contact_data = contact_data or {}
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign  # Nueva: campaña de respaldo
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        
        self.stop_event = threading.Event()
        self.whatsapp_service = WhatsAppService()
        self.report_service = ReportService()
        
    def start(self):
        """Inicia la ejecución en un hilo."""
        thread = threading.Thread(target=self._run)
        thread.daemon = True
        thread.start()
        
    def stop(self):
        """Detiene la ejecución."""
        self.stop_event.set()
        
    def _run(self):
        """Lógica principal de ejecución loop."""
        try:
            # 1. Inicializar navegador
            if self.progress_callback:
                self.progress_callback(0, len(self.phone_numbers), "Iniciando navegador...")
                
            if not self.whatsapp_service.initialize_driver(self.profile.path):
                raise Exception("No se pudo iniciar el navegador")
            
            # 2. Esperar login
            if self.progress_callback:
                self.progress_callback(0, len(self.phone_numbers), "Esperando inicio de sesión...")
                
            # Loop simple para esperar login (el usuario debe escanear QR si no está logueado)
            # En la versión original había un messagebox, aquí asumimos que el usuario lo ve en la UI principal
            # o que verificamos el login periódicamente.
            # Para simplificar, esperamos un tiempo o checkeamos en loop
            
            max_wait = 300 # 5 min max para login inicial
            start_wait = time.time()
            while not self.stop_event.is_set():
                if self.whatsapp_service.is_logged_in():
                    break
                if time.time() - start_wait > max_wait:
                    raise Exception("Tiempo de espera de inicio de sesión agotado")
                time.sleep(2)
                
            if self.stop_event.is_set():
                return
                
            # 3. Bucle de envío
            total = len(self.phone_numbers)
            pause_after = int(self.config.get("pause", 0))
            interval = int(self.config.get("interval", 20))
            
            for index, phone in enumerate(self.phone_numbers):
                if self.stop_event.is_set():
                    break
                    
                self.progress_callback(index, total, f"Enviando a {phone}...")
                
                # Construir lista de números a intentar (principal + contactos)
                phone_list = [phone]
                contacts = self.contact_data.get(phone, {})
                if contacts:
                    # Filtrar contactos válidos (no None, no NaN)
                    import numpy as np
                    valid_contacts = [v for v in contacts.values() if v is not None and not (isinstance(v, float) and np.isnan(v))]
                    phone_list.extend(valid_contacts)
                
                # Intentar enviar a cada número en la lista hasta que uno tenga éxito
                sent_successfully = False
                
                for attempt_index, target_phone in enumerate(phone_list):
                    if self.stop_event.is_set():
                        break
                        
                    # --- Lógica de mensaje ---
                    message_text = ""
                    image_path = ""
                    
                    # Determinar mensaje según configuración
                    msg_type = self.config.get("message_type")
                    
                    try:
                        if msg_type == "Anti Spam":
                            # Lógica anti spam (intervalos aleatorios)
                            interval = random.randint(30, max(31, int(self.config.get("interval", 60))))
                            
                        # Obtener texto
                        if self.config.get("campaign_type") == "Default":
                            message_text = generate_random_message()
                        elif self.campaign:
                            # Reemplazo de variables
                            raw_msg = self.campaign.message
                            if phone in self.user_data:
                                # Generar mensaje dinámico con fallback
                                fallback_msg = self.fallback_campaign.message if self.fallback_campaign else self.campaign.message
                                message_text = replace_variables(raw_msg, self.user_data.get(phone, {}), fallback_msg)
                            else:
                                 message_text = self.campaign.message
                            
                            # CORRECCIÓN: Usar atributo 'image' no 'image_path'
                            if self.campaign.image:
                                 image_path = self.campaign.image
                        
                        # Tipo Facturas (override imagen)
                        if msg_type == "Facturas":
                            import os
                            folder = self.config.get("facturas_folder")
                            pdf_path = f"{folder}/{phone}.pdf" # Simplificado, usar file_utils real
                            if os.path.exists(pdf_path):
                                # Enviar solo PDF con mensaje fijo
                                self.whatsapp_service.attach_file(pdf_path)
                                self.whatsapp_service.send_attached_file()
                                message_text = "Hola, adjunto tu factura." 
                                image_path = None # Evitar doble envío
                            # Mensaje puede ser fijo o de campaña
                        
                        # --- Envío ---
                        self.whatsapp_service.click_new_chat()
                        
                        if not self.whatsapp_service.search_contact(str(target_phone)):
                            # Si no es el último intento, continuar con el siguiente
                            if attempt_index < len(phone_list) - 1:
                                self.progress_callback(index, total, f"{phone}: Intento {attempt_index+1} fallido, probando contacto alternativo...")
                                continue
                            else:
                                # Era el último intento, reportar fallo
                                self.report_service.add_entry(phone, "No encontrado / Error búsqueda")
                                break
                            
                        exists, has_wa, err = self.whatsapp_service.check_contact_exists()
                        if not has_wa:
                            self.whatsapp_service.go_back() # Importante volver
                            # Si no es el último intento, continuar con el siguiente
                            if attempt_index < len(phone_list) - 1:
                                self.progress_callback(index, total, f"{phone}: Sin WhatsApp en intento {attempt_index+1}, probando contacto alternativo...")
                                continue
                            else:
                                # Era el último intento, reportar fallo
                                self.report_service.add_entry(phone, "Sin WhatsApp (Todos los contactos)")
                                break
                            
                        self.whatsapp_service.open_chat()
                        
                        # Flujo de Envío Diferenciado
                        import os
                        from selenium.webdriver.common.keys import Keys
                        if image_path and os.path.exists(image_path):
                            # 1. Adjuntar imagen
                            if self.whatsapp_service.attach_file(image_path):
                                # 2. Si hay texto, enviarlo como comentario (caption)
                                if message_text:
                                    # Al adjuntar, el foco suele ir al campo de comentario
                                    for line in message_text.split('\n'):
                                        self.whatsapp_service.driver.switch_to.active_element.send_keys(line)
                                        self.whatsapp_service.driver.switch_to.active_element.send_keys(Keys.SHIFT + Keys.ENTER)
                                
                                # 3. Enviar todo (Imagen + Texto)
                                self.whatsapp_service.send_attached_file()
                            else:
                                # Fallback si falla adjuntar: enviar solo texto
                                if message_text:
                                    self.whatsapp_service.send_text_message(message_text)
                                    self.whatsapp_service.send_message_simple()
                        else:
                            # Flujo Solo Texto
                            if message_text:
                                self.whatsapp_service.send_text_message(message_text)
                                self.whatsapp_service.send_message_simple()
                        
                        # Enviar (si solo texto y no se envió con enter, la funcion send_text_message ya envía enter si es config simple)
                        # En la implementación de whatsapp_service.send_text_message usé SHIFT+ENTER, falta el ENTER final o clic enviar.
                        # Vamos a corregir send_text_message para que envíe o agregar un metodo send_current
                        self.whatsapp_service.send_message_simple()
                        
                        status_msg = "Enviado"
                        if attempt_index > 0:
                            status_msg = f"Enviado al contacto {attempt_index+1}"
                        self.report_service.add_entry(phone, status_msg)
                        sent_successfully = True
                        
                        self.whatsapp_service.close_chat()
                        break  # Salir del bucle de intentos si fue exitoso
                        
                    except Exception as e:
                        print(f"Error procesando {target_phone} (intento {attempt_index+1}): {e}")
                        # Si no es el último intento, continuar con el siguiente
                        if attempt_index < len(phone_list) - 1:
                            continue
                        else:
                            # Era el último intento, reportar error
                            self.report_service.add_entry(phone, f"Error: {str(e)}")
                        # Intentar recuperar estado
                        self.whatsapp_service.driver.refresh()
                        time.sleep(5)
                
                # Pausas
                if index < total - 1:
                    time.sleep(interval)
                    if pause_after > 0 and (index + 1) % pause_after == 0:
                        self.progress_callback(index + 1, total, "Pausa programada...")
                        time.sleep(60) # Pausa fija de lote
            
        except Exception as e:
            print(f"Error fatal en Runner: {e}")
            if self.progress_callback:
                self.progress_callback(0, 0, f"Error: {e}")
        finally:
            self.whatsapp_service.close()
            # Guardar reporte
            report_path = self.report_service.save_report()
            
            if self.completion_callback:
                self.completion_callback(report_path)
