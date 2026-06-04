"""
Configuración global de la aplicación MKT.
Contiene rutas, constantes y configuraciones del sistema.
"""
import os

# Directorio base del proyecto
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Rutas de directorios
DATA_DIR = os.path.join(BASE_DIR, "data")
CAMPAIGNS_DIR = os.path.join(DATA_DIR, "campañas")
IMAGES_DIR = os.path.join(DATA_DIR, "imagenes")
PROFILES_DIR = os.path.join(DATA_DIR, "perfiles")
REPORTS_DIR = os.path.join(BASE_DIR, "informes")

# Rutas de archivos
CONTACTS_FILE = os.path.join(DATA_DIR, "contactos.json")
CAMPAIGNS_FILE = os.path.join(CAMPAIGNS_DIR, "campaigns.json")
CUSTOM_CAMPAIGNS_FILE = os.path.join(CAMPAIGNS_DIR, "custom_campaign.json")

# Configuración de ChromeDriver
CHROMEDRIVER_PATH = os.path.join(BASE_DIR, "chromedriver.exe")

# Configuración de WhatsApp
WHATSAPP_URL = "https://web.whatsapp.com"
WHATSAPP_WAIT_TIMEOUT = 60  # segundos

# Configuración de Google Messages (SMS)
GOOGLE_MESSAGES_URL = "https://messages.google.com/web/authentication?hl=es-419"
GOOGLE_MESSAGES_WAIT_TIMEOUT = 60  # segundos

# Canales de envío
CHANNEL_WHATSAPP = "WhatsApp"
CHANNEL_SMS = "SMS (Google Messages)"

# Configuración de envío
MIN_INTERVAL = 20  # segundos mínimos entre mensajes
MIN_INTERVAL_ANTI_SPAM = 30  # segundos mínimos para modo anti-spam
PAUSE_AFTER_BATCH = 60  # segundos de pausa después de un lote
PAUSE_ANTI_SPAM = 120  # segundos de pausa en modo anti-spam

# Configuración de UI
WINDOW_TITLE = "Aplicación de Envío de Mensajes"
WINDOW_SIZE = "1000x600"
SIDEBAR_WIDTH = 200

# Tipos de campaña
CAMPAIGN_TYPE_PREDETERMINADA = "Predeterminada"
CAMPAIGN_TYPE_PERSONALIZADA = "Personalizada"
CAMPAIGN_TYPE_DEFAULT = "Default"

# Tipos de mensaje
MESSAGE_TYPE_SIMPLE = "Simple"
MESSAGE_TYPE_FACTURAS = "Facturas"
MESSAGE_TYPE_ANTI_SPAM = "Anti Spam"
MESSAGE_TYPE_HUMAN_SIM = "Simulador Humano"


# Tipos de base
BASE_TYPE_ORIGINAL = "Original"
BASE_TYPE_CON_INTERVALOS = "Con Intervalos"


# ── Simulador Humano: valores por defecto ─────────────────────────────────────
HUMAN_SIM_MSGS_PER_WINDOW   = 7      # mensajes maximos por ventana de tiempo
HUMAN_SIM_WINDOW_MINUTES    = 10     # duracion de la ventana (minutos)
HUMAN_SIM_TYPING_MIN_MS     = 40     # ms minimo entre caracteres
HUMAN_SIM_TYPING_MAX_MS     = 150    # ms maximo entre caracteres
HUMAN_SIM_TYPO_CHANCE       = 5      # porcentaje de errores tipograficos
HUMAN_SIM_LONG_PAUSE_EVERY  = 15     # pausa larga cada N mensajes
HUMAN_SIM_LONG_PAUSE_MIN_S  = 120    # duracion minima de pausa larga (segundos)
HUMAN_SIM_LONG_PAUSE_MAX_S  = 420    # duracion maxima de pausa larga (segundos)
HUMAN_SIM_WARMUP            = True   # calentar sesion al inicio
HUMAN_SIM_ACTIVE_START      = "07:00" # hora inicio del horario activo
HUMAN_SIM_ACTIVE_END        = "21:00" # hora fin del horario activo
HUMAN_SIM_USE_SCHEDULE      = False  # respetar horario activo



def ensure_directories():
    """Asegura que todos los directorios necesarios existan."""
    directories = [
        DATA_DIR,
        CAMPAIGNS_DIR,
        IMAGES_DIR,
        PROFILES_DIR,
        REPORTS_DIR
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def get_report_filename():
    """Genera un nombre de archivo único para el informe."""
    from datetime import datetime
    now = datetime.now()
    fecha_formateada = now.strftime("%Y%m%d_%H%M%S")
    return f"Informe_{fecha_formateada}.xlsx"


def get_report_path():
    """Genera la ruta completa para un nuevo informe."""
    ensure_directories()
    return os.path.join(REPORTS_DIR, get_report_filename())
