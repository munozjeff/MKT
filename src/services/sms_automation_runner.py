"""
Runner Individual de automatización SMS via Google Messages.
"""
import time
import threading
from .google_messages_service import GoogleMessagesService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables

MAX_CONSECUTIVE_CHAT_ERRORS = 3


class SmsAutomationRunner:
    """Ejecuta una tarea de envío de SMS en modo Individual."""

    def __init__(self, browser_profile, config, phone_numbers, user_data=None,
                 contact_data=None, campaign=None, fallback_campaign=None,
                 progress_callback=None, completion_callback=None,
                 profile_blocked_callback=None):
        self.profile = browser_profile
        self.config = config
        self.phone_numbers = phone_numbers
        self.user_data = user_data or {}
        self.contact_data = contact_data or {}
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.profile_blocked_callback = profile_blocked_callback

        self.stop_event = threading.Event()
        self.sms_service = GoogleMessagesService()
        self.report_service = ReportService()
        self.only_rcs = config.get("only_rcs", False)

    def start(self):
        thread = threading.Thread(target=self._run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.stop_event.set()

    def _mark_profile_blocked(self, reason="BLOQUEADO_SMS"):
        try:
            self.profile.add_tag(reason)
            print(f"[SMS][{self.profile.name}] Perfil marcado como {reason}")
        except Exception as e:
            print(f"[SMS][{self.profile.name}] Error marcando perfil: {e}")
        if self.profile_blocked_callback:
            try:
                self.profile_blocked_callback(self.profile.name)
            except Exception:
                pass

    def _run(self):
        try:
            if self.progress_callback:
                self.progress_callback(0, len(self.phone_numbers), "Iniciando Google Messages...")

            if not self.sms_service.initialize_driver(self.profile.path):
                raise Exception("Fallo al iniciar navegador para Google Messages")

            if self.progress_callback:
                self.progress_callback(0, len(self.phone_numbers), "Esperando autenticación QR...")

            time.sleep(3)
            max_wait = 300
            start_wait = time.time()
            while not self.stop_event.is_set():
                if self.sms_service.is_logged_in():
                    break
                if time.time() - start_wait > max_wait:
                    raise Exception("Tiempo de espera de autenticación agotado")
                if self.progress_callback:
                    elapsed = int(time.time() - start_wait)
                    self.progress_callback(0, len(self.phone_numbers),
                                           f"Escanea el QR en tu teléfono... ({elapsed}s)")
                time.sleep(2)

            if self.stop_event.is_set():
                return

            if self.progress_callback:
                self.progress_callback(0, len(self.phone_numbers), "✅ Autenticado. Iniciando envíos...")

            total = len(self.phone_numbers)
            interval = int(self.config.get("interval", 20))
            pause_after = int(self.config.get("pause", 0))
            consecutive_chat_errors = 0

            for index, phone in enumerate(self.phone_numbers):
                if self.stop_event.is_set():
                    break

                # Verificar QR en tiempo de ejecución
                if self.sms_service.is_qr_visible():
                    print(f"[SMS][{self.profile.name}] ⚠️ QR detectado — bloqueando perfil")
                    self._mark_profile_blocked("BLOQUEADO_SMS")
                    self.report_service.add_entry(phone, "QR detectado — envío cancelado")
                    for p in self.phone_numbers[index + 1:]:
                        self.report_service.add_entry(p, "Cancelado (QR detectado en perfil)")
                    if self.progress_callback:
                        self.progress_callback(index, total,
                            f"⚠️ QR detectado — perfil [{self.profile.name}] bloqueado para SMS")
                    return

                if self.progress_callback:
                    self.progress_callback(index, total, f"Enviando SMS a {phone}...")

                chat_failed = self._process_single_message(self.sms_service, phone, self.profile.name)

                if chat_failed:
                    consecutive_chat_errors += 1
                    print(f"[SMS][{self.profile.name}] ⚠️ Error de chat: {consecutive_chat_errors}/{MAX_CONSECUTIVE_CHAT_ERRORS}")
                    if consecutive_chat_errors >= MAX_CONSECUTIVE_CHAT_ERRORS:
                        print(f"[SMS][{self.profile.name}] ❌ {MAX_CONSECUTIVE_CHAT_ERRORS} errores consecutivos de chat — descartando perfil")
                        self._mark_profile_blocked("BLOQUEADO_SMS")
                        for p in self.phone_numbers[index + 1:]:
                            self.report_service.add_entry(p, "Cancelado (perfil descartado por errores de chat)")
                        if self.progress_callback:
                            self.progress_callback(index + 1, total,
                                f"❌ [{self.profile.name}] Descartado — 3 errores consecutivos de chat")
                        return
                else:
                    consecutive_chat_errors = 0

                if index < total - 1 and not self.stop_event.is_set():
                    time.sleep(interval)
                    if pause_after > 0 and (index + 1) % pause_after == 0:
                        if self.progress_callback:
                            self.progress_callback(index + 1, total, "Pausa programada...")
                        time.sleep(60)

        except Exception as e:
            print(f"[SMS Runner] Error fatal: {e}")
            if self.progress_callback:
                self.progress_callback(0, 0, f"Error: {e}")
        finally:
            self.sms_service.close()
            report_path = self.report_service.save_report(filename_prefix="Informe_SMS")
            if self.completion_callback:
                self.completion_callback(report_path)

    def _process_single_message(self, service, phone, profile_name) -> bool:
        """
        Procesa un solo número.
        Retorna True si el fallo fue por error al abrir el chat (para contador consecutivo).
        Retorna False en cualquier otro caso (éxito, número no encontrado, etc.).
        """
        status = "Fallido"
        is_chat_failure = False

        phone_list = [phone]
        contacts = self.contact_data.get(phone, {})
        if contacts:
            import numpy as np
            valid = [v for v in contacts.values()
                     if v is not None and not (isinstance(v, float) and np.isnan(v))]
            phone_list.extend(valid)

        for attempt_index, target_phone in enumerate(phone_list):
            if self.stop_event.is_set():
                break
            try:
                # Verificar sesión / QR
                if not service.is_session_active():
                    if service.is_qr_visible():
                        raise _QrDetectedException("QR detectado")
                    raise Exception("Sesión cerrada inesperadamente")

                message_text = self._build_message(phone)
                if not message_text:
                    self.report_service.add_entry(phone, "Sin mensaje configurado")
                    return False

                # Flujo: nuevo chat → buscar → abrir → verificar textarea
                service.click_new_chat()

                if not service.search_contact(str(target_phone)):
                    if attempt_index < len(phone_list) - 1:
                        continue
                    self.report_service.add_entry(phone, "No encontrado / Error búsqueda")
                    return False

                exists, has_sms, err = service.check_contact_exists()
                if not has_sms:
                    service.go_back()
                    if attempt_index < len(phone_list) - 1:
                        continue
                    self.report_service.add_entry(phone, "Número no reconocido por Google Messages")
                    return False

                # Abrir chat
                if not service.open_chat():
                    print(f"[SMS][{profile_name}] ⚠️ open_chat() falló para {target_phone} — volviendo")
                    try:
                        service.go_back()
                    except Exception:
                        pass
                    if attempt_index < len(phone_list) - 1:
                        is_chat_failure = True
                        continue
                    self.report_service.add_entry(phone, "Error abriendo chat")
                    return True  # <- fallo de chat

                # ── Filtro Solo RCS ───────────────────────────────────────────
                # Se verifica inmediatamente después de abrir el chat (antes de
                # cualquier otra acción) leyendo el placeholder del textarea.
                # Polling cada 100ms por hasta 5s para capturar el flash inicial.
                if self.only_rcs and not service.is_rcs_available(timeout=5):
                    print(f"[SMS][{profile_name}] No RCS para {target_phone} — omitiendo")
                    try:
                        service.go_back()
                    except Exception:
                        pass
                    self.report_service.add_entry(phone, "No RCS — omitido")
                    return False  # no es fallo de chat

                # Verificación extra: ¿el textarea es accesible?
                if not service.verify_chat_opened():
                    print(f"[SMS][{profile_name}] ⚠️ Textarea no encontrado tras open_chat() — volviendo")
                    try:
                        service.go_back()
                    except Exception:
                        pass
                    if attempt_index < len(phone_list) - 1:
                        is_chat_failure = True
                        continue
                    self.report_service.add_entry(phone, "Error chat — textarea inaccesible")
                    return True  # <- fallo de chat

                # RCS confirmado (o no requerido) — seleccionar SIM y enviar
                is_chat_failure = False
                service.select_next_sim()

                if not service.send_text_message(message_text):
                    self.report_service.add_entry(phone, "Error escribiendo mensaje")
                    return False

                service.send_message_simple()
                delivery_status = service.check_delivery_status(timeout=10)
                status_msg = delivery_status
                if attempt_index > 0:
                    status_msg = f"{delivery_status} (contacto {attempt_index + 1})"
                self.report_service.add_entry(phone, status_msg)
                service.close_chat()
                return False  # éxito

            except _QrDetectedException:
                raise
            except Exception as e:
                print(f"[SMS] Error procesando {target_phone} (intento {attempt_index + 1}): {e}")
                if attempt_index < len(phone_list) - 1:
                    continue
                self.report_service.add_entry(phone, f"Error: {str(e)}")
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


class _QrDetectedException(Exception):
    pass
