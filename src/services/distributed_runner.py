"""
Servicio para la ejecución distribuida de envíos masivos utilizando múltiples perfiles.
"""
import threading
import queue
import time
import random
import os
from concurrent.futures import ThreadPoolExecutor
from .whatsapp_service import WhatsAppService
from .whatsapp_monitor_service import WhatsAppMonitorService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables
from ..models.campaign import Campaign
from ..utils.file_utils import verify_pdf_file
from .human_simulator import HumanSimulator, RateLimiter

class DistributedAutomationRunner:
    """Clase para coordinar el envío distribuido entre múltiples navegadores."""
    
    def __init__(self, browser_profiles, config, phone_numbers, user_data, contact_data, campaign=None, fallback_campaign=None, progress_callback=None, completion_callback=None):
        self.profiles = browser_profiles
        self.config = config
        self.phone_list = phone_numbers
        self.user_data = user_data
        self.contact_data = contact_data
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign  # Nueva: campaña de respaldo
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        
        # Servicios compartidos
        self.report_service = ReportService()
        self.phone_queue = queue.Queue()
        for phone in phone_numbers:
            self.phone_queue.put(phone)
            
        # Control de ejecución
        self.stop_event = threading.Event()
        self.total_messages = len(phone_numbers)
        self.processed_count = 0
        self.count_lock = threading.Lock()
        
        # Lista de instancias de servicios activos (para cleanup)
        self.active_services = []
        self.active_services_lock = threading.Lock()

        # Round-robin compartido entre todos los workers
        self.rr_state = {"idx": 0, "lock": threading.Lock()}
        
    def start(self):
        """Inicia la ejecución distribuida en un hilo maestro."""
        master_thread = threading.Thread(target=self._master_run, daemon=True)
        master_thread.start()
        
    def stop(self):
        """Detiene la ejecución gracilesmente."""
        self.stop_event.set()
        
    def _master_run(self):
        """Hilo principal que coordina los workers."""
        workers = []
        
        # Iniciar un worker por cada perfil
        for profile in self.profiles:
            t = threading.Thread(target=self._worker_run, args=(profile,), daemon=True)
            workers.append(t)
            t.start()
            # Pequeña pausa entre inicios para no saturar CPU al lanzar browsers
            time.sleep(2)
            
        # Esperar a que terminen todos
        for t in workers:
            t.join()
            
        # Generar reporte final
        report_path = self.report_service.save_report(filename_prefix="Informe_Distribuido")
        
        if self.completion_callback:
            self.completion_callback(report_path)

    def _worker_run(self, profile):
        """Lógica de cada worker individual con su propio navegador."""
        service = WhatsAppService()
        monitor_service = None
        
        with self.active_services_lock:
            self.active_services.append(service)
            
        try:
            # 1. Inicializar Navegador
            if not service.initialize_driver(profile.path):
                print(f"[{profile.name}] Falló al iniciar driver")
                return
                
            # 2. Verificar Login / Detectar QR de bloqueo
            print(f"[{profile.name}] Verificando sesión...")
            if not self._wait_for_login(service, profile):
                print(f"[{profile.name}] Login fallido o QR detectado — worker omitido.")
                return

            print(f"[{profile.name}] Listo para enviar.")

            # ── Simulador Humano: configurar por worker ──────────────────────────
            hs_cfg = self.config.get("human_sim")
            sim = None
            rate_limiter = None
            if hs_cfg:
                sim = HumanSimulator(service.driver, hs_cfg)
                sim.inyectar_fingerprints()
                rate_limiter = RateLimiter(
                    int(hs_cfg.get("msgs_per_window", 7)),
                    int(hs_cfg.get("window_minutes", 10))
                )
                sim.calentar_sesion()

            monitor_targets = self.config.get("monitor_targets") or []
            monitor_backup  = self.config.get("monitor_backup", "")
            if not monitor_targets:
                legacy = self.config.get("monitor_group", "")
                if legacy:
                    monitor_targets = [legacy]
            if monitor_targets or monitor_backup:
                monitor_service = WhatsAppMonitorService(
                    driver=service.driver,
                    notification_targets=monitor_targets,
                    notification_backup=monitor_backup or None,
                    profile_name=profile.name
                )
                print(f"[{profile.name}] 📱 Monitor activado — 🎯 Destinos: {monitor_targets} | 🆘 Respaldo: '{monitor_backup or '—'}'")
            
            # 3. Procesar cola
            while not self.phone_queue.empty() and not self.stop_event.is_set():
                try:
                    current_phone = self.phone_queue.get_nowait()
                except queue.Empty:
                    break

                # Horario activo (Simulador Humano)
                if sim:
                    sim.esperar_si_fuera_horario()
                if self.stop_event.is_set():
                    break

                # Rate Limiter (Simulador Humano)
                if sim and rate_limiter:
                    espera = rate_limiter.tiempo_hasta_siguiente()
                    if espera > 0:
                        t0 = time.time()
                        while time.time() - t0 < espera:
                            if self.stop_event.is_set():
                                break
                            restante = espera - (time.time() - t0)
                            sim.scroll_idle(min(restante, 4))
                if self.stop_event.is_set():
                    break

                # MONITOREAR MENSAJES NUEVOS ANTES DE CADA ENVIO
                monitor_time = 0
                if monitor_service:
                    try:
                        base_interval = int(self.config.get("interval", 20))
                        max_monitor_time = min(30, base_interval // 2)
                        auto_reply_text = self.config.get("auto_reply_text")
                        monitor_time = monitor_service.monitorear_y_notificar(
                            service,
                            max_time=max_monitor_time,
                            auto_reply_text=auto_reply_text,
                            rr_state=self.rr_state
                        )
                        if monitor_time > 0:
                            print(f"[{profile.name}] Tiempo de monitoreo: {monitor_time:.1f}s")
                    except Exception as e:
                        print(f"[{profile.name}] Error en monitoreo: {e}")

                self._process_single_message(service, current_phone, profile.name, sim)

                # Registrar envio en rate limiter
                if rate_limiter:
                    rate_limiter.registrar_envio()

                # Pausa larga si corresponde (Simulador Humano)
                if sim:
                    sim.pausa_larga_si_toca()

                # Pausa entre mensajes
                if not self.stop_event.is_set():
                    base_interval = int(self.config.get("interval", 20))
                    adjusted_interval = max(1, base_interval - int(monitor_time))
                    if sim:
                        sleep_time = random.uniform(adjusted_interval * 0.7, adjusted_interval * 1.5)
                        t0 = time.time()
                        while time.time() - t0 < sleep_time:
                            if self.stop_event.is_set():
                                break
                            restante = sleep_time - (time.time() - t0)
                            sim.scroll_idle(min(restante, 3))
                    else:
                        sleep_time = random.uniform(adjusted_interval * 0.8, adjusted_interval * 1.2)
                        time.sleep(sleep_time)
                    
        except Exception as e:
            print(f"[{profile.name}] Error crítico en worker: {e}")
        finally:
            service.close()
            with self.active_services_lock:
                if service in self.active_services:
                    self.active_services.remove(service)

    def _wait_for_login(self, service, profile) -> bool:
        """
        Espera hasta que el usuario inicie sesión.
        En el contexto de ENVÍO: si detecta QR inmediatamente, marca el perfil
        como BLOQUEADO y aborta este worker.
        """
        # Dar tiempo a que WhatsApp Web cargue antes de verificar
        time.sleep(4)

        # --- DETECCIÓN INMEDIATA DE QR (Perfil Bloqueado en contexto de Envío) ---
        if service.is_qr_visible():
            print(f"[{profile.name}] ⛔ QR detectado al inicio → marcando BLOQUEADO y descartando.")
            try:
                if "BLOQUEADO" not in profile.tags:
                    profile.tags.append("BLOQUEADO")
                    profile.save_metadata()
                    print(f"[{profile.name}] ✅ Etiqueta BLOQUEADO guardada.")
            except Exception as e:
                print(f"[{profile.name}] ❌ Error guardando etiqueta BLOQUEADO: {e}")
            return False

        # Sin QR: esperar login normal (~56s restantes)
        for _ in range(56):
            if self.stop_event.is_set(): return False
            if service.is_logged_in(): return True
            time.sleep(1)
        return False

    def _process_single_message(self, service, phone, profile_name, sim=None):
        """Procesa un solo mensaje usando el servicio dado."""
        status = "Fallido"
        
        # Construir lista de números a intentar (principal + contactos)
        phone_list = [phone]
        contacts = self.contact_data.get(phone, {})
        if contacts:
            # Filtrar contactos válidos (no None, no NaN)
            import numpy as np
            valid_contacts = [v for v in contacts.values() if v is not None and not (isinstance(v, float) and np.isnan(v))]
            phone_list.extend(valid_contacts)
        
        # Intentar con cada número hasta que uno tenga éxito
        for attempt_index, target_phone in enumerate(phone_list):
            try:
                # 1. Clic en Nuevo Chat (FUNDAMENTAL para iniciar flujo)
                service.click_new_chat()
                
                # Buscar contacto
                if not service.search_contact(target_phone):
                    # Si no es el último intento, continuar con el siguiente
                    if attempt_index < len(phone_list) - 1:
                        self._update_progress(f"[{profile_name}] {phone}: Intento {attempt_index+1} fallido, probando contacto alternativo...")
                        continue
                    else:
                        status = "No encontrado"
                        self.report_service.add_entry(phone, status)
                        self._update_progress(f"[{profile_name}] {phone}: No encontrado")
                        return

                # Verificar existencia (opcional, igual que en AutomationRunner)
                exists, has_whatsapp, error_msg = service.check_contact_exists()
                if not exists:
                    if "conexión" in error_msg:
                        service.handle_connection_error()
                    # Si no es el último intento, continuar con el siguiente
                    if attempt_index < len(phone_list) - 1:
                        continue
                    else:
                        status = error_msg or "Error verificación"
                        self.report_service.add_entry(phone, status)
                        self._update_progress(f"[{profile_name}] {phone}: {status}")
                        return
                
                if not has_whatsapp:
                    service.go_back()  # Importante: volver atrás para resetear estado
                    # Si no es el último intento, continuar con el siguiente
                    if attempt_index < len(phone_list) - 1:
                        self._update_progress(f"[{profile_name}] {phone}: Sin WhatsApp en intento {attempt_index+1}, probando contacto alternativo...")
                        continue
                    else:
                        status = "Sin WhatsApp (Todos los contactos)"
                        self.report_service.add_entry(phone, status)
                        self._update_progress(f"[{profile_name}] {phone}: {status}")
                        return
                    
                service.open_chat()
                
                # Preparar mensaje
                msg_type = self.config.get("message_type")
                camp_type = self.config.get("campaign_type")
                
                message_text = ""
                image_path = None
                
                # Lógica de mensaje (similar a AutomationRunner)
                # Lógica de mensaje (similar a AutomationRunner)
                if msg_type == "Facturas":
                    folder = self.config.get("facturas_folder")
                    pdf_path = verify_pdf_file(folder, f"{phone}.pdf")
                    if pdf_path:
                        # Enviar solo PDF con mensaje fijo
                        service.attach_file(pdf_path)
                        service.send_attached_file()
                        message_text = "Hola, adjunto tu factura." 
                    else:
                        self.report_service.add_entry(phone, "Sin Factura PDF")
                        return
                
                elif camp_type == "Default":
                    message_text = generate_random_message()
                else:
                    # Campaña (Predet o Custom)
                    if self.campaign:
                        base_msg = self.campaign.message
                        user_info = self.user_data.get(phone, {})
                        # Usar fallback_campaign si está disponible, sino usar el mensaje base como fallback
                        fallback_msg = self.fallback_campaign.message if self.fallback_campaign else base_msg
                        message_text = replace_variables(base_msg, user_info, fallback_msg)
                        # CORRECCIÓN: Usar atributo 'image' no 'image_path'
                        if self.campaign.image:
                            image_path = self.campaign.image
                
                # Flujo de Envio Diferenciado
                from selenium.webdriver.common.keys import Keys
                if sim:
                    sim.micro_pausa()
                if image_path and os.path.exists(image_path):
                    # 1. Adjuntar imagen
                    if service.attach_file(image_path):
                        # 2. Si hay texto, enviarlo como comentario (caption)
                        if message_text:
                            if sim:
                                try:
                                    caption = service.driver.switch_to.active_element
                                    sim.escribir_como_humano(caption, message_text)
                                except Exception:
                                    for line in message_text.split('\n'):
                                        service.driver.switch_to.active_element.send_keys(line)
                                        service.driver.switch_to.active_element.send_keys(Keys.SHIFT + Keys.ENTER)
                            else:
                                for line in message_text.split('\n'):
                                    service.driver.switch_to.active_element.send_keys(line)
                                    service.driver.switch_to.active_element.send_keys(Keys.SHIFT + Keys.ENTER)

                        # 3. Enviar todo (Imagen + Texto)
                        service.send_attached_file()
                    else:
                        # Fallback si falla adjuntar: enviar solo texto
                        if message_text:
                            if sim:
                                sim.enviar_mensaje_humano(service, message_text)
                            else:
                                service.send_text_message(message_text)
                                service.send_message_simple()
                else:
                    # Flujo Solo Texto
                    if message_text:
                        if sim:
                            sim.enviar_mensaje_humano(service, message_text)
                        else:
                            service.send_text_message(message_text)
                            service.send_message_simple()
                    
                status = "Enviado"
                if attempt_index > 0:
                    status = f"Enviado al contacto {attempt_index+1}"
                service.close_chat()
                
                # Éxito, salir del bucle
                break
                
            except Exception as e:
                print(f"Error procesando {target_phone} (intento {attempt_index+1}): {e}")
                # Si no es el último intento, continuar con el siguiente
                if attempt_index < len(phone_list) - 1:
                    continue
                else:
                    status = f"Error: {str(e)}"
            
        self.report_service.add_entry(phone, status)
        self._update_progress(f"[{profile_name}] {phone}: {status}")

    def _update_progress(self, current_action):
        """Actualiza el progreso general."""
        with self.count_lock:
            self.processed_count += 1
            idx = self.processed_count
            
        if self.progress_callback:
            self.progress_callback(idx, self.total_messages, current_action)
