from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time, random, unicodedata

# ================= CONFIG =================
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=options)
driver.get("https://web.whatsapp.com")
wait = WebDriverWait(driver, 20)

MI_CONTACTO = "3217166019"  # 👈 TU NÚMERO

print("⏳ Esperando login...")

WebDriverWait(driver, 300).until(
    EC.presence_of_element_located((By.ID, "pane-side"))
)
print("✅ Sesión iniciada")


# ================= SANITIZAR TEXTO =================
def sanitize_text(text):
    return ''.join(c for c in text if unicodedata.category(c)[0] != "C")


# ================= FILTRO NO LEIDOS =================
def get_filter_btn():
    return driver.find_element(By.ID, "unread-filter")

def is_filter_active():
    return get_filter_btn().get_attribute("aria-pressed") == "true"

def activate_filter():
    if not is_filter_active():
        print("⚪ Activando filtro NO LEÍDOS...")
        btn = get_filter_btn()
        ActionChains(driver).move_to_element(btn).pause(0.3).click().perform()
        WebDriverWait(driver, 10).until(lambda d: is_filter_active())
        print("✅ Filtro activado")
    else:
        print("✅ Filtro ya activo")


# ================= BUSCAR CHATS =================
def get_unread_chats():
    return driver.find_elements(
        By.XPATH,
        "//div[@aria-label='Lista de chats']//div[@role='row']"
    )


# ================= EXTRAER INFO CHAT =================
def get_chat_info(chat):
    def safe(xpath):
        try:
            return sanitize_text(chat.find_element(By.XPATH, xpath).text)
        except:
            return ""

    # Intentar obtener el badge de mensajes no leídos
    unread_count = ""
    try:
        # Buscar el badge con el número de mensajes no leídos
        badge_selectors = [
            ".//span[@data-testid='icon-unread-count']",
            ".//span[contains(@aria-label, 'no leído')]",
            ".//div[contains(@class,'x1rg5ohu')]//span[@dir='ltr']",
            ".//span[contains(@class,'x1c4vz4f')]"
        ]
        for selector in badge_selectors:
            try:
                badge = chat.find_element(By.XPATH, selector)
                if badge and badge.text.strip():
                    unread_count = badge.text.strip()
                    break
            except:
                continue
    except:
        pass

    return {
        "name": safe(".//span[@dir='auto'][@title]"),
        "time": safe(".//span[contains(@class,'x140p0ai')]"),
        "preview": safe(".//span[contains(@title,'‪')]"),
        "unread_count": unread_count
    }


# ================= ENVIAR MENSAJE =================
def send_text_message(message):
    try:
        message = sanitize_text(message)

        parent = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div._ak1q, div._ak1r")))
        box = parent.find_element(By.CSS_SELECTOR, 'p.copyable-text.x15bjb6t.x1n2onr6')

        box.send_keys(Keys.CONTROL + "a")
        box.send_keys(Keys.DELETE)

        for p in message.split("\n"):
            box.send_keys(p)
            box.send_keys(Keys.SHIFT + Keys.ENTER)

        box.send_keys(Keys.ENTER)
        return True
    except Exception as e:
        print("❌ Error send msg:", e)
        return False


# ================= NUEVO CHAT UI =================
def click_new_chat():
    try:
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.3)
    except:
        pass

    try:
        btn = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "[title='Nuevo chat'], [aria-label='Nuevo chat']")
        ))
        btn.click()
        time.sleep(0.5)
    except:
        btn = driver.find_element(By.XPATH, "//span[@data-icon='new-chat-outline']/ancestor::button[1]")
        btn.click()
        time.sleep(0.5)


def search_contact(phone):
    try:
        field = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//p[contains(@class,"copyable-text")]')
        ))
        field.send_keys(Keys.CONTROL + "a")
        field.send_keys(Keys.DELETE)
        field.send_keys(phone)
        time.sleep(1)
        return True
    except Exception as e:
        print("Error buscar contacto:", e)
        return False


def open_chat():
    try:
        field = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//p[contains(@class,"copyable-text")]')
        ))
        field.send_keys(Keys.ENTER)
        return True
    except Exception as e:
        print("Error abrir chat:", e)
        return False


# ================= CHECK CONTACT EXISTS =================
def check_contact_exists():
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='listitem']"))
        )
        return True, True, "Encontrado en lista"
    except:
        return True, False, "No visible en lista"


# ================= VERIFICAR CHAT ABIERTO =================
def is_chat_open():
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div._ak1q, div._ak1r"))
        )
        return True
    except:
        return False


# ================= BASE GLOBAL =================
# Diccionario: key = nombre del chat, value = ultimo estado procesado (preview + time + count)
GLOBAL_DB = {}


# ================= LOOP PRINCIPAL =================
while True:
    try:
        activate_filter()

        chats = get_unread_chats()
        nuevos_ciclo = []

        if not chats:
            print("🟢 No hay chats nuevos")
        else:
            print(f"🔴 Chats detectados: {len(chats)}")

            for chat in chats:
                info = get_chat_info(chat)
                chat_name = info["name"]
                
                # Crear identificador del estado actual (preview + time + unread_count)
                current_state = f"{info['preview']}|{info['time']}|{info['unread_count']}"
                
                # Verificar si este chat tiene un estado diferente al último procesado
                last_state = GLOBAL_DB.get(chat_name, None)
                
                is_new = (last_state is None or last_state != current_state)
                
                # CLICK PARA MARCAR LEÍDO
                ActionChains(driver).move_to_element(chat).pause(random.uniform(0.2, 0.5)).click().perform()
                time.sleep(random.uniform(1, 2))

                if not is_new:
                    print(f"⏭️ Chat '{chat_name}' ya procesado con el mismo estado")
                    continue

                # Actualizar el estado en la base de datos
                GLOBAL_DB[chat_name] = current_state
                nuevos_ciclo.append(info)

                print(f"🆕 NUEVO MENSAJE en chat: {chat_name}")
                print(f"   Estado anterior: {last_state}")
                print(f"   Estado actual: {current_state}")

                send_text_message("Te contactaré pronto...")

        # ================= ENVIAR REPORTE A TU NUMERO =================
        if nuevos_ciclo:
            print(f"📨 Enviando reporte a MI_CONTACTO: {len(nuevos_ciclo)} chats")

            click_new_chat()
            search_contact(MI_CONTACTO)

            ok, exists, reason = check_contact_exists()
            print(f"DEBUG contacto: ok={ok}, exists={exists}, reason={reason}")

            # abrir chat aunque no lo detecte (WA abre directo)
            open_chat()

            if not is_chat_open():
                print("❌ No se pudo abrir chat con MI_CONTACTO")
                continue

            print("✅ Chat MI_CONTACTO abierto")

            for chat in nuevos_ciclo:
                msg = f"""Nuevo chat detectado:
Nombre: {chat['name']}
Hora: {chat['time']}
Preview: {chat['preview']}"""

                send_text_message(msg)
                time.sleep(random.uniform(1, 2))

        time.sleep(5)

    except Exception as e:
        print("❌ ERROR LOOP:", e)
        time.sleep(5)
