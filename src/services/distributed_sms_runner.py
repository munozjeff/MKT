"""
Runner Distribuido de automatización SMS via Google Messages.
Múltiples perfiles de Chrome, cada uno con su propia sesión de Google Messages,
procesan la cola de números en paralelo.
"""
import threading
import queue
import time
import random
from .google_messages_service import GoogleMessagesService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables


class DistributedSmsRunner:
    """Coordina el envío distribuido de SMS entre múltiples perfiles."""

    def __init__(self, browser_profiles, config, phone_numbers, user_data=None,
                 contact_data=None, campaign=None, fallback_campaign=None,
                 progress_callback=None, completion_callback=None):
        self.profiles = browser_profiles
        self.config = config
        self.user_data = user_data or {}
        self.contact_data = contact_data or {}
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback

        self.report_service = ReportService()
        self.phone_queue = queue.Queue()
        for phone in phone_numbers:
            self.phone_queue.put(phone)

        self.stop_event = threading.Event()
        self.total_messages = len(phone_numbers)
        self.processed_count = 0
        self.count_lock = threading.Lock()

        self.active_services = []
        self.active_services_lock = threading.Lock()

    def start(self):
        """Inicia la ejecución distribuida."""
        master_thread = threading.Thread(target=self._master_run, daemon=True)
        master_thread.start()

    def stop(self):
        """Detiene la ejecución."""
        self.stop_event.set()

    def _master_run(self):
        """Hilo principal que coordina los workers."""
        workers = []
        for profile in self.profiles:
            t = threading.Thread(target=self._worker_run, args=(profile,), daemon=True)
            workers.append(t)
            t.start()
            time.sleep(2)  # Pausa entre inicios para no saturar CPU

        for t in workers:
            t.join()

        report_path = self.report_service.save_report(filename_prefix="Informe_SMS_Distribuido")
        if self.completion_callback:
            self.completion_callback(report_path)

    def _worker_run(self, profile):
        """Lógica de cada worker con su propio navegador."""
        service = GoogleMessagesService()
        with self.active_services_lock:
            self.active_services.append(service)

        try:
            if not service.initialize_driver(profile.path):
                print(f"[SMS-Dist][{profile.name}] Falló al iniciar driver")
                return

            print(f"[SMS-Dist][{profile.name}] Esperando autenticación...")
            if not self._wait_for_login(service, profile):
                print(f"[SMS-Dist][{profile.name}] Autenticación fallida — worker omitido")
                return

            print(f"[SMS-Dist][{profile.name}] Listo para enviar.")

            while not self.phone_queue.empty() and not self.stop_event.is_set():
                try:
                    current_phone = self.phone_queue.get_nowait()
                except queue.Empty:
                    break

                self._process_single_message(service, current_phone, profile.name)

                if not self.stop_event.is_set():
                    base_interval = int(self.config.get("interval", 20))
                    sleep_time = random.uniform(base_interval * 0.8, base_interval * 1.2)
                    time.sleep(sleep_time)

        except Exception as e:
            print(f"[SMS-Dist][{profile.name}] Error crítico: {e}")
        finally:
            service.close()
            with self.active_services_lock:
                if service in self.active_services:
                    self.active_services.remove(service)

    def _wait_for_login(self, service, profile) -> bool:
        """Espera autenticación (max 5 min)."""
        time.sleep(3)
        max_wait = 300
        start = time.time()
        while time.time() - start < max_wait:
            if self.stop_event.is_set():
                return False
            if service.is_logged_in():
                return True
            time.sleep(2)
        return False

    def _process_single_message(self, service, phone, profile_name):
        """Procesa un solo número."""
        status = "Fallido"

        phone_list = [phone]
        contacts = self.contact_data.get(phone, {})
        if contacts:
            import numpy as np
            valid = [v for v in contacts.values()
                     if v is not None and not (isinstance(v, float) and np.isnan(v))]
            phone_list.extend(valid)

        for attempt_index, target_phone in enumerate(phone_list):
            try:
                if not service.is_session_active():
                    raise Exception("Sesión cerrada")

                message_text = self._build_message(phone)
                if not message_text:
                    status = "Sin mensaje"
                    break

                service.click_new_chat()

                if not service.search_contact(str(target_phone)):
                    if attempt_index < len(phone_list) - 1:
                        continue
                    status = "No encontrado"
                    break

                exists, has_sms, err = service.check_contact_exists()
                if not has_sms:
                    service.go_back()
                    if attempt_index < len(phone_list) - 1:
                        continue
                    status = "Número no reconocido"
                    break

                if not service.open_chat():
                    if attempt_index < len(phone_list) - 1:
                        continue
                    status = "Error abriendo chat"
                    break

                service.send_text_message(message_text)
                service.send_message_simple()
                delivery = service.check_delivery_status(timeout=6)

                status = delivery if attempt_index == 0 else f"{delivery} (contacto {attempt_index + 1})"
                service.close_chat()
                break

            except Exception as e:
                print(f"[SMS-Dist][{profile_name}] Error {target_phone} (intento {attempt_index + 1}): {e}")
                if attempt_index < len(phone_list) - 1:
                    continue
                status = f"Error: {str(e)}"

        self.report_service.add_entry(phone, status)
        self._update_progress(f"[{profile_name}] {phone}: {status}")

    def _build_message(self, phone: str) -> str:
        camp_type = self.config.get("campaign_type", "")
        if camp_type == "Default":
            return generate_random_message()
        if self.campaign:
            raw_msg = self.campaign.message
            user_info = self.user_data.get(phone, {})
            fallback_msg = self.fallback_campaign.message if self.fallback_campaign else raw_msg
            return replace_variables(raw_msg, user_info, fallback_msg)
        return ""

    def _update_progress(self, current_action):
        with self.count_lock:
            self.processed_count += 1
            idx = self.processed_count
        if self.progress_callback:
            self.progress_callback(idx, self.total_messages, current_action)
