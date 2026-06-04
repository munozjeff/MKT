"""
Simulador de comportamiento humano para automatizacion de WhatsApp.
Provee utilidades para escritura, clics, pausas y fingerprinting
que imitan la interaccion de un usuario real.
"""
import time
import random
import math
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiter: ventana deslizante de mensajes
# ─────────────────────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Controla la velocidad de envio usando una ventana de tiempo deslizante.
    Ejemplo: max 7 mensajes cada 10 minutos, distribuidos aleatoriamente.
    """

    def __init__(self, max_msgs: int, window_minutes: int):
        self.max_msgs = max_msgs
        self.window_seconds = window_minutes * 60
        self._timestamps = []  # lista de timestamps de envios recientes

    def registrar_envio(self):
        """Registra el timestamp del envio actual."""
        now = time.time()
        self._timestamps.append(now)
        # Limpiar timestamps viejos fuera de la ventana
        self._timestamps = [t for t in self._timestamps if now - t <= self.window_seconds]

    def _timestamps_en_ventana(self):
        now = time.time()
        return [t for t in self._timestamps if now - t <= self.window_seconds]

    def tiempo_hasta_siguiente(self) -> float:
        """
        Calcula cuantos segundos esperar antes del proximo envio.
        Si la ventana esta llena, espera hasta que salga el mas antiguo.
        Si hay espacio, distribuye aleatoriamente el slot dentro del tiempo restante.
        """
        ahora = time.time()
        en_ventana = self._timestamps_en_ventana()

        if len(en_ventana) >= self.max_msgs:
            # Ventana llena: esperar hasta que el mas antiguo expire + offset
            mas_antiguo = min(en_ventana)
            expira_en = (mas_antiguo + self.window_seconds) - ahora
            espera = max(1.0, expira_en) + random.uniform(2, 20)
            print(
                f"[RateLimiter] {len(en_ventana)}/{self.max_msgs} msgs en ventana. "
                f"Esperando {espera:.0f}s para proximo envio."
            )
            return espera
        else:
            # Hay espacio: distribuir el envio aleatoriamente dentro del tiempo restante
            slots_restantes = self.max_msgs - len(en_ventana)
            if en_ventana:
                # Tiempo restante de la ventana actual (desde el mas reciente)
                mas_reciente = max(en_ventana)
                tiempo_restante = self.window_seconds - (ahora - mas_reciente)
                tiempo_restante = max(5.0, tiempo_restante)
            else:
                tiempo_restante = self.window_seconds

            # Distribuir el slot aleatoriamente en el tiempo disponible
            fraccion = tiempo_restante / max(slots_restantes, 1)
            espera = random.uniform(fraccion * 0.3, fraccion * 0.9)
            espera = max(5.0, espera)
            print(
                f"[RateLimiter] {len(en_ventana)}/{self.max_msgs} msgs en ventana. "
                f"Proximo en {espera:.0f}s (distribucion aleatoria)."
            )
            return espera

    def puede_enviar(self) -> bool:
        return len(self._timestamps_en_ventana()) < self.max_msgs


# ─────────────────────────────────────────────────────────────────────────────
# HumanSimulator: acciones que imitan comportamiento humano
# ─────────────────────────────────────────────────────────────────────────────

class HumanSimulator:
    """
    Clase principal del simulador humano.
    Envuelve las interacciones de Selenium con comportamiento natural.
    """

    def __init__(self, driver, config: dict):
        """
        Args:
            driver: instancia de Selenium WebDriver
            config: diccionario con parametros del simulador (human_sim subdict)
        """
        self.driver = driver
        self.cfg = config
        self._msgs_enviados = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Fingerprint injection
    # ─────────────────────────────────────────────────────────────────────────

    def inyectar_fingerprints(self):
        """
        Inyecta propiedades falsas del navegador via CDP para reducir
        la deteccion como bot. Se llama UNA VEZ antes de cargar WhatsApp.
        """
        script = """
        // Ocultar navigator.webdriver (ya hecho en initialize_driver, pero reforzamos)
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

        // Plugins falsos (Chrome real tiene varios)
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                var PluginArray = function() {};
                PluginArray.prototype = {
                    length: 3,
                    item: function(i) { return this[i]; },
                    namedItem: function(n) { return null; },
                    refresh: function() {}
                };
                var arr = new PluginArray();
                arr[0] = { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format', length: 1 };
                arr[1] = { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '', length: 1 };
                arr[2] = { name: 'Native Client', filename: 'internal-nacl-plugin', description: '', length: 2 };
                return arr;
            }
        });

        // Idiomas naturales (Colombia)
        Object.defineProperty(navigator, 'languages', {
            get: () => ['es-CO', 'es', 'en-US', 'en']
        });

        // Plataforma Windows
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32'
        });

        // Objeto window.chrome (Chrome real lo tiene)
        if (!window.chrome) {
            Object.defineProperty(window, 'chrome', {
                value: { runtime: {}, loadTimes: function(){}, csi: function(){}, app: {} },
                writable: true, enumerable: true, configurable: false
            });
        }

        // Hardware concurrency realista
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8
        });

        // Memoria del dispositivo
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8
        });

        // Profundidad de color
        Object.defineProperty(screen, 'colorDepth', {
            get: () => 24
        });

        // Ocultar automation en Chrome permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) =>
            parameters.name === 'notifications'
                ? Promise.resolve({ state: Notification.permission })
                : originalQuery(parameters);
        """
        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": script}
            )
            print("[Fingerprint] Fingerprints anti-deteccion inyectados correctamente.")
        except Exception as e:
            print(f"[Fingerprint] Advertencia: no se pudo inyectar fingerprints: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Warm-up: calentamiento de sesion
    # ─────────────────────────────────────────────────────────────────────────

    def calentar_sesion(self):
        """
        Simula actividad inicial antes de empezar a enviar:
        scrolls lentos en la lista de chats y movimientos de mouse.
        """
        if not self.cfg.get("warmup", True):
            return

        print("[HumanSim] Calentando sesion (warm-up)...")
        try:
            from selenium.webdriver.common.action_chains import ActionChains

            # Scroll aleatorio en la lista de chats
            scrolls = random.randint(3, 5)
            for i in range(scrolls):
                try:
                    chat_list = self.driver.find_element(
                        "css selector", "div#pane-side"
                    )
                    delta = random.randint(80, 250)
                    direccion = random.choice([1, -1])
                    self.driver.execute_script(
                        f"arguments[0].scrollTop += {delta * direccion};", chat_list
                    )
                    print(f"[HumanSim] Scroll warm-up {i+1}/{scrolls}")
                    time.sleep(random.uniform(0.8, 2.5))
                except Exception:
                    time.sleep(random.uniform(0.5, 1.5))

            # Movimientos de mouse aleatorios
            pasos = random.randint(2, 4)
            for _ in range(pasos):
                try:
                    w = self.driver.execute_script("return window.innerWidth;")
                    h = self.driver.execute_script("return window.innerHeight;")
                    x = random.randint(50, max(51, w - 50))
                    y = random.randint(50, max(51, h - 50))
                    ActionChains(self.driver).move_by_offset(0, 0).move_by_offset(
                        random.randint(-20, 20), random.randint(-20, 20)
                    ).perform()
                    time.sleep(random.uniform(0.4, 1.2))
                except Exception:
                    time.sleep(0.5)

            print("[HumanSim] Warm-up completado.")
        except Exception as e:
            print(f"[HumanSim] Warm-up parcial (no critico): {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Escritura humana
    # ─────────────────────────────────────────────────────────────────────────

    def escribir_como_humano(self, elemento, texto: str):
        """
        Escribe texto caracter a caracter con delays variables,
        errores tipograficos ocasionales y pausas de 'pensar'.
        """
        from selenium.webdriver.common.keys import Keys

        typing_min = self.cfg.get("typing_min_ms", 40) / 1000.0
        typing_max = self.cfg.get("typing_max_ms", 150) / 1000.0
        typo_chance = self.cfg.get("typo_chance", 5) / 100.0

        # Pausa de "lectura" antes de empezar a escribir
        time.sleep(random.uniform(0.2, 0.7))
        elemento.click()
        time.sleep(random.uniform(0.1, 0.3))

        # Teclado QWERTY: vecinos de cada tecla para errores realistas
        vecinos = {
            'a': 'sq', 'b': 'vn', 'c': 'xv', 'd': 'sf', 'e': 'wr',
            'f': 'dg', 'g': 'fh', 'h': 'gj', 'i': 'uo', 'j': 'hk',
            'k': 'jl', 'l': 'k', 'm': 'n', 'n': 'bm', 'o': 'ip',
            'p': 'o', 'q': 'wa', 'r': 'et', 's': 'ad', 't': 'ry',
            'u': 'yi', 'v': 'cb', 'w': 'qe', 'x': 'zc', 'y': 'tu',
            'z': 'x',
        }

        i = 0
        while i < len(texto):
            char = texto[i]

            # Pausa larga a mitad del texto (simula pensar)
            if i == len(texto) // 2 and len(texto) > 20:
                if random.random() < 0.3:
                    pausa_mid = random.uniform(0.8, 2.5)
                    time.sleep(pausa_mid)

            # Generar error tipografico
            if char.isalpha() and random.random() < typo_chance:
                char_lower = char.lower()
                posibles = vecinos.get(char_lower, "")
                if posibles:
                    error_char = random.choice(posibles)
                    if char.isupper():
                        error_char = error_char.upper()
                    elemento.send_keys(error_char)
                    time.sleep(random.uniform(0.15, 0.45))
                    # "Se da cuenta" del error y lo borra
                    elemento.send_keys(Keys.BACKSPACE)
                    time.sleep(random.uniform(0.10, 0.30))

            # Escribir el caracter correcto
            elemento.send_keys(char)
            delay = random.uniform(typing_min, typing_max)

            # Aceleración en palabras cortas, desaceleración en largas
            if char == ' ':
                delay *= random.uniform(0.8, 1.5)

            time.sleep(delay)
            i += 1

    # ─────────────────────────────────────────────────────────────────────────
    # Clic humano
    # ─────────────────────────────────────────────────────────────────────────

    def clic_humano(self, elemento):
        """
        Simula un clic humano: mueve el mouse hacia el elemento con
        trayectoria suavizada, hace hover, luego clic con offset aleatorio.
        """
        from selenium.webdriver.common.action_chains import ActionChains

        try:
            # Offset aleatorio del centro del elemento
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-4, 4)

            ac = ActionChains(self.driver)

            # Movimiento intermedio (simula trayectoria no recta)
            ac.move_to_element(elemento)
            ac.move_by_offset(
                random.randint(-8, 8),
                random.randint(-4, 4)
            )
            ac.pause(random.uniform(0.08, 0.25))  # hover antes de clic
            ac.move_to_element_with_offset(elemento, offset_x, offset_y)
            ac.pause(random.uniform(0.05, 0.15))
            ac.click()
            ac.perform()

        except Exception:
            # Fallback al clic normal
            try:
                elemento.click()
            except Exception as e:
                print(f"[HumanSim] Error en clic_humano: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Micro-pausa
    # ─────────────────────────────────────────────────────────────────────────

    def micro_pausa(self):
        """Pausa corta aleatoria entre acciones (tiempo de reaccion humano)."""
        time.sleep(random.uniform(0.15, 0.60))

    # ─────────────────────────────────────────────────────────────────────────
    # Pausa larga
    # ─────────────────────────────────────────────────────────────────────────

    def pausa_larga_si_toca(self):
        """
        Aplica una pausa larga cada N mensajes (simula descanso o distraccion).
        Retorna True si se aplico la pausa.
        """
        self._msgs_enviados += 1
        every = self.cfg.get("long_pause_every", 15)
        if every > 0 and self._msgs_enviados % every == 0:
            min_s = self.cfg.get("long_pause_min_s", 120)
            max_s = self.cfg.get("long_pause_max_s", 420)
            duracion = random.uniform(min_s, max_s)
            mins = duracion / 60
            print(f"[HumanSim] Pausa larga: {mins:.1f} min (simulando descanso tras {self._msgs_enviados} mensajes)")
            time.sleep(duracion)
            return True
        return False

    # ─────────────────────────────────────────────────────────────────────────
    # Scroll idle
    # ─────────────────────────────────────────────────────────────────────────

    def scroll_idle(self, segundos: float = 3.0):
        """
        Realiza scrolls lentos en la lista de chats durante el intervalo
        de espera entre mensajes, simulando que el usuario revisa chats.
        """
        try:
            chat_list = self.driver.find_element("css selector", "div#pane-side")
            scrolls = random.randint(1, 3)
            tiempo_por_scroll = segundos / max(scrolls, 1)
            for _ in range(scrolls):
                delta = random.randint(30, 120)
                direction = random.choice([1, -1])
                self.driver.execute_script(
                    f"arguments[0].scrollTop += {delta * direction};", chat_list
                )
                time.sleep(min(tiempo_por_scroll, random.uniform(0.5, 1.5)))
        except Exception:
            time.sleep(min(segundos, 2.0))

    # ─────────────────────────────────────────────────────────────────────────
    # Verificacion de horario activo
    # ─────────────────────────────────────────────────────────────────────────

    def esperar_si_fuera_horario(self) -> bool:
        """
        Si el horario activo esta habilitado y la hora actual esta fuera del
        rango, duerme en ciclos de 60s hasta que sea hora de trabajar.
        Retorna True si tuvo que esperar.
        """
        if not self.cfg.get("use_schedule", False):
            return False

        start_str = self.cfg.get("active_start", "07:00")
        end_str   = self.cfg.get("active_end",   "21:00")

        try:
            sh, sm = map(int, start_str.split(":"))
            eh, em = map(int, end_str.split(":"))
        except Exception:
            return False

        now = datetime.now()
        start_min = sh * 60 + sm
        end_min   = eh * 60 + em
        cur_min   = now.hour * 60 + now.minute

        if start_min <= cur_min <= end_min:
            return False

        # Fuera de horario
        print(f"[HumanSim] Fuera de horario activo ({start_str}-{end_str}). Esperando...")
        while True:
            now = datetime.now()
            cur_min = now.hour * 60 + now.minute
            if start_min <= cur_min <= end_min:
                print("[HumanSim] Dentro del horario activo. Reanudando envio.")
                return True
            time.sleep(60)

    # ─────────────────────────────────────────────────────────────────────────
    # Metodos compartidos para usar desde cualquier runner
    # ─────────────────────────────────────────────────────────────────────────

    def buscar_contacto_humano(self, service, phone: str) -> bool:
        """
        Busca un contacto en el campo de busqueda de WhatsApp usando tipeo humano.
        Funciona en modo 'Nuevo Chat' (p editable) y barra lateral (input html).
        Retorna True si tuvo exito.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.keys import Keys

        try:
            short_wait = WebDriverWait(service.driver, 10)
            input_field = short_wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    '//p[contains(@class,"copyable-text") and contains(@class,"x15bjb6t")]'
                    ' | //input[@data-tab="3" and contains(@class,"html-input")]'
                ))
            )
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.DELETE)
            self.micro_pausa()
            self.escribir_como_humano(input_field, phone)
            time.sleep(random.uniform(0.6, 1.2))
            return True
        except Exception as e:
            print(f"[HumanSim] Error buscando contacto: {e}")
            return False

    def enviar_mensaje_humano(self, service, message_text: str):
        """
        Escribe y envia un mensaje en el chat abierto usando tipeo humano.

        IMPORTANTE: usa driver.switch_to.active_element para cada send_keys
        posterior al primer clic, porque WhatsApp Web recrea el nodo <p>
        del contenteditable tras cada SHIFT+ENTER, dejando obsoleta cualquier
        referencia directa al input_box (StaleElementReferenceException).
        """
        from selenium.webdriver.common.keys import Keys

        # 1. Obtener el input box y hacer UN SOLO clic para enfocarlo
        input_box = service._get_message_input_box()
        if not input_box:
            raise Exception("[HumanSim] No se encontro el input de mensaje")

        input_box.click()
        input_box.send_keys(Keys.CONTROL + "a")
        input_box.send_keys(Keys.DELETE)
        self.micro_pausa()

        # 2. Escribir caracter a caracter usando active_element
        #    (siempre apunta al elemento enfocado actual, nunca queda obsoleto)
        typing_min = self.cfg.get("typing_min_ms", 40) / 1000.0
        typing_max = self.cfg.get("typing_max_ms", 150) / 1000.0
        typo_chance = self.cfg.get("typo_chance", 5) / 100.0

        vecinos = {
            'a': 'sq', 'b': 'vn', 'c': 'xv', 'd': 'sf', 'e': 'wr',
            'f': 'dg', 'g': 'fh', 'h': 'gj', 'i': 'uo', 'j': 'hk',
            'k': 'jl', 'l': 'k', 'm': 'n', 'n': 'bm', 'o': 'ip',
            'p': 'o', 'q': 'wa', 'r': 'et', 's': 'ad', 't': 'ry',
            'u': 'yi', 'v': 'cb', 'w': 'qe', 'x': 'zc', 'y': 'tu',
            'z': 'x',
        }

        chars = list(message_text)
        total = len(chars)

        for idx, char in enumerate(chars):
            # Pausa pensativa a mitad del texto
            if idx == total // 2 and total > 20:
                if random.random() < 0.3:
                    time.sleep(random.uniform(0.8, 2.5))

            if char == '\n':
                # Salto de linea dentro del mensaje: SHIFT+ENTER
                # NO usar input_box (puede estar obsoleto tras el SHIFT+ENTER anterior)
                service.driver.switch_to.active_element.send_keys(Keys.SHIFT + Keys.ENTER)
                time.sleep(random.uniform(0.10, 0.28))
                continue

            # Error tipografico ocasional
            if char.isalpha() and random.random() < typo_chance:
                char_lower = char.lower()
                posibles = vecinos.get(char_lower, "")
                if posibles:
                    error_char = random.choice(posibles)
                    if char.isupper():
                        error_char = error_char.upper()
                    service.driver.switch_to.active_element.send_keys(error_char)
                    time.sleep(random.uniform(0.15, 0.45))
                    service.driver.switch_to.active_element.send_keys(Keys.BACKSPACE)
                    time.sleep(random.uniform(0.10, 0.30))

            # Caracter correcto
            service.driver.switch_to.active_element.send_keys(char)
            delay = random.uniform(typing_min, typing_max)
            if char == ' ':
                delay *= random.uniform(0.8, 1.5)
            time.sleep(delay)

        # 3. Pausa final (simula revision del mensaje) y ENTER para enviar
        time.sleep(random.uniform(0.4, 1.2))
        service.driver.switch_to.active_element.send_keys(Keys.ENTER)
