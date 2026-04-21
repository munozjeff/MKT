"""
Runner Distribuido de automatización SMS via Google Messages.
"""
import threading
import queue
import time
import random
from .google_messages_service import GoogleMessagesService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables

MAX_CONSECUTIVE_CHAT_ERRORS = 3


class DistributedSmsRunner:
    """Coordina el envío distribuido de SMS entre múltiples perfiles."""

    def __init__(self, browser_profiles, config, phone_numbers, user_data=None,
                 contact_data=None, campaign=None, fallback_campaign=None,
                 progress_callback=None, completion_callback=None,
                 profile_blocked_callback=None):
        self.profiles = browser_profiles
        self.config = config
        self.user_data = user_data or {}
        self.contact_data = contact_data or {}
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.profile_blocked_callback = profile_blocked_callback

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
        master_thread = threading.Thread(target=self._master_run, daemon=True)
        master_thread.start()

    def stop(self):
        self.stop_event.set()

    def _master_run(self):
        workers = []
        for profile in self.profiles:
            t = threading.Thread(target=self._worker_run, args=(profile,), daemon=True)
            workers.append(t)
            t.start()
            time.sleep(2)
        for t in workers:
            t.join()
        report_path = self.report_service.save_report(filename_prefix="Informe_SMS_Distribuido")
        if self.completion_callback:
            self.completion_callback(report_path)

    def _mark_profile_blocked(self, profile):
        try:
            profile.add_tag("BLOQUEADO_SMS")
            print(f"[SMS-Dist][{profile.name}] Perfil marcado como BLOQUEADO_SMS")
        except Exception as e:
            print(f"[SMS-Dist][{profile.name}] Error marcando perfil: {e}")
        if self.profile_blocked_callback:
            try:
                self.profile_blocked_callback(profile.name)
            except Exception:
                pass

    def _worker_run(self, profile):
        service = GoogleMessagesService()
        with self.active_services_lock:
            self.active_services.append(service)

        consecutive_chat_errors = 0

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

                # Verificar QR antes de cada número
                if service.is_qr_visible():
                    print(f"[SMS-Dist][{profile.name}] ⚠️ QR detectado — bloqueando perfil")
                    self._mark_profile_blocked(profile)
                    if self.progress_callback:
                        self.progress_callback(self.processed_count, self.total_messages,
                            f"⚠️ [{profile.name}] QR detectado — perfil bloqueado para SMS")
                    return

                try:
                    current_phone = self.phone_queue.get_nowait()
                except queue.Empty:
                    break

                # Doble chequeo QR
                if service.is_qr_visible():
                    self._mark_profile_blocked(profile)
                    self.report_service.add_entry(current_phone, "QR detectado — envío cancelado")
                    self._update_progress(f"⚠️ [{profile.name}] QR detectado — perfil bloqueado")
                    return

                chat_failed = self._process_single_message(service, current_phone, profile.name)

                if chat_failed:
                    consecutive_chat_errors += 1
                    print(f"[SMS-Dist][{profile.name}] ⚠️ Error de chat: {consecutive_chat_errors}/{MAX_CONSECUTIVE_CHAT_ERRORS}")
                    if consecutive_chat_errors >= MAX_CONSECUTIVE_CHAT_ERRORS:
                        print(f"[SMS-Dist][{profile.name}] ❌ {MAX_CONSECUTIVE_CHAT_ERRORS} errores consecutivos — descartando perfil")
                        self._mark_profile_blocked(profile)
                        self._update_progress(f"❌ [{profile.name}] Descartado — 3 errores consecutivos de chat")
                        return
                else:
                    consecutive_chat_errors = 0

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

    def _process_single_message(self, service, phone, profile_name) -> bool:
        """
        Procesa un solo número.
        Retorna True si el fallo fue por error al abrir el chat.
        Retorna False en cualquier otro caso (éxito o fallo no relacionado con el chat).
        """
        is_chat_failure = False

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
                    if service.is_qr_visible():
                        raise _QrDetectedException("QR detectado")
                    raise Exception("Sesión cerrada")

                message_text = self._build_message(phone)
                if not message_text:
                    self.report_service.add_entry(phone, "Sin mensaje")
                    self._update_progress(f"[{profile_name}] {phone}: Sin mensaje")
                    return False

                service.click_new_chat()

                if not service.search_contact(str(target_phone)):
                    if attempt_index < len(phone_list) - 1:
                        continue
                    self.report_service.add_entry(phone, "No encontrado")
                    self._update_progress(f"[{profile_name}] {phone}: No encontrado")
                    return False

                exists, has_sms, err = service.check_contact_exists()
                if not has_sms:
                    service.go_back()
                    if attempt_index < len(phone_list) - 1:
                        continue
                    self.report_service.add_entry(phone, "Número no reconocido")
                    self._update_progress(f"[{profile_name}] {phone}: Número no reconocido")
                    return False

                # Abrir chat
                if not service.open_chat():
                    print(f"[SMS-Dist][{profile_name}] ⚠️ open_chat() falló — volviendo")
                    try:
                        service.go_back()
                    except Exception:
                        pass
                    if attempt_index < len(phone_list) - 1:
                        is_chat_failure = True
                        continue
                    self.report_service.add_entry(phone, "Error abriendo chat")
                    self._update_progress(f"[{profile_name}] {phone}: Error abriendo chat")
                    return True

                # Verificación extra: textarea accesible
                if not service.verify_chat_opened():
                    print(f"[SMS-Dist][{profile_name}] ⚠️ Textarea no encontrado — volviendo al inicio")
                    try:
                        service.go_back()
                    except Exception:
                        pass
                    if attempt_index < len(phone_list) - 1:
                        is_chat_failure = True
                        continue
                    self.report_service.add_entry(phone, "Error chat — textarea inaccesible")
                    self._update_progress(f"[{profile_name}] {phone}: Error chat — textarea inaccesible")
                    return True

                # Chat abierto correctamente
                is_chat_failure = False
                service.send_text_message(message_text)
                service.send_message_simple()
                delivery = service.check_delivery_status(timeout=6)
                status = delivery if attempt_index == 0 else f"{delivery} (contacto {attempt_index + 1})"
                self.report_service.add_entry(phone, status)
                self._update_progress(f"[{profile_name}] {phone}: {status}")
                service.close_chat()
                return False

            except _QrDetectedException:
                raise
            except Exception as e:
                print(f"[SMS-Dist][{profile_name}] Error {target_phone} (intento {attempt_index + 1}): {e}")
                if attempt_index < len(phone_list) - 1:
                    continue
                self.report_service.add_entry(phone, f"Error: {str(e)}")
                self._update_progress(f"[{profile_name}] {phone}: Error: {str(e)}")
                return False

        return is_chat_failure

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


class _QrDetectedException(Exception):
    pass
