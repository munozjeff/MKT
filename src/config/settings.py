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

# Tipos de base
BASE_TYPE_ORIGINAL = "Original"
BASE_TYPE_CON_INTERVALOS = "Con Intervalos"


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
