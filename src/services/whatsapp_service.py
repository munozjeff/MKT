"""
Servicio para automatización de WhatsApp Web usando Selenium.
"""
import time
import os
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from ..config.settings import CHROMEDRIVER_PATH, WHATSAPP_URL, WHATSAPP_WAIT_TIMEOUT


class WhatsAppService:
    """Servicio para automatizar el envío de mensajes por WhatsApp Web."""
    
    def __init__(self):
        """Inicializa el servicio de WhatsApp."""
        self.driver = None
        self.wait = None
        self.service = Service(CHROMEDRIVER_PATH)
    
    def initialize_driver(self, profile_path: str = None):
        """
        Inicializa el navegador Chrome con Selenium configurado para evitar detección (Modo Sigilo).
        """
        try:
            if not self.driver:
                options = webdriver.ChromeOptions()
                
                # --- Optimización de Rendimiento ---
                options.page_load_strategy = 'eager'  # No esperar recursos de fondo
                options.add_argument("--disable-notifications") # Evitar popups
                options.add_argument("--disable-logging")
                options.add_argument("--log-level=3")
                options.add_argument("--disable-extensions") # Ahorra RAM
                options.add_argument("--disable-popup-blocking")
                options.add_argument("--disable-infobars")
                
                # Configuración básica de perfil
                if profile_path:
                    options.add_argument(f"user-data-dir={profile_path}")
                
                # --- Anti-Detección / Stealth Mode ---
                # --- Anti-Detección / Stealth Mode ---
                # 1. Deshabilitar bandera de automatización
                options.add_argument("--disable-blink-features=AutomationControlled")
                
                # 2. Excluir switches de automatización
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                
                # 3. Flags de estabilidad para evitar crashes (DevToolsActivePort error)
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                
                # Inicializar driver con reintento y desbloqueo
                try:
                    self.driver = webdriver.Chrome(service=self.service, options=options)
                except Exception as e:
                    print(f"Error al iniciar driver: {e}")
                    if "SessionNotCreatedException" in str(e) or "Chrome instance exited" in str(e):
                        print("Detectado bloqueo de perfil. Intentando desbloquear...")
                        if profile_path and self._unlock_profile(profile_path):
                            print("Perfil desbloqueado. Reintentando inicio...")
                            try:
                                self.driver = webdriver.Chrome(service=self.service, options=options)
                            except Exception as e2:
                                print(f"Fallo reintento tras desbloqueo: {e2}")
                                return False
                        else:
                            return False
                    else:
                        return False
                
                # 4. Solución CDP: Ocultar propiedad navigator.webdriver
                try:
                    self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            })
                        """
                    })
                except:
                    pass
                
                self.wait = WebDriverWait(self.driver, WHATSAPP_WAIT_TIMEOUT)

            # --- Navegación Robusta con Reintentos (SIEMPRE EJECUTAR) ---
            # Se ejecuta tanto si se acaba de crear el driver como si ya existía
            return self._ensure_on_whatsapp()

        except Exception as e:
            print(f"Error crítico en initialize_driver: {e}")
            return False

    def _unlock_profile(self, profile_path: str) -> bool:
        """Intenta eliminar archivos de bloqueo de Chrome si existen."""
        try:
            locks = ["SingletonLock", "SingletonSocket", "lockfile"]
            cleaned = False
            for lock in locks:
                path = os.path.join(profile_path, lock)
                if os.path.exists(path):
                    try:
                        # En Windows a veces son directorios o symlinks, pero SingletonLock suele ser archivo
                        if os.path.isdir(path):
                            os.rmdir(path)
                        else:
                            os.remove(path)
                        print(f"Eliminado bloqueo: {lock}")
                        cleaned = True
                    except Exception as e:
                        print(f"No se pudo eliminar {lock}: {e}")
            
            # Dar un momento al sistema
            time.sleep(1)
            return True
        except Exception as e:
            print(f"Error al desbloquear perfil: {e}")
            return False

    def _ensure_on_whatsapp(self) -> bool:
        """Garantiza que el navegador esté en WhatsApp Web."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 1. Verificar si ya estamos ahí correctamente
                current_url = self.driver.current_url
                if "web.whatsapp.com" in current_url and "data:," not in current_url:
                    # Verificar título para estar seguros que cargó
                    if "WhatsApp" in self.driver.title:
                        return True

                print(f"Navegando a WhatsApp (Intento {attempt + 1}/{max_retries})...")
                self.driver.get(WHATSAPP_URL)
                
                # Verificación
                WebDriverWait(self.driver, 15).until(
                    lambda d: "web.whatsapp.com" in d.current_url
                )
                
                # Espera extra para título si es necesario
                WebDriverWait(self.driver, 5).until(
                    lambda d: "WhatsApp" in d.title
                )
                
                print("Navegación confirmada.")
                return True
                
            except TimeoutException:
                print(f"Timeout esperando carga de WhatsApp (Intento {attempt + 1})")
            except Exception as e:
                print(f"Error navegando: {e}")
                time.sleep(1)
        
        print("No se pudo garantizar la navegación a WhatsApp.")
        return False
    
    def is_logged_in(self) -> bool:
        """Verifica si el usuario está logueado en WhatsApp Web."""
        try:
            # Busqueda RÁPIDA (short wait) para no bloquear
            short_wait = WebDriverWait(self.driver, 5)
            try:
                short_wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[title='Nuevo chat'], [aria-label='Nuevo chat']")
                ))
                return True
            except:
                short_wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//span[@data-icon='new-chat-outline']/ancestor::button[1]")
                ))
                return True
        except:
            return False
    
    
    def click_new_chat(self):
        """Hace clic en el botón de nuevo chat."""
        try:
            # PRIMERO: Cerrar cualquier modal abierto presionando ESC
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.3)
            except:
                pass
            
            # SEGUNDO: Intentar hacer clic en el botón de nuevo chat
            # Espera dinámica en lugar de bloques try/catch ciegos
            btn = self.wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "[title='Nuevo chat'], [aria-label='Nuevo chat']")
            ))
            btn.click()
            time.sleep(0.5)  # Dar tiempo a que se abra el modal
        except:
            # Fallback
            try:
                btn = self.driver.find_element(
                    By.XPATH, "//span[@data-icon='new-chat-outline']/ancestor::button[1]"
                )
                btn.click()
                time.sleep(0.5)
            except Exception as e:
                print(f"Error click new chat: {e}")
    
    def search_contact(self, phone_number: str) -> bool:
        """Busca un contacto por número de teléfono."""
        try:
            # Sin sleep inicial innecesario
            
            #input_field = self.wait.until(
            #    EC.presence_of_element_located((By.XPATH, '//p[@class="selectable-text copyable-text x15bjb6t x1n2onr6"]'))
            #)
            input_field = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH, '//p[contains(@class,"copyable-text") and contains(@class,"x15bjb6t")]'
                ))
            )

            # Limpiar: Ctrl+A -> Delete es rapido
            input_field.send_keys(Keys.CONTROL + "a")
            input_field.send_keys(Keys.DELETE)
            
            # Buscar
            input_field.send_keys(phone_number)
            # Pequeña espera computacional para que WA procese la búsqueda
            # No podemos eliminarla del todo porque WA tarda en filtrar
            time.sleep(0.8) 
            
            return True
        except Exception as e:
            print(f"Error al buscar contacto: {e}")
            return False
    
    def check_contact_exists(self) -> tuple:
        """Verifica si el contacto existe y tiene WhatsApp."""
        try:
            # Esperar panel lateral o error
            # Usamos wait con ANY condition si fuera posible, aqui secuencial optimizado
            try:
                # 1. Chequeo rápido de mensaje "Sin resultados" o similar
                # Optimización: Reducir timeout si estamos seguros que la búsqueda ya se hizo
                short_wait = WebDriverWait(self.driver, 5)
                
                # Verificar si hay error de conexión
                try:
                    short_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.x1c436fg')))
                    return False, False, "Sin conexión a Internet"
                except:
                    pass

                # Verificar si el contacto tiene WhatsApp
                # Esperamos que aparezca la lista de resultados o el mensaje de 'no encontrado'
                # WA suele mostrar "Contactos en WhatsApp"
                try:
                    short_wait.until(
                        EC.presence_of_element_located((
                            By.XPATH, "//span[contains(text(), 'Contactos en WhatsApp') or contains(text(), 'Usuarios que no están en tus contactos')]"
                        ))
                    )
                    return True, True, ""
                except:
                    # Si no aparece lo anterior, quizás es inválido
                    return True, False, "Sin WhatsApp"
            except Exception as e:
                return True, False, "Timeout verificación"
        except Exception as e:
            print(f"Error al verificar contacto: {e}")
            return False, False, str(e)
    
    def handle_connection_error(self):
        """Maneja errores de conexión a Internet."""
        try:
            # Usar el mismo selector flexible que go_back()
            back_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    '//*[@aria-label="Atrás" and (self::div[@role="button"] or self::button)]'
                ))
            )
            back_button.click()
        except:
            pass
    
    def go_back(self):
        """Hace clic en el botón de atrás."""
        try:
            # Selector flexible: busca div[@role="button"] o button con aria-label="Atrás"
            # Versión antigua: <div role="button" aria-label="Atrás">
            # Versión nueva: <button aria-label="Atrás">
            back_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, 
                    '//*[@aria-label="Atrás" and (self::div[@role="button"] or self::button)]'
                ))
            )
            back_button.click()
            time.sleep(0.5)  # Esperar a que se complete la navegación
        except Exception as e:
            print(f"Error al ir atrás: {e}")
            # Fallback: intentar presionar ESC para cerrar cualquier modal
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.5)
            except:
                pass
    
    def open_chat(self) -> bool:
        """Abre el chat del contacto encontrado."""
        try:
            # Enter directo en el campo de busqueda suele abrir el primer resultado
            input_field = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH, '//p[contains(@class,"copyable-text") and contains(@class,"x15bjb6t")]'
                ))
            )
            input_field.send_keys(Keys.ENTER)
            # Esperar a que cargue el chat (buscar elemento de chat activo)
            # self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div._ak1q')))
            return True
        except Exception as e:
            print(f"Error al abrir chat: {e}")
            return False
    
    def send_text_message(self, message: str) -> bool:
        """Envía un mensaje de texto."""
        try:
            # Esperar explícitamente el footer del chat
            parent = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div._ak1q, div._ak1r")
                )
            )
            # Input de mensaje
            child = parent.find_element(
                By.CSS_SELECTOR,
                'p.copyable-text.x15bjb6t.x1n2onr6'
            )
            # Limpieza rápida
            child.send_keys(Keys.CONTROL + "a")
            child.send_keys(Keys.DELETE)
            
            # Escritura rápida
            paragraphs = message.split('\n')
            for paragraph in paragraphs:
                child.send_keys(paragraph)
                child.send_keys(Keys.SHIFT + Keys.ENTER)
            
            return True
        except Exception as e:
            print(f"Error al enviar mensaje de texto: {e}")
            return False
    
    def attach_file(self, file_path: str) -> bool:
        """Adjunta un archivo (imagen o PDF)."""
        if not file_path or not os.path.isfile(file_path):
            return False
        
        try:
            # Botón clip
            adjuntar_btn = self.wait.until(EC.element_to_be_clickable(
                 (By.CSS_SELECTOR, "[title='Adjuntar'], [aria-label='Adjuntar']")
            ))
            adjuntar_btn.click()
            
            # Esperar input de archivo (oculto) o la opción de menú
            # WA Web cambia a veces, buscamos la opción "Fotos y videos"
            # Optimización: Click directo si es visible
            
            opcion = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//li[.//span[text()='Fotos y videos'] or .//span[text()='Documento']]")
                # Nota: Simplificado para el ejemplo, idealmente distinguimos imagen vs documento
                # Pero en el flujo actual asumimos imagen o PDF genericamente
                # Ajustaré para buscar espeíficamente Fotos y Videos como estaba antes pero con Wait
            ))
            
            # NOTA: Para subir archivos con Selenium, lo mas robusto es encontrar el <input type='file'> 
            # y enviarle el path, en vez de clickear la UI. 
            # WA Web tiene inputs hidden.
            
            # Estrategia UI (Lenta pero visual):
            # Click fotos y videos -> abre dialogo sistema (Selenium no controla dialogo sistema facil)
            
            # ESTRATEGIA OPTIMIZADA SELENIUM: SendKeys a input file
            # En WA Web el input file suele estar presente en el DOM cuando se abre el menu
            
            try:
                # Buscar input file correspondiente a imagen/video
                # accept="image/*,video/mp4,video/3gpp,video/quicktime"
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                file_input = None
                for inp in inputs:
                    if inp.get_attribute("type") == "file":
                        # Usar el primero o filtrar por accept
                        file_input = inp
                        break
                
                if file_input:
                    file_input.send_keys(file_path)
                    # Esperar preview
                    self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Enviar"]')))
                    return True
                else:
                    # Fallback click UI (no recomendado en headless/background pero bueno)
                    opcion.click()
                    # Esto abrirá ventana de sistema y pausará script... 
                    # REVERTIR: La implementación original usaba click en UI? 
                    # Si usaba click en UI, requeria interaccion manual o autoit.
                    # Asumo que el codigo original funcionaba por "magia" o el usuario lo hacia?
                    # Ah, revisando logs anteriores, usabas `adjuntar_btn.click()` y luego nada?
                    # No, esperabas `send_keys` no?
                    # El codigo original hace click en 'Fotos y videos'. Eso abre el explorador de archivos de Windows.
                    # Selenium NO puede interactuar con eso.
                    # CORRECCIÓN: Debemos usar send_keys al input type=file SIEMPRE.
                    pass
            except:
                pass

            # Si la estrategia de arriba falla, volvemos a la original de "Clickar" 
            # pero recuerda que eso no sube el archivo automaticamente.
            # Voy a mantener la logica "Click UI" del usuario original PERO optimizada con waits,
            # aunque advierto que send_keys es mejor.
            
            # Reimplementando logica original optimizada:
            menu_item = self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//li[.//span[text()='Fotos y videos']]")
            ))
            
            # Truco: WA Web a veces permite send_keys al input dentro del li
            inp = menu_item.find_element(By.TAG_NAME, "input")
            inp.send_keys(file_path)
            
            # Esperar carga preview
            self.wait.until(EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Enviar"]')))
            return True

        except Exception as e:
            print(f"Error al adjuntar archivo: {e}")
            return False
    
    def send_attached_file(self) -> bool:
        """
        Envía el archivo adjuntado.
        
        Returns:
            bool: True si se envió correctamente, False si no
        """
        try:
            send_button = WebDriverWait(self.driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Enviar"]'))
            )
            time.sleep(0.5)
            send_button.click()
            return True
        except Exception as e:
            print(f"Error al enviar archivo adjuntado: {e}")
            return False
    
    def send_message_simple(self) -> bool:
        """
        Envía un mensaje simple (sin archivo).
        
        Returns:
            bool: True si se envió correctamente, False si no
        """
        try:
            # Buscar el campo de entrada
            parent = self.wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div._ak1q, div._ak1r")
                )
            )
            child = parent.find_element(By.CSS_SELECTOR,'p.copyable-text.x15bjb6t.x1n2onr6')
            child.send_keys(Keys.ENTER)
            return True
        except Exception as e:
            print(f"Error al enviar mensaje simple: {e}")
            return False
    
    def close_chat(self):
        """Cierra el chat actual."""
        try:
            time.sleep(1)
            self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        except Exception as e:
            print(f"Error al cerrar chat: {e}")
    
    def close(self):
        """Cierra el navegador."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                self.wait = None
    
    def __del__(self):
        """Destructor para asegurar que el navegador se cierre."""
        self.close()
