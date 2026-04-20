"""
Runner Individual de automatización SMS via Google Messages.
Equivalente a AutomationRunner pero para Google Messages.
No incluye lógica de monitor (no aplica a SMS).
"""
import time
import random
import threading
from datetime import datetime
from .google_messages_service import GoogleMessagesService
from .report_service import ReportService
from ..utils.message_templates import generate_random_message, replace_variables


class SmsAutomationRunner:
    """Ejecuta una tarea de envío de SMS en modo Individual."""

    def __init__(self, browser_profile, config, phone_numbers, user_data=None,
                 contact_data=None, campaign=None, fallback_campaign=None,
                 progress_callback=None, completion_callback=None):
        self.profile = browser_profile
        self.config = config
        self.phone_numbers = phone_numbers
        self.user_data = user_data or {}
        self.contact_data = contact_data or {}
        self.campaign = campaign
        self.fallback_campaign = fallback_campaign
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback

        self.stop_event = threading.Event()
        self.sms_service = GoogleMessagesService()
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
        """Lógica principal del loop de envío."""
        try:
            # 1. Inicializar navegador
            if self.progress_callback:
                self.progress_callback(0, len(self.phone_numbers), "Iniciando Google Messages...")

            if not self.sms_service.initialize_driver(self.profile.path):
                raise Exception("Fallo al iniciar navegador para Google Messages")

            # 2. Esperar autenticación QR si es necesario
            if self.progress_callback:
                self.progress_callback(0, len(self.phone_numbers), "Esperando autenticación QR...")

            time.sleep(3)

            # Si aparece QR, esperar hasta 5 minutos para que el usuario lo escanee
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

            # 3. Bucle de envío
            total = len(self.phone_numbers)
            interval = int(self.config.get("interval", 20))
            pause_after = int(self.config.get("pause", 0))

            for index, phone in enumerate(self.phone_numbers):
                if self.stop_event.is_set():
                    break

                if self.progress_callback:
                    self.progress_callback(index, total, f"Enviando SMS a {phone}...")

                # Construir lista de números a intentar
                phone_list = [phone]
                contacts = self.contact_data.get(phone, {})
                if contacts:
                    import numpy as np
                    valid = [v for v in contacts.values()
                             if v is not None and not (isinstance(v, float) and np.isnan(v))]
                    phone_list.extend(valid)

                sent_successfully = False

                for attempt_index, target_phone in enumerate(phone_list):
                    if self.stop_event.is_set():
                        break

                    try:
                        # Verificar que la sesión esté activa
                        if not self.sms_service.is_session_active():
                            raise Exception("Sesión de Google Messages cerrada inesperadamente")

                        # Resolver mensaje
                        message_text = self._build_message(phone)
                        if not message_text:
                            self.report_service.add_entry(phone, "Sin mensaje configurado")
                            break

                        # Flujo de envío
                        self.sms_service.click_new_chat()

                        if not self.sms_service.search_contact(str(target_phone)):
                            if attempt_index < len(phone_list) - 1:
                                continue
                            self.report_service.add_entry(phone, "No encontrado / Error búsqueda")
                            break

                        exists, has_sms, err = self.sms_service.check_contact_exists()
                        if not has_sms:
                            self.sms_service.go_back()
                            if attempt_index < len(phone_list) - 1:
                                continue
                            self.report_service.add_entry(phone, "Número no reconocido por Google Messages")
                            break

                        if not self.sms_service.open_chat():
                            if attempt_index < len(phone_list) - 1:
                                continue
                            self.report_service.add_entry(phone, "No se pudo abrir el chat")
                            break

                        if not self.sms_service.send_text_message(message_text):
                            self.report_service.add_entry(phone, "Error escribiendo mensaje")
                            break

                        self.sms_service.send_message_simple()

                        # Verificar estado de entrega
                        delivery_status = self.sms_service.check_delivery_status(timeout=6)

                        status_msg = delivery_status
                        if attempt_index > 0:
                            status_msg = f"{delivery_status} (contacto {attempt_index + 1})"

                        self.report_service.add_entry(phone, status_msg)
                        sent_successfully = True

                        self.sms_service.close_chat()
                        break

                    except Exception as e:
                        print(f"[SMS] Error procesando {target_phone} (intento {attempt_index + 1}): {e}")
                        if attempt_index < len(phone_list) - 1:
                            continue
                        self.report_service.add_entry(phone, f"Error: {str(e)}")

                # Pausa entre envíos
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

    def _build_message(self, phone: str) -> str:
        """Construye el texto del mensaje según la configuración de campaña."""
        camp_type = self.config.get("campaign_type", "")
        if camp_type == "Default":
            return generate_random_message()
        if self.campaign:
            raw_msg = self.campaign.message
            user_info = self.user_data.get(phone, {})
            fallback_msg = self.fallback_campaign.message if self.fallback_campaign else raw_msg
            return replace_variables(raw_msg, user_info, fallback_msg)
        return ""
