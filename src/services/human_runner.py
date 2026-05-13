"""
Runner del Modo Simulador Humano.
Extiende la logica de AutomationRunner aplicando comportamiento humano
en cada interaccion: tipeo realista, clics suavizados, rate limiting
por ventana de tiempo y fingerprinting anti-deteccion.
"""
import time
import random
import threading
from datetime import datetime
from .whatsapp_service import WhatsAppService
from .whatsapp_monitor_service import WhatsAppMonitorService
from .report_service import ReportService
from .human_simulator import HumanSimulator, RateLimiter
from ..utils.message_templates import generate_random_message, replace_variables
from ..models.campaign import Campaign


class HumanRunner:
    """
    Ejecuta una tarea de envio con comportamiento humano simulado.
    Modo individual unicamente (modo distribuido / rotacion en version futura).
    """

    def __init__(
        self,
        browser_profile,
        config: dict,
        phone_numbers: list,
        user_data: dict = None,
        contact_data: dict = None,
        campaign=None,
        fallback_campaign=None,
        progress_callback=None,
        completion_callback=None,
    ):
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
        self.whatsapp_service = WhatsAppService()
        self.report_service = ReportService()
        self.monitor_service = None

        # Extraer sub-config del simulador humano
        hs_cfg = config.get("human_sim", {})
        self._hs_cfg = hs_cfg

        # Rate limiter
        max_msgs     = int(hs_cfg.get("msgs_per_window", 7))
        window_mins  = int(hs_cfg.get("window_minutes", 10))
        self.rate_limiter = RateLimiter(max_msgs, window_mins)

    # ─────────────────────────────────────────────────────────────────────────
    # Control del hilo
    # ─────────────────────────────────────────────────────────────────────────

    def start(self):
        """Inicia la ejecucion en un hilo daemon."""
        t = threading.Thread(target=self._run)
        t.daemon = True
        t.start()

    def stop(self):
        """Detiene el runner de forma ordenada."""
        self.stop_event.set()

    # ─────────────────────────────────────────────────────────────────────────
    # Logica principal
    # ─────────────────────────────────────────────────────────────────────────

    def _run(self):
        try:
            # ── 1. Iniciar navegador ──────────────────────────────────────────
            self._cb(0, len(self.phone_numbers), "Iniciando navegador (Modo Humano)...")

            if not self.whatsapp_service.initialize_driver(self.profile.path):
                self._marcar_bloqueado()
                raise Exception("Fallo inicio navegador (Perfil BLOQUEADO)")

            # ── 2. Inyectar fingerprints ANTES de que WhatsApp cargue ─────────
            self._cb(0, len(self.phone_numbers), "Inyectando fingerprints anti-deteccion...")
            sim = HumanSimulator(self.whatsapp_service.driver, self._hs_cfg)
            sim.inyectar_fingerprints()

            # ── 3. Verificar QR / session ────────────────────────────────────
            self._cb(0, len(self.phone_numbers), "Verificando sesion...")
            time.sleep(4)

            if self.whatsapp_service.is_qr_visible():
                self._cb(0, len(self.phone_numbers), "QR detectado — Perfil BLOQUEADO")
                self._marcar_bloqueado()
                raise Exception("QR detectado al inicio — Perfil BLOQUEADO")

            self._cb(0, len(self.phone_numbers), "Esperando inicio de sesion...")
            max_wait = 300
            t0 = time.time()
            while not self.stop_event.is_set():
                if self.whatsapp_service.is_logged_in():
                    break
                if time.time() - t0 > max_wait:
                    raise Exception("Timeout esperando inicio de sesion")
                time.sleep(2)

            if self.stop_event.is_set():
                return

            # ── 4. Warm-up de sesion ──────────────────────────────────────────
            self._cb(0, len(self.phone_numbers), "Calentando sesion...")
            sim.calentar_sesion()

            # ── 5. Inicializar monitor (si esta configurado) ──────────────────
            monitor_group  = self.config.get("monitor_group", "")
            monitor_backup = self.config.get("monitor_backup", "")
            if monitor_group or monitor_backup:
                self.monitor_service = WhatsAppMonitorService(
                    driver=self.whatsapp_service.driver,
                    notification_group=monitor_group or None,
                    notification_backup=monitor_backup or None,
                    profile_name=self.profile.name
                )
                print(f"[HumanRunner] Monitor activo — Grupo: '{monitor_group}' | Respaldo: '{monitor_backup}'")

            # ── 6. Bucle de envio ─────────────────────────────────────────────
            total = len(self.phone_numbers)

            for index, phone in enumerate(self.phone_numbers):
                if self.stop_event.is_set():
                    break

                # Verificar horario activo
                sim.esperar_si_fuera_horario()
                if self.stop_event.is_set():
                    break

                # Esperar segun Rate Limiter
                espera = self.rate_limiter.tiempo_hasta_siguiente()
                if espera > 0:
                    self._cb(index, total, f"Rate limiter: esperando {espera:.0f}s...")
                    # Mientras espera, hace scroll idle para simular actividad
                    t_espera = time.time()
                    while time.time() - t_espera < espera:
                        if self.stop_event.is_set():
                            break
                        restante = espera - (time.time() - t_espera)
                        idle_secs = min(restante, random.uniform(2, 5))
                        if idle_secs > 0:
                            sim.scroll_idle(idle_secs)

                if self.stop_event.is_set():
                    break

                # Monitor antes del envio
                monitor_time = 0
                if self.monitor_service:
                    try:
                        auto_reply_text = self.config.get("auto_reply_text")
                        monitor_time = self.monitor_service.monitorear_y_notificar(
                            self.whatsapp_service,
                            max_time=20,
                            auto_reply_text=auto_reply_text
                        )
                    except Exception as e:
                        print(f"[HumanRunner] Error en monitor: {e}")

                self._cb(index, total, f"Preparando envio a {phone}...")

                # Lista de intentos (numero principal + contactos alternativos)
                phone_list = [phone]
                contacts = self.contact_data.get(phone, {})
                if contacts:
                    import numpy as np
                    valid = [
                        v for v in contacts.values()
                        if v is not None and not (isinstance(v, float) and np.isnan(v))
                    ]
                    phone_list.extend(valid)

                sent_ok = False
                for attempt_idx, target in enumerate(phone_list):
                    if self.stop_event.is_set():
                        break

                    try:
                        # Verificar sesion activa
                        if not self.whatsapp_service.is_session_active():
                            self._marcar_bloqueado()
                            raise Exception("Sesion cerrada (Perfil BLOQUEADO)")

                        # Construir mensaje
                        message_text, image_path = self._build_message(phone)

                        # ── ENVIO CON COMPORTAMIENTO HUMANO ──────────────────
                        self._cb(index, total, f"Enviando a {target}...")

                        # Click nuevo chat (humano)
                        try:
                            from selenium.webdriver.common.by import By
                            btn = self.whatsapp_service.wait.until(
                                lambda d: d.find_element(By.CSS_SELECTOR, "[title='Nuevo chat'], [aria-label='Nuevo chat']")
                            )
                            sim.micro_pausa()
                            sim.clic_humano(btn)
                        except Exception:
                            self.whatsapp_service.click_new_chat()

                        time.sleep(random.uniform(0.5, 1.2))

                        # Buscar contacto (escritura humana)
                        if not self._buscar_contacto_humano(sim, str(target)):
                            self._check_session_lockout(index, total)
                            if attempt_idx < len(phone_list) - 1:
                                continue
                            self.report_service.add_entry(phone, "No encontrado / Error busqueda")
                            break

                        exists, has_wa, _ = self.whatsapp_service.check_contact_exists()
                        if not has_wa:
                            self._check_session_lockout(index, total)
                            self.whatsapp_service.go_back()
                            if attempt_idx < len(phone_list) - 1:
                                continue
                            self.report_service.add_entry(phone, "Sin WhatsApp (todos los contactos)")
                            break

                        # Abrir chat
                        sim.micro_pausa()
                        self.whatsapp_service.open_chat()
                        time.sleep(random.uniform(0.6, 1.5))

                        # Enviar mensaje con escritura humana
                        self._enviar_mensaje_humano(sim, message_text, image_path)

                        status = "Enviado" if attempt_idx == 0 else f"Enviado al contacto {attempt_idx+1}"
                        self.report_service.add_entry(phone, status)
                        self.rate_limiter.registrar_envio()
                        sent_ok = True

                        # Cerrar chat con micro-pausa
                        sim.micro_pausa()
                        self.whatsapp_service.close_chat()
                        break

                    except Exception as e:
                        print(f"[HumanRunner] Error procesando {target} (intento {attempt_idx+1}): {e}")
                        self._check_session_lockout(index, total)
                        if attempt_idx < len(phone_list) - 1:
                            continue
                        self.report_service.add_entry(phone, f"Error: {e}")
                        try:
                            self.whatsapp_service.driver.refresh()
                        except Exception:
                            pass
                        time.sleep(5)

                # Pausa larga si corresponde
                if sent_ok:
                    sim.pausa_larga_si_toca()

        except Exception as e:
            print(f"[HumanRunner] Error fatal: {e}")
            if self.progress_callback:
                self.progress_callback(0, 0, f"Error: {e}")
        finally:
            self.whatsapp_service.close()
            report_path = self.report_service.save_report()
            if self.completion_callback:
                self.completion_callback(report_path)

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers internos
    # ─────────────────────────────────────────────────────────────────────────

    def _cb(self, idx, total, msg):
        if self.progress_callback:
            self.progress_callback(idx, total, msg)

    def _marcar_bloqueado(self):
        try:
            if "BLOQUEADO" not in self.profile.tags:
                self.profile.tags.append("BLOQUEADO")
                self.profile.save_metadata()
                print(f"[HumanRunner] Perfil {self.profile.name} marcado como BLOQUEADO.")
        except Exception as e:
            print(f"[HumanRunner] Error guardando etiqueta BLOQUEADO: {e}")

    def _check_session_lockout(self, index, total):
        try:
            if not self.whatsapp_service.is_session_active():
                self._cb(index, total, "Sesion cerrada. Marcando BLOQUEADO...")
                self._marcar_bloqueado()
                raise Exception("Sesion cerrada (Perfil BLOQUEADO)")
        except Exception as e:
            if "BLOQUEADO" in str(e):
                raise
            print(f"[HumanRunner] Error verificando lockout: {e}")

    def _build_message(self, phone: str):
        """Construye el texto del mensaje e imagen segun la configuracion."""
        msg_type = self.config.get("message_type", "")
        message_text = ""
        image_path = ""

        if self.config.get("campaign_type") == "Default":
            message_text = generate_random_message()
        elif self.campaign:
            raw = self.campaign.message
            if phone in self.user_data:
                fallback_msg = (
                    self.fallback_campaign.message
                    if self.fallback_campaign
                    else self.campaign.message
                )
                message_text = replace_variables(raw, self.user_data.get(phone, {}), fallback_msg)
            else:
                message_text = self.campaign.message
            if self.campaign.image:
                image_path = self.campaign.image

        return message_text, image_path

    def _buscar_contacto_humano(self, sim: HumanSimulator, phone: str) -> bool:
        """Busca un contacto usando escritura humana en el campo de busqueda."""
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.keys import Keys

            short_wait = WebDriverWait(self.whatsapp_service.driver, 10)
            input_field = short_wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//p[contains(@class,"copyable-text") and contains(@class,"x15bjb6t")]'
                    ' | //input[@data-tab="3" and contains(@class,"html-input")]'
                ))
            )
            # Limpiar campo
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.DELETE)

            sim.micro_pausa()
            # Escribir numero con tipeo humano
            sim.escribir_como_humano(input_field, phone)
            time.sleep(random.uniform(0.6, 1.2))
            return True
        except Exception as e:
            print(f"[HumanRunner] Error buscando contacto: {e}")
            return False

    def _enviar_mensaje_humano(self, sim: HumanSimulator, message_text: str, image_path: str):
        """Envia el mensaje usando escritura humana."""
        import os
        from selenium.webdriver.common.keys import Keys

        if image_path and os.path.exists(image_path):
            # Con imagen: adjuntar y agregar caption con escritura humana
            if self.whatsapp_service.attach_file(image_path):
                if message_text:
                    try:
                        caption_box = self.whatsapp_service.driver.switch_to.active_element
                        sim.micro_pausa()
                        sim.escribir_como_humano(caption_box, message_text)
                        caption_box.send_keys(Keys.SHIFT + Keys.ENTER)
                    except Exception:
                        pass
                self.whatsapp_service.send_attached_file()
            else:
                if message_text:
                    self._escribir_y_enviar(sim, message_text)
        else:
            if message_text:
                self._escribir_y_enviar(sim, message_text)

    def _escribir_y_enviar(self, sim: HumanSimulator, texto: str):
        """Localiza el input box, escribe con tipeo humano y envia."""
        from selenium.webdriver.common.keys import Keys

        input_box = self.whatsapp_service._get_message_input_box()
        if not input_box:
            raise Exception("No se encontro el input de mensaje")

        # Limpiar
        input_box.send_keys(Keys.CONTROL + "a")
        input_box.send_keys(Keys.DELETE)

        sim.micro_pausa()

        # Escribir con comportamiento humano (parrafo a parrafo)
        parrafos = texto.split("\n")
        for i, parrafo in enumerate(parrafos):
            sim.escribir_como_humano(input_box, parrafo)
            if i < len(parrafos) - 1:
                input_box.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(random.uniform(0.1, 0.3))

        # Pausa antes de enviar (como si revisara el mensaje)
        time.sleep(random.uniform(0.4, 1.2))
        input_box.send_keys(Keys.ENTER)
