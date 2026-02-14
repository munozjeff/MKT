"""
Servicio para la ejecución con rotación de perfiles.
Gestiona un pool de perfiles activos con límites de mensajes y rotación inteligente.
"""
import threading
import queue
import time
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from .whatsapp_service import WhatsAppService
from .whatsapp_monitor_service import WhatsAppMonitorService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables
from ..models.campaign import Campaign
from ..utils.file_utils import verify_pdf_file


class RotationAutomationRunner:
    """
    Gestiona el envío con rotación de perfiles:
    - Pool de N perfiles activos simultáneos
    - Cada perfil envía máximo M mensajes
    - Cuando un perfil completa M mensajes, se cierra y se activa otro
    - Selección aleatoria del siguiente perfil (sin repetir hasta agotar pool)
    - GARANTÍA: Siempre mantiene N perfiles activos si hay mensajes pendientes
    """
    
    def __init__(self, 
                 browser_profiles: List,
                 simultaneous_profiles: int,
                 messages_per_profile: int,
                 profile_cooldown_minutes: int = 0,
                 config: dict = None,
                 phone_numbers: List[str] = None,
                 user_data: dict = None,
                 contact_data: dict = None,
                 campaign=None,
                 fallback_campaign=None,
                 progress_callback=None,
                 completion_callback=None):
        
        self.all_profiles = browser_profiles  # Todos los perfiles seleccionados
        self.simultaneous_count = simultaneous_profiles  # N perfiles activos a la vez
        self.max_messages_per_profile = messages_per_profile  # Límite de mensajes
        self.profile_cooldown_minutes = profile_cooldown_minutes  # Tiempo antes de reutilizar perfil
        self.config = config or {}
        self.phone_list = phone_numbers or []
        self.user_data = user_data or {}
        self.contact_data = contact_data or {}
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        
        # Servicios
        self.report_service = ReportService()
        
        # Cola de mensajes compartida
        self.phone_queue = queue.Queue()
        for phone in phone_numbers:
            self.phone_queue.put(phone)
        
        # Gestión de pool de perfiles
        self.available_profiles = list(browser_profiles)  # Perfiles disponibles para selección
        self.recently_used = []  # Perfiles usados recientemente (para evitar repetir)
        
        # Workers activos
        self.active_workers: Dict[str, threading.Thread] = {}  # {profile_name: thread}
        self.profile_services: Dict[str, WhatsAppService] = {}  # {profile_name: service}
        self.profile_message_counts: Dict[str, int] = {}  # {profile_name: count}
        self.profile_last_used: Dict[str, datetime] = {}  # {profile_name: timestamp} para cooldown
        
        # Locks y eventos
        self.stop_event = threading.Event()
        self.pool_lock = threading.RLock()  # RLock permite reentrada (fix deadlock)
        self.count_lock = threading.Lock()  # Protege contadores
        
        # Contadores globales
        self.total_messages = len(phone_numbers)
        self.processed_count = 0
        
    def start(self):
        """Inicia la ejecución en un hilo maestro."""
        master_thread = threading.Thread(target=self._master_run, daemon=True)
        master_thread.start()
        
    def stop(self):
        """Detiene la ejecución graciosamente."""
        self.stop_event.set()
        
    def _master_run(self):
        """
        Hilo principal que coordina los workers.
        GARANTIZA que siempre haya N perfiles activos mientras haya mensajes.
        """
        try:
            # Fase inicial: Iniciar N workers
            self._start_initial_workers()
            
            # Loop de monitoreo: mantener siempre N activos
            # Continuar mientras haya workers activos O mensajes pendientes
            while not self.stop_event.is_set():
                # Verificar si hay trabajo pendiente
                has_pending_messages = not self.phone_queue.empty()
                has_active_workers = len(self.active_workers) > 0
                
                if not has_pending_messages and not has_active_workers:
                    print("[Rotación] Cola vacía y sin workers activos. Finalizando...")
                    break
                
                self._maintain_worker_count()
                time.sleep(0.5)  # Polling más frecuente (cada 0.5 segundos)
            
            # Esperar a que terminen los workers restantes
            for thread in list(self.active_workers.values()):
                thread.join(timeout=30)
                
        except Exception as e:
            print(f"Error en master_run: {e}")
        finally:
            # Cleanup: cerrar todos los servicios activos
            self._cleanup_all_services()
            
            # Generar reporte final
            report_path = self.report_service.save_report(filename_prefix="Informe_Rotacion")
            
            if self.completion_callback:
                self.completion_callback(report_path)
    
    def _start_initial_workers(self):
        """Inicia los primeros N workers."""
        profiles_to_start = min(self.simultaneous_count, len(self.all_profiles))
        
        for _ in range(profiles_to_start):
            if self.stop_event.is_set():
                break
            profile = self._select_next_profile()
            if profile:
                self._start_worker(profile)
                time.sleep(2)  # Pausa entre inicios para no saturar
    
    def _maintain_worker_count(self):
        """
        Verifica y mantiene el número de workers activos.
        Si hay menos de N, inicia nuevos hasta alcanzar N.
        """
        with self.pool_lock:
            # Limpiar workers terminados
            finished_workers = [
                name for name, thread in self.active_workers.items()
                if not thread.is_alive()
            ]
            for name in finished_workers:
                print(f"[Rotación] Worker '{name}' terminado. Buscando reemplazo...")
                del self.active_workers[name]
                if name in self.profile_services:
                    del self.profile_services[name]
            
            # Calcular cuántos necesitamos iniciar
            current_count = len(self.active_workers)
            needed = self.simultaneous_count - current_count
            
            # Solo iniciar si hay mensajes pendientes
            if needed > 0 and not self.phone_queue.empty():
                print(f"[Rotación] Activos: {current_count}, Necesarios: {self.simultaneous_count}, Iniciando: {needed}")
                started = 0
                for _ in range(needed):
                    if self.stop_event.is_set() or self.phone_queue.empty():
                        break
                    profile = self._select_next_profile()
                    if profile:
                        self._start_worker(profile)
                        started += 1
                        time.sleep(1)  # Pequeña pausa entre inicios
                    else:
                        print(f"[Rotación] No hay perfiles disponibles (posible cooldown activo)")
                        break
                
                if started > 0:
                    print(f"[Rotación] Se iniciaron {started} nuevos workers")
    
    def _select_next_profile(self) -> Optional[object]:
        """
        Selecciona el siguiente perfil de forma aleatoria sin repetir.
        Respeta el cooldown temporal antes de reutilizar un perfil.
        Retorna None si no hay perfiles disponibles.
        """
        with self.pool_lock:
            # Excluir perfiles actualmente activos
            active_names = set(self.active_workers.keys())
            now = datetime.now()
            
            # Filtrar perfiles disponibles considerando:
            # 1. No están activos actualmente
            # 2. No fueron usados recientemente (lista recently_used)
            # 3. Han pasado el tiempo de cooldown
            candidates = []
            for p in self.available_profiles:
                if p.name in active_names:
                    continue  # Ya está activo
                if p in self.recently_used:
                    continue  # Evitar repetir hasta rotar todos
                
                # Verificar cooldown temporal
                if self.profile_cooldown_minutes > 0 and p.name in self.profile_last_used:
                    last_used = self.profile_last_used[p.name]
                    cooldown_delta = timedelta(minutes=self.profile_cooldown_minutes)
                    if now - last_used < cooldown_delta:
                        continue  # Aún no ha pasado el tiempo de cooldown
                
                candidates.append(p)
            
            # Si no hay candidatos, intentar resetear el pool de usados recientemente
            if not candidates:
                # Quitar de recently_used los que ya no están activos
                self.recently_used = [
                    p for p in self.recently_used
                    if p.name in active_names
                ]
                
                # Recalcular candidatos (ahora solo respetando cooldown)
                candidates = []
                for p in self.available_profiles:
                    if p.name in active_names:
                        continue
                    
                    # Verificar cooldown temporal
                    if self.profile_cooldown_minutes > 0 and p.name in self.profile_last_used:
                        last_used = self.profile_last_used[p.name]
                        cooldown_delta = timedelta(minutes=self.profile_cooldown_minutes)
                        if now - last_used < cooldown_delta:
                            continue
                    
                    candidates.append(p)
            
            if not candidates:
                # Mostrar mensaje de espera por cooldown si hay perfiles en cooldown
                if self.profile_cooldown_minutes > 0:
                    profiles_in_cooldown = [
                        p.name for p in self.available_profiles
                        if p.name not in active_names and p.name in self.profile_last_used
                    ]
                    if profiles_in_cooldown:
                        print(f"[Rotación] Esperando cooldown de perfiles: {profiles_in_cooldown}")
                return None
            
            # Selección aleatoria
            selected = random.choice(candidates)
            self.recently_used.append(selected)
            
            # Mantener recently_used con tamaño máximo
            max_recent = max(1, len(self.all_profiles) - self.simultaneous_count)
            if len(self.recently_used) > max_recent:
                self.recently_used = self.recently_used[-max_recent:]
            
            return selected
    
    def _start_worker(self, profile):
        """Inicia un worker para un perfil específico."""
        thread = threading.Thread(
            target=self._worker_run,
            args=(profile,),
            daemon=True
        )
        self.active_workers[profile.name] = thread
        self.profile_message_counts[profile.name] = 0
        thread.start()
        print(f"[Rotación] Iniciado worker para perfil: {profile.name}")
    
    def _worker_run(self, profile):
        """
        Lógica de cada worker individual.
        Envía mensajes hasta alcanzar el límite o quedarse sin cola.
        """
        service = WhatsAppService()
        monitor_service = None
        self.profile_services[profile.name] = service
        
        try:
            # 1. Inicializar Navegador
            if not service.initialize_driver(profile.path):
                print(f"[{profile.name}] Falló al iniciar driver")
                return  # El master iniciará otro perfil
            
            # 2. Verificar Login
            print(f"[{profile.name}] Esperando login...")
            if not self._wait_for_login(service):
                print(f"[{profile.name}] Timeout login")
                return  # El master iniciará otro perfil
            
            print(f"[{profile.name}] Listo para enviar.")
            
            # Inicializar monitor si está configurado
            monitor_phone = self.config.get("monitor_phone", "")
            if monitor_phone:
                monitor_service = WhatsAppMonitorService(
                    driver=service.driver,
                    notification_contact=monitor_phone,
                    profile_name=profile.name
                )
                print(f"[{profile.name}] 📱 Monitor activado - Notificaciones a: {monitor_phone}")
            
            # 3. Procesar mensajes hasta límite o cola vacía
            messages_sent = 0
            
            while (not self.stop_event.is_set() and 
                   messages_sent < self.max_messages_per_profile):
                
                try:
                    # Timeout corto para permitir chequear stop_event
                    current_phone = self.phone_queue.get(timeout=2)
                except queue.Empty:
                    # Cola vacía, terminar worker
                    break
                
                # MONITOREAR MENSAJES NUEVOS ANTES DE CADA ENVÍO
                monitor_time = 0
                if monitor_service:
                    try:
                        base_interval = int(self.config.get("interval", 20))
                        max_monitor_time = min(30, base_interval // 2)  # Máximo 30 seg para procesar múltiples chats
                        auto_reply_text = self.config.get("auto_reply_text")  # Extraer auto-respuesta
                        monitor_time = monitor_service.monitorear_y_notificar(
                            service, 
                            max_time=max_monitor_time,
                            auto_reply_text=auto_reply_text
                        )
                        if monitor_time > 0:
                            print(f"[{profile.name}] ⏱ Tiempo de monitoreo: {monitor_time:.1f}s")
                    except Exception as e:
                        print(f"[{profile.name}] Error en monitoreo: {e}")
                
                # Procesar mensaje
                self._process_single_message(service, current_phone, profile.name)
                messages_sent += 1
                
                with self.pool_lock:
                    self.profile_message_counts[profile.name] = messages_sent
                
                # Pausa entre mensajes
                if not self.stop_event.is_set():
                    base_interval = int(self.config.get("interval", 20))
                    # Restar el tiempo del monitoreo
                    adjusted_interval = max(1, base_interval - int(monitor_time))
                    sleep_time = random.uniform(adjusted_interval * 0.8, adjusted_interval * 1.2)
                    time.sleep(sleep_time)
            
            print(f"[{profile.name}] Completado. Mensajes enviados: {messages_sent}")
            
        except Exception as e:
            print(f"[{profile.name}] Error crítico en worker: {e}")
        finally:
            # Registrar timestamp de última vez usado (para cooldown)
            with self.pool_lock:
                self.profile_last_used[profile.name] = datetime.now()
            
            service.close()
            with self.pool_lock:
                if profile.name in self.profile_services:
                    del self.profile_services[profile.name]
    
    def _wait_for_login(self, service) -> bool:
        """Espera hasta 60s por login."""
        for _ in range(60):
            if self.stop_event.is_set():
                return False
            if service.is_logged_in():
                return True
            time.sleep(1)
        return False
    
    def _process_single_message(self, service, phone, profile_name):
        """Procesa un solo mensaje usando el servicio dado."""
        status = "Fallido"
        
        # Construir lista de números a intentar (principal + contactos)
        phone_list = [phone]
        contacts = self.contact_data.get(phone, {})
        if contacts:
            import numpy as np
            valid_contacts = [
                v for v in contacts.values() 
                if v is not None and not (isinstance(v, float) and np.isnan(v))
            ]
            phone_list.extend(valid_contacts)
        
        # Intentar con cada número hasta éxito
        for attempt_index, target_phone in enumerate(phone_list):
            try:
                # 1. Clic en Nuevo Chat
                service.click_new_chat()
                
                # Buscar contacto
                if not service.search_contact(target_phone):
                    if attempt_index < len(phone_list) - 1:
                        self._update_progress(
                            f"[{profile_name}] {phone}: Intento {attempt_index+1} fallido, probando alternativo..."
                        )
                        continue
                    else:
                        status = "No encontrado"
                        self.report_service.add_entry(phone, status)
                        self._update_progress(f"[{profile_name}] {phone}: No encontrado")
                        return
                
                # Verificar existencia
                exists, has_whatsapp, error_msg = service.check_contact_exists()
                if not exists:
                    if "conexión" in error_msg:
                        service.handle_connection_error()
                    if attempt_index < len(phone_list) - 1:
                        continue
                    else:
                        status = error_msg or "Error verificación"
                        self.report_service.add_entry(phone, status)
                        self._update_progress(f"[{profile_name}] {phone}: {status}")
                        return
                
                if not has_whatsapp:
                    service.go_back()
                    if attempt_index < len(phone_list) - 1:
                        self._update_progress(
                            f"[{profile_name}] {phone}: Sin WhatsApp, probando alternativo..."
                        )
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
                
                # Lógica de mensaje
                if msg_type == "Facturas":
                    folder = self.config.get("facturas_folder")
                    pdf_path = verify_pdf_file(folder, f"{phone}.pdf")
                    if pdf_path:
                        service.attach_file(pdf_path)
                        service.send_attached_file()
                        message_text = "Hola, adjunto tu factura."
                    else:
                        self.report_service.add_entry(phone, "Sin Factura PDF")
                        return
                
                elif camp_type == "Default":
                    message_text = generate_random_message()
                else:
                    if self.campaign:
                        base_msg = self.campaign.message
                        user_info = self.user_data.get(phone, {})
                        fallback_msg = (
                            self.fallback_campaign.message 
                            if self.fallback_campaign 
                            else base_msg
                        )
                        message_text = replace_variables(base_msg, user_info, fallback_msg)
                        if self.campaign.image:
                            image_path = self.campaign.image
                
                # Flujo de Envío
                from selenium.webdriver.common.keys import Keys
                
                if image_path and os.path.exists(image_path):
                    if service.attach_file(image_path):
                        if message_text:
                            for line in message_text.split('\n'):
                                service.driver.switch_to.active_element.send_keys(line)
                                service.driver.switch_to.active_element.send_keys(
                                    Keys.SHIFT + Keys.ENTER
                                )
                        service.send_attached_file()
                    else:
                        if message_text:
                            service.send_text_message(message_text)
                            service.send_message_simple()
                else:
                    if message_text:
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
    
    def _cleanup_all_services(self):
        """Cierra todos los servicios de navegador activos."""
        with self.pool_lock:
            for service in list(self.profile_services.values()):
                try:
                    service.close()
                except:
                    pass
            self.profile_services.clear()
            self.active_workers.clear()
