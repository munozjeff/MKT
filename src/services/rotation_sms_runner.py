"""
Runner con Rotación de perfiles para automatización SMS via Google Messages.
Basado en RotationAutomationRunner pero usando GoogleMessagesService.
"""
import threading
import queue
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .google_messages_service import GoogleMessagesService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables


class RotationSmsRunner:
    """
    Gestiona el envío SMS con rotación de perfiles:
    - Pool de N perfiles activos simultáneos
    - Cada perfil envía máximo M mensajes antes de rotar
    - Cooldown configurable entre reusos de un mismo perfil
    - Perfiles con QR detectado son marcados BLOQUEADO_SMS y excluidos de rotación
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
                 completion_callback=None,
                 profile_blocked_callback=None):

        self.all_profiles = browser_profiles
        self.simultaneous_count = simultaneous_profiles
        self.max_messages_per_profile = messages_per_profile
        self.profile_cooldown_minutes = profile_cooldown_minutes
        self.config = config or {}
        self.phone_list = phone_numbers or []
        self.user_data = user_data or {}
        self.contact_data = contact_data or {}
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        # Callback opcional: se llama con (profile_name) cuando un perfil es bloqueado por QR
        self.profile_blocked_callback = profile_blocked_callback

        self.report_service = ReportService()

        self.phone_queue = queue.Queue()
        for phone in phone_numbers:
            self.phone_queue.put(phone)

        self.available_profiles = list(browser_profiles)
        self.recently_used = []

        # Perfiles bloqueados por QR en esta sesión (excluidos de selección)
        self.qr_blocked_profile_names = set()

        self.active_workers: Dict[str, threading.Thread] = {}
        self.profile_services: Dict[str, GoogleMessagesService] = {}
        self.profile_message_counts: Dict[str, int] = {}
        self.profile_last_used: Dict[str, datetime] = {}

        self.stop_event = threading.Event()
        self.pool_lock = threading.RLock()
        self.count_lock = threading.Lock()

        self.total_messages = len(phone_numbers)
        self.processed_count = 0

    def start(self):
        master_thread = threading.Thread(target=self._master_run, daemon=True)
        master_thread.start()

    def stop(self):
        self.stop_event.set()

    def _mark_profile_qr_blocked(self, profile):
        """Marca el perfil como BLOQUEADO_SMS y lo excluye de la rotación."""
        try:
            profile.add_tag("BLOQUEADO_SMS")
            print(f"[SMS-Rotación][{profile.name}] Perfil marcado como BLOQUEADO_SMS (QR detectado en ejecución)")
        except Exception as e:
            print(f"[SMS-Rotación][{profile.name}] Error marcando perfil como bloqueado: {e}")

        with self.pool_lock:
            self.qr_blocked_profile_names.add(profile.name)

        if self.profile_blocked_callback:
            try:
                self.profile_blocked_callback(profile.name)
            except Exception:
                pass

    def _master_run(self):
        try:
            self._start_initial_workers()

            while not self.stop_event.is_set():
                has_pending = not self.phone_queue.empty()
                has_active = len(self.active_workers) > 0

                if not has_pending and not has_active:
                    print("[SMS-Rotación] Cola vacía y sin workers activos. Finalizando...")
                    break

                self._maintain_worker_count()
                time.sleep(0.5)

            for thread in list(self.active_workers.values()):
                thread.join(timeout=30)

        except Exception as e:
            print(f"[SMS-Rotación] Error en master_run: {e}")
        finally:
            self._cleanup_all_services()
            report_path = self.report_service.save_report(filename_prefix="Informe_SMS_Rotacion")
            if self.completion_callback:
                self.completion_callback(report_path)

    def _start_initial_workers(self):
        profiles_to_start = min(self.simultaneous_count, len(self.all_profiles))
        for _ in range(profiles_to_start):
            if self.stop_event.is_set():
                break
            profile = self._select_next_profile()
            if profile:
                self._start_worker(profile)
                time.sleep(2)

    def _maintain_worker_count(self):
        with self.pool_lock:
            finished = [name for name, t in self.active_workers.items() if not t.is_alive()]
            for name in finished:
                print(f"[SMS-Rotación] Worker '{name}' terminado. Buscando reemplazo...")
                del self.active_workers[name]
                if name in self.profile_services:
                    del self.profile_services[name]

            current_count = len(self.active_workers)
            needed = self.simultaneous_count - current_count

            if needed > 0 and not self.phone_queue.empty():
                for _ in range(needed):
                    if self.stop_event.is_set() or self.phone_queue.empty():
                        break
                    profile = self._select_next_profile()
                    if profile:
                        self._start_worker(profile)
                        time.sleep(1)
                    else:
                        break

    def _select_next_profile(self) -> Optional[object]:
        with self.pool_lock:
            active_names = set(self.active_workers.keys())
            now = datetime.now()

            candidates = []
            for p in self.available_profiles:
                if p.name in active_names:
                    continue
                # Excluir perfiles bloqueados por QR en esta sesión
                if p.name in self.qr_blocked_profile_names:
                    continue
                if p in self.recently_used:
                    continue
                if self.profile_cooldown_minutes > 0 and p.name in self.profile_last_used:
                    if now - self.profile_last_used[p.name] < timedelta(minutes=self.profile_cooldown_minutes):
                        continue
                candidates.append(p)

            if not candidates:
                self.recently_used = [p for p in self.recently_used if p.name in active_names]
                candidates = [
                    p for p in self.available_profiles
                    if p.name not in active_names
                    and p.name not in self.qr_blocked_profile_names
                    and (
                        self.profile_cooldown_minutes == 0 or
                        p.name not in self.profile_last_used or
                        now - self.profile_last_used[p.name] >= timedelta(minutes=self.profile_cooldown_minutes)
                    )
                ]

            if not candidates:
                return None

            selected = random.choice(candidates)
            self.recently_used.append(selected)
            max_recent = max(1, len(self.all_profiles) - self.simultaneous_count)
            if len(self.recently_used) > max_recent:
                self.recently_used = self.recently_used[-max_recent:]
            return selected

    def _start_worker(self, profile):
        thread = threading.Thread(target=self._worker_run, args=(profile,), daemon=True)
        self.active_workers[profile.name] = thread
        self.profile_message_counts[profile.name] = 0
        thread.start()
        print(f"[SMS-Rotación] Iniciado worker: {profile.name}")

    def _worker_run(self, profile):
        service = GoogleMessagesService()
        self.profile_services[profile.name] = service

        try:
            if not service.initialize_driver(profile.path):
                print(f"[SMS-Rotación][{profile.name}] Falló al iniciar driver")
                return

            print(f"[SMS-Rotación][{profile.name}] Esperando autenticación...")
            if not self._wait_for_login(service, profile):
                print(f"[SMS-Rotación][{profile.name}] Autenticación fallida")
                return

            print(f"[SMS-Rotación][{profile.name}] Listo para enviar.")
            messages_sent = 0

            while (not self.stop_event.is_set() and
                   messages_sent < self.max_messages_per_profile):

                # ── Verificar QR antes de procesar cada número ─────────────────
                if service.is_qr_visible():
                    print(f"[SMS-Rotación][{profile.name}] ⚠️ QR detectado durante ejecución — bloqueando perfil")
                    self._mark_profile_qr_blocked(profile)
                    if self.progress_callback:
                        self.progress_callback(
                            self.processed_count, self.total_messages,
                            f"⚠️ [{profile.name}] QR detectado — perfil bloqueado para SMS"
                        )
                    return  # el master reemplazará este worker con otro perfil

                try:
                    current_phone = self.phone_queue.get(timeout=2)
                except queue.Empty:
                    break

                # Doble chequeo de QR justo después de obtener el número
                if service.is_qr_visible():
                    print(f"[SMS-Rotación][{profile.name}] ⚠️ QR detectado al obtener número — bloqueando perfil")
                    self._mark_profile_qr_blocked(profile)
                    self.report_service.add_entry(current_phone, "QR detectado — envío cancelado")
                    self._update_progress(f"⚠️ [{profile.name}] QR detectado — perfil bloqueado para SMS")
                    return

                self._process_single_message(service, current_phone, profile.name)
                messages_sent += 1

                with self.pool_lock:
                    self.profile_message_counts[profile.name] = messages_sent

                if not self.stop_event.is_set():
                    base_interval = int(self.config.get("interval", 20))
                    sleep_time = random.uniform(base_interval * 0.8, base_interval * 1.2)
                    time.sleep(sleep_time)

            print(f"[SMS-Rotación][{profile.name}] Completado. Enviados: {messages_sent}")

        except Exception as e:
            print(f"[SMS-Rotación][{profile.name}] Error crítico: {e}")
        finally:
            with self.pool_lock:
                self.profile_last_used[profile.name] = datetime.now()
            service.close()
            with self.pool_lock:
                if profile.name in self.profile_services:
                    del self.profile_services[profile.name]

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

    def _process_single_message(self, service, phone, profile_name):
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
                    if service.is_qr_visible():
                        raise _QrDetectedException(f"QR detectado al procesar {phone}")
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

            except _QrDetectedException:
                raise  # propagar hacia _worker_run para que bloquee el perfil
            except Exception as e:
                print(f"[SMS-Rotación][{profile_name}] Error {target_phone} (intento {attempt_index + 1}): {e}")
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

    def _cleanup_all_services(self):
        with self.pool_lock:
            for service in list(self.profile_services.values()):
                try:
                    service.close()
                except Exception:
                    pass
            self.profile_services.clear()
            self.active_workers.clear()


class _QrDetectedException(Exception):
    """Excepción interna: QR detectado durante el procesamiento de un mensaje."""
    pass
