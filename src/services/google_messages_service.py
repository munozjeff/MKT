"""
Servicio para automatización de Google Messages Web usando Selenium.
Replica la interfaz pública de WhatsAppService para ser intercambiable
en los runners de automatización.
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from ..config.settings import CHROMEDRIVER_PATH, GOOGLE_MESSAGES_URL, GOOGLE_MESSAGES_WAIT_TIMEOUT


class GoogleMessagesService:
    """
    Servicio para automatizar el envío de mensajes de texto (SMS/RCS)
    a través de Google Messages Web (messages.google.com).
    """

    def __init__(self):
        """Inicializa el servicio."""
        self.driver = None
        self.wait = None
        self.service = Service(CHROMEDRIVER_PATH)
        self._last_delivery_status = None  # resultado del último envío
        self._sim_counter = 0              # contador para rotación de SIM
        self._sim_count_cache = None       # número de SIMs detectadas (caché)

    # ──────────────────────────────────────────────────────────────
    # Inicialización del navegador
    # ──────────────────────────────────────────────────────────────

    def initialize_driver(self, profile_path: str = None) -> bool:
        """
        Inicializa el navegador Chrome con el perfil dado y navega a Google Messages.
        Reintenta hasta 3 veces si Chrome sale inmediatamente (perfil bloqueado o crash).
        """
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                if self.driver:
                    return self._ensure_on_messages()

                options = webdriver.ChromeOptions()

                # Rendimiento
                options.page_load_strategy = 'eager'
                options.add_argument("--disable-notifications")
                options.add_argument("--disable-logging")
                options.add_argument("--log-level=3")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-popup-blocking")
                options.add_argument("--disable-infobars")

                # Perfil de Chrome (mantiene la sesión autenticada)
                if profile_path:
                    options.add_argument(f"user-data-dir={profile_path}")

                # Anti-detección
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])

                # Estabilidad (evita crashes por DevToolsActivePort, GPU, sandbox)
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-first-run")
                options.add_argument("--no-default-browser-check")
                options.add_argument("--disable-background-networking")
                options.add_argument("--disable-crash-reporter")

                self.driver = webdriver.Chrome(service=self.service, options=options)

                # Ocultar webdriver flag
                try:
                    self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            })
                        """
                    })
                except Exception:
                    pass

                self.wait = WebDriverWait(self.driver, GOOGLE_MESSAGES_WAIT_TIMEOUT)
                return self._ensure_on_messages()

            except Exception as e:
                print(f"[GoogleMessages] Error al iniciar driver (intento {attempt}/{max_attempts}): {e}")
                # Limpiar driver fallido
                try:
                    if self.driver:
                        self.driver.quit()
                except Exception:
                    pass
                self.driver = None

                if attempt < max_attempts:
                    wait_secs = attempt * 5  # 5s, 10s entre reintentos
                    print(f"[GoogleMessages] Reintentando en {wait_secs}s... "
                          f"(Si el perfil está abierto en otra ventana de Chrome, ciérrela primero)")
                    time.sleep(wait_secs)

        print("[GoogleMessages] No se pudo iniciar Chrome tras 3 intentos.")
        return False

    def _ensure_on_messages(self) -> bool:
        """Garantiza que el navegador esté en Google Messages."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                current_url = self.driver.current_url
                if "messages.google.com" in current_url and "data:," not in current_url:
                    return True

                print(f"[GoogleMessages] Navegando (intento {attempt + 1}/{max_retries})...")
                self.driver.get(GOOGLE_MESSAGES_URL)

                WebDriverWait(self.driver, 15).until(
                    lambda d: "messages.google.com" in d.current_url
                )
                print("[GoogleMessages] Navegación confirmada.")
                return True

            except TimeoutException:
                print(f"[GoogleMessages] Timeout esperando carga (intento {attempt + 1})")
            except Exception as e:
                print(f"[GoogleMessages] Error navegando: {e}")
                time.sleep(1)

        print("[GoogleMessages] No se pudo navegar a Google Messages.")
        return False

    # ──────────────────────────────────────────────────────────────
    # Detección de estado de sesión
    # ──────────────────────────────────────────────────────────────

    def is_logged_in(self) -> bool:
        """
        Verifica si la sesión está activa buscando el botón 'Iniciar chat'.
        El botón real es un <a> con data-e2e-start-button.
        """
        try:
            short_wait = WebDriverWait(self.driver, 5)
            short_wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                '[data-e2e-start-button]'
            )))
            return True
        except Exception:
            return False

    def is_qr_visible(self) -> bool:
        """
        Detecta si el código QR de autenticación está visible.
        Retorna True si el QR está presente (sesión no iniciada).
        """
        try:
            # Selector del componente QR de Google Messages
            if self.driver.find_elements(By.TAG_NAME, "mw-qr-code"):
                return True
            if self.driver.find_elements(By.CSS_SELECTOR, "[data-e2e-qr-code]"):
                return True
            if self.driver.find_elements(By.CSS_SELECTOR, "canvas[width='280']"):
                return True
            # Página de autenticación en general
            if "authentication" in self.driver.current_url:
                return True
            return False
        except Exception:
            return False

    def is_session_active(self) -> bool:
        """
        Verifica si la sesión está activa.
        Maneja explícitamente 'invalid session id' cuando Chrome fue cerrado.
        """
        try:
            if self.is_qr_visible():
                print("[GoogleMessages] QR detectado. Sesión cerrada.")
                return False
            found = self.driver.find_elements(By.CSS_SELECTOR, '[data-e2e-start-button]')
            on_new_conv = 'conversations/new' in self.driver.current_url
            return bool(found) or on_new_conv
        except Exception as e:
            err = str(e).lower()
            if 'invalid session id' in err or 'no such session' in err or 'session deleted' in err:
                print("[GoogleMessages] Sesión de Chrome inválida (Chrome fue cerrado externamente).")
            else:
                print(f"[GoogleMessages] Error verificando sesión: {e}")
            return False

    # ──────────────────────────────────────────────────────────────
    # Flujo de envío
    # ──────────────────────────────────────────────────────────────

    def click_new_chat(self):
        """
        Hace clic en el botón 'Iniciar chat' (elemento <a> Angular).
        Usa JavaScript click para mayor compatibilidad con Angular.
        """
        try:
            # Si ya estamos en la página de nueva conversación, no hace falta clicar
            if 'conversations/new' in self.driver.current_url:
                return

            # Esperar que el elemento esté en el DOM
            btn = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, '[data-e2e-start-button]'
                ))
            )

            # Click via JavaScript (más confiable con Angular)
            self.driver.execute_script("arguments[0].click();", btn)

            # Esperar a que la URL cambie a /conversations/new
            WebDriverWait(self.driver, 15).until(
                lambda d: 'conversations/new' in d.current_url
            )
            time.sleep(0.5)
        except Exception as e:
            print(f"[GoogleMessages] Error click_new_chat: {e}")

    def search_contact(self, phone_number: str) -> bool:
        """
        Pega el número en el input de contacto.
        Selector: input[data-e2e-contact-input]
        El input aparece después de navegar a /conversations/new.
        """
        try:
            short_wait = WebDriverWait(self.driver, 15)

            # Esperar a que la página de nueva conversación cargue y el input aparezca
            input_field = short_wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, 'input[data-e2e-contact-input]'
            )))

            # Limpiar y escribir el número
            input_field.click()
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.DELETE)
            input_field.send_keys(str(phone_number))

            # Dar tiempo a que aparezca la sugerencia
            time.sleep(2)
            return True
        except Exception as e:
            print(f"[GoogleMessages] Error search_contact: {e}")
            return False

    def check_contact_exists(self) -> tuple:
        """
        Verifica si aparece el botón 'Enviar a XXXXXXXXXX'.
        Selector: button[data-e2e-send-to-button]
        Espera hasta 10 segundos.

        Returns:
            (exists: bool, has_sms: bool, error_msg: str)
        """
        try:
            short_wait = WebDriverWait(self.driver, 10)
            try:
                short_wait.until(EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'button[data-e2e-send-to-button]'
                )))
                return True, True, ""
            except TimeoutException:
                return True, False, "Número no reconocido"
        except Exception as e:
            print(f"[GoogleMessages] Error check_contact_exists: {e}")
            return False, False, str(e)

    def open_chat(self) -> bool:
        """
        Hace clic en el botón 'Enviar a XXXXXXXXXX' para abrir el chat.
        Después espera que el textarea esté listo y selecciona la SIM
        correspondiente si el dispositivo tiene más de una.
        """
        try:
            btn = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'button[data-e2e-send-to-button]'
                ))
            )
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", btn)

            # Esperar que la URL cambie de /new a la conversación real
            WebDriverWait(self.driver, 15).until(
                lambda d: (
                    'conversations/new' not in d.current_url and
                    '/conversations/' in d.current_url
                )
            )

            # Esperar que el textarea del mensaje esté presente
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'textarea[data-e2e-message-input-box]'
                ))
            )
            time.sleep(1.0)  # pausa para que el DOM de Angular se estabilice

            # Seleccionar SIM si hay más de una disponible
            self.select_next_sim()

            return True
        except Exception as e:
            print(f"[GoogleMessages] Error open_chat: {e}")
            return False

    def verify_chat_opened(self, timeout: int = 3) -> bool:
        """
        Verificación rápida tras open_chat(): confirma que el textarea
        del mensaje está presente y es interactivo.
        Retorna False si el textarea no aparece en `timeout` segundos.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 'textarea[data-e2e-message-input-box]'
                ))
            )
            return True
        except Exception:
            return False


    def inject_rcs_observer(self) -> bool:
        """
        Inyecta un MutationObserver JavaScript que captura CUALQUIER aparición
        de 'RCS' en el placeholder/aria-label del textarea, incluyendo flashes
        de milisegundos que el polling de Python jamás podría detectar.

        DEBE llamarse ANTES de open_chat() para estar activo desde el primer
        instante en que Google Messages carga el textarea del chat.
        """
        try:
            self.driver.execute_script("""
                // Resetear estado previo
                window.__rcs_detected = false;
                if (window.__rcs_observer) {
                    try { window.__rcs_observer.disconnect(); } catch(e) {}
                }

                function _checkRcsInElement(el) {
                    if (!el || !el.getAttribute) return;
                    var ph = (el.getAttribute('placeholder') || '').toUpperCase();
                    var al = (el.getAttribute('aria-label')  || '').toUpperCase();
                    if (ph.indexOf('RCS') !== -1 || al.indexOf('RCS') !== -1) {
                        window.__rcs_detected = true;
                    }
                }

                window.__rcs_observer = new MutationObserver(function(mutations) {
                    mutations.forEach(function(m) {
                        // Cambio de atributo directo en el textarea
                        if (m.type === 'attributes' && m.target) {
                            _checkRcsInElement(m.target);
                        }
                        // Nodos añadidos al DOM (textarea recién creado)
                        if (m.type === 'childList') {
                            m.addedNodes.forEach(function(node) {
                                if (node.nodeType === 1) {
                                    _checkRcsInElement(node);
                                    if (node.querySelectorAll) {
                                        node.querySelectorAll(
                                            'textarea[data-e2e-message-input-box]'
                                        ).forEach(_checkRcsInElement);
                                    }
                                }
                            });
                        }
                    });
                    // También re-escanear el textarea actual por si cambió sin mutación
                    document.querySelectorAll(
                        'textarea[data-e2e-message-input-box]'
                    ).forEach(_checkRcsInElement);
                });

                window.__rcs_observer.observe(document.body, {
                    childList:       true,
                    subtree:         true,
                    attributes:      true,
                    attributeFilter: ['placeholder', 'aria-label']
                });
            """)
            return True
        except Exception as e:
            print(f"[GoogleMessages] Error inyectando RCS observer: {e}")
            return False

    def query_rcs_observer(self) -> bool:
        """
        Consulta si el MutationObserver detectó 'RCS' en cualquier momento
        desde que fue inyectado (incluyendo flashes brevísimos).
        Desconecta y limpia el observer al leerlo.

        DEBE llamarse DESPUÉS de open_chat() / select_next_sim().
        """
        try:
            detected = self.driver.execute_script("""
                var result = window.__rcs_detected || false;
                if (window.__rcs_observer) {
                    try { window.__rcs_observer.disconnect(); } catch(e) {}
                    window.__rcs_observer = null;
                }
                window.__rcs_detected = false;
                return result;
            """)
            return bool(detected)
        except Exception as e:
            print(f"[GoogleMessages] Error consultando RCS observer: {e}")
            return False

    def is_rcs_available(self, timeout: float = 5.0, poll: float = 0.1) -> bool:
        """
        Verifica si el modo RCS está disponible para el número actual.

        Google Messages tarda unos segundos en negociar el protocolo RCS
        después de abrir el chat. Por eso se sondea cada `poll` segundos
        hasta que aparezca 'RCS' en el placeholder/aria-label del textarea,
        o hasta agotar `timeout` segundos.

        Ejemplo placeholder RCS   : "Mensaje RCS de Movistar"
        Ejemplo placeholder no-RCS: "Mensaje"  /  "Enviar SMS a..."

        Args:
            timeout: Segundos máximos de espera (por defecto 5).
            poll:    Intervalo entre sondeos en segundos (por defecto 0.1 = 100ms).

        Retorna True  → el número admite RCS.
        Retorna False → solo SMS convencional tras agotar el tiempo de espera.
        """
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                textarea = self.driver.find_element(
                    By.CSS_SELECTOR, 'textarea[data-e2e-message-input-box]'
                )
                placeholder = (textarea.get_attribute('placeholder') or '').upper()
                aria_label  = (textarea.get_attribute('aria-label')  or '').upper()
                if 'RCS' in placeholder or 'RCS' in aria_label:
                    print(f"[GoogleMessages] \u2705 RCS detectado: '{placeholder or aria_label}'")
                    return True
            except Exception:
                pass   # textarea aún no visible, seguimos esperando
            time.sleep(poll)

        print(f"[GoogleMessages] No RCS detectado tras {timeout}s de espera")
        return False


    def select_next_sim(self) -> bool:
        """
        Detecta si hay un selector de SIM en la pantalla de conversación.
        Si hay más de una SIM, las alterna automáticamente en cada envío.

        Estrategia:
          1. Busca el botón del selector de SIM (varios selectores posibles).
          2. Abre el menú.
          3. Lee las SIMs disponibles.
          4. Selecciona la SIM según el contador interno (round-robin).

        Returns:
            True  si se seleccionó una SIM
            False si no hay selector de SIM o solo hay una SIM
        """
        try:
            # ── Buscar el botón trigger del selector de SIM ──────────────
            # El selector de SIM es un botón en el área de composición
            # (NO dentro del menú .mat-mdc-menu-content).
            # Intentamos varios selectores en orden de especificidad.
            trigger_selectors = [
                'mws-message-sim-selector button',
                'mw-message-sim-selector button',
                '[data-e2e-sim-selector] button',
                '[data-e2e-sim-button]',
            ]

            sim_trigger = None
            for sel in trigger_selectors:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    sim_trigger = els[0]
                    break

            # Fallback: buscar botón que contenga mw-sim-icon
            # fuera del menú desplegable
            if not sim_trigger:
                candidates = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'mw-sim-icon'
                )
                for c in candidates:
                    # Excluir si está dentro del menú
                    try:
                        in_menu = c.find_elements(
                            By.XPATH,
                            'ancestor::*[contains(@class,"mat-mdc-menu-content")]'
                        )
                        if not in_menu:
                            # El padre inmediato clickeable
                            parent_btn = self.driver.execute_script(
                                """var el = arguments[0];
                                while (el && el.tagName !== 'BUTTON') el = el.parentElement;
                                return el;""", c
                            )
                            if parent_btn:
                                sim_trigger = parent_btn
                                break
                    except Exception:
                        pass

            if not sim_trigger:
                return False  # No hay selector de SIM en esta conversación

            # ── Abrir el menú de SIM ─────────────────────────────────────
            self.driver.execute_script("arguments[0].click();", sim_trigger)

            # Esperar que aparezca el menú con las opciones de SIM
            try:
                WebDriverWait(self.driver, 4).until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR, 'button.sim-menu-item-button'
                    ))
                )
            except TimeoutException:
                # El menú no apareció — puede que solo haya una SIM y se seleccionó automáticamente
                return False

            # ── Leer las SIMs disponibles ─────────────────────────────────
            sim_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, 'button.sim-menu-item-button'
            )
            sim_count = len(sim_buttons)

            if sim_count == 0:
                return False

            # Actualizar caché si cambió el número de SIMs
            if self._sim_count_cache != sim_count:
                self._sim_count_cache = sim_count
                sim_labels = []
                for btn in sim_buttons:
                    try:
                        label = btn.get_attribute('aria-label') or ''
                        sim_labels.append(label)
                    except Exception:
                        sim_labels.append('?')
                print(f"[GoogleMessages] SIMs detectadas ({sim_count}): {sim_labels}")

            # ── Seleccionar SIM en modo round-robin ───────────────────────
            target_index = self._sim_counter % sim_count
            selected_btn = sim_buttons[target_index]

            # Obtener el label para logging
            try:
                label = selected_btn.get_attribute('aria-label') or f'SIM {target_index + 1}'
            except Exception:
                label = f'SIM {target_index + 1}'

            self.driver.execute_script("arguments[0].click();", selected_btn)
            self._sim_counter += 1

            print(f"[GoogleMessages] SIM seleccionada: {label} (slot {target_index + 1}/{sim_count})")
            time.sleep(0.3)
            return True

        except Exception as e:
            print(f"[GoogleMessages] Error select_next_sim: {e}")
            return False

    def send_text_message(self, message: str) -> bool:
        """
        Escribe el mensaje en el textarea de Google Messages.
        - Espera dinámica a que el textarea sea interactivo
        - Click para enfocar antes de escribir
        - Pausa tras cada párrafo para que el DOM se actualice
        """
        try:
            # Esperar que el textarea sea clickeable (no solo presente)
            textarea = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((
                    By.CSS_SELECTOR, 'textarea[data-e2e-message-input-box]'
                ))
            )

            # Enfocar el campo
            textarea.click()
            time.sleep(0.4)

            # Limpiar contenido previo
            textarea.send_keys(Keys.CONTROL + "a")
            time.sleep(0.2)
            textarea.send_keys(Keys.DELETE)
            time.sleep(0.3)

            # Escribir párrafo por párrafo
            paragraphs = message.split('\n')
            for i, paragraph in enumerate(paragraphs):
                textarea.send_keys(paragraph)
                time.sleep(0.15)  # pausa breve entre líneas
                if i < len(paragraphs) - 1:
                    textarea.send_keys(Keys.SHIFT + Keys.ENTER)
                    time.sleep(0.2)

            # Esperar 1 s para que el botón de enviar se active
            time.sleep(1.0)
            return True
        except Exception as e:
            print(f"[GoogleMessages] Error send_text_message: {e}")
            return False

    def send_message_simple(self) -> bool:
        """
        Envía el mensaje presionando Enter en el textarea.

        Solo hace un chequeo rápido (2 s) de errores inmediatos.
        La espera de confirmación completa la hace check_delivery_status().
        """
        self._last_delivery_status = None

        try:
            textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 'textarea[data-e2e-message-input-box]'
                ))
            )

            # Enviar con Enter
            textarea.send_keys(Keys.RETURN)

            # Ventana rápida (2 s) para detectar errores inmediatos
            deadline = time.time() + 2
            while time.time() < deadline:
                try:
                    failed_els = self.driver.find_elements(
                        By.CSS_SELECTOR, 'span.failed'
                    )
                    for el in failed_els:
                        try:
                            if el.is_displayed():
                                self._last_delivery_status = "Error al enviar"
                                print("[GoogleMessages] ❌ Error inmediato detectado tras envío")
                                return True
                        except Exception:
                            pass
                except Exception:
                    pass
                time.sleep(0.2)

            return True

        except Exception as e:
            print(f"[GoogleMessages] Error send_message_simple: {e}")
            self._last_delivery_status = "Error al enviar"
            return False


    def check_delivery_status(self, timeout: int = 10) -> str:
        """
        Espera la confirmación de entrega tras send_message_simple().

        Sondea hasta `timeout` segundos buscando:
          • [data-e2e-delivered-status-icon] / .delivered-icon
              → "Entregado ✓✓"  (chulitos RCS)
          • span.failed
              → "Error al enviar"  (no se envió)

        Si ninguno aparece antes del timeout devuelve "Enviado"
        (el mensaje partió pero la confirmación de entrega tardó más).

        Selectores basados en el DOM real de Google Messages:
          Éxito : <mws-icon data-e2e-delivered-status-icon class="delivered-icon">
          Error : <span class="failed">No se envió; haz clic para volver a intentarlo</span>
        """
        # Prioridad 1: error ya detectado en send_message_simple()
        if self._last_delivery_status is not None:
            status = self._last_delivery_status
            self._last_delivery_status = None
            return status

        try:
            deadline = time.time() + timeout
            while time.time() < deadline:
                try:
                    # ── Verificar error ────────────────────────────────────
                    failed_els = self.driver.find_elements(
                        By.CSS_SELECTOR, 'span.failed'
                    )
                    for el in failed_els:
                        try:
                            if el.is_displayed():
                                print("[GoogleMessages] ❌ No se envió (span.failed visible)")
                                return "Error al enviar"
                        except Exception:
                            pass

                    # ── Verificar entrega (chulitos dobles) ────────────────
                    # Selector 1: atributo data-e2e
                    delivered = self.driver.find_elements(
                        By.CSS_SELECTOR, '[data-e2e-delivered-status-icon]'
                    )
                    # Selector 2: clase CSS como respaldo
                    if not delivered:
                        delivered = self.driver.find_elements(
                            By.CSS_SELECTOR, 'mws-icon.delivered-icon'
                        )

                    if delivered:
                        try:
                            if delivered[-1].is_displayed():
                                print("[GoogleMessages] ✅ Mensaje entregado (chulitos detectados)")
                                return "Entregado ✓✓"
                        except Exception:
                            pass

                except Exception:
                    pass

                time.sleep(0.4)

            # Timeout: partió pero sin confirmación de entrega aún
            print(f"[GoogleMessages] ⏱ Timeout {timeout}s — mensaje enviado sin confirmar entrega")
            return "Enviado"

        except Exception as e:
            print(f"[GoogleMessages] Error check_delivery_status: {e}")
            return "Enviado"

    def close_chat(self):
        """
        Vuelve a la pantalla principal de Google Messages SIN recargar la página.
        - Si Google Messages ya navegó automáticamente a la lista → solo esperar.
        - Si todavía estamos en la conversación → usar driver.back() (respeta el
          historial del Angular router y no provoca recarga completa).
        """
        try:
            current_url = self.driver.current_url
            in_conversation = (
                '/conversations/' in current_url and
                'conversations/new' not in current_url
            )

            if in_conversation:
                # Usar historial del navegador — sin recarga de página
                self.driver.back()

            # Esperar a que el botón Iniciar chat esté disponible
            WebDriverWait(self.driver, 12).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-e2e-start-button]'))
            )
            time.sleep(0.3)
        except Exception as e:
            print(f"[GoogleMessages] Error close_chat: {e}")

    # ──────────────────────────────────────────────────────────────
    # Stubs de compatibilidad con la interfaz de WhatsAppService
    # (no aplican en Google Messages pero evitan errores si se llaman)
    # ──────────────────────────────────────────────────────────────

    def go_back(self):
        """Vuelve a la pantalla principal (lista de conversaciones)."""
        self.close_chat()

    def handle_connection_error(self):
        """Compatibilidad: vuelve a la pantalla principal."""
        self.close_chat()

    # ──────────────────────────────────────────────────────────────
    # Limpieza
    # ──────────────────────────────────────────────────────────────

    def close(self):
        """Cierra el navegador."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None
                self.wait = None

    def __del__(self):
        """Destructor."""
        self.close()
