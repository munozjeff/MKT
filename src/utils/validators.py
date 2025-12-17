"""
Validadores de entrada de datos.
"""
import re


def validate_phone(phone):
    """
    Valida un número de teléfono.
    
    Args:
        phone (str): Número de teléfono a validar
        
    Returns:
        bool: True si es válido, False si no
    """
    if not phone or not isinstance(phone, (str, int)):
        return False
    
    phone_str = str(phone).strip()
    
    # Verificar que solo contenga dígitos (y opcionalmente +)
    if not re.match(r'^[\d+]+$', phone_str):
        return False
    
    # Verificar longitud mínima
    if len(phone_str.replace('+', '')) < 7:
        return False
    
    return True


def validate_interval(interval, min_value=20):
    """
    Valida un intervalo de tiempo.
    
    Args:
        interval: Valor del intervalo (puede ser str o int)
        min_value (int): Valor mínimo permitido
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not interval:
        return False, "El intervalo no puede estar vacío"
    
    # Convertir a string para validar
    interval_str = str(interval).strip()
    
    if not interval_str.isdigit():
        return False, "El intervalo debe ser un número entero"
    
    interval_int = int(interval_str)
    
    if interval_int < min_value:
        return False, f"El intervalo debe ser mayor a {min_value} segundos"
    
    return True, ""


def validate_campaign_data(title, message):
    """
    Valida los datos de una campaña.
    
    Args:
        title (str): Título de la campaña
        message (str): Mensaje de la campaña
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "El título de la campaña no puede estar vacío"
    
    if not message or not message.strip():
        return False, "El mensaje de la campaña no puede estar vacío"
    
    return True, ""


def validate_contact_data(phone, name):
    """
    Valida los datos de un contacto.
    
    Args:
        phone (str): Número de teléfono
        name (str): Nombre del contacto
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not phone or not phone.strip():
        return False, "El número de teléfono no puede estar vacío"
    
    if not validate_phone(phone):
        return False, "El número de teléfono no es válido"
    
    if not name or not name.strip():
        return False, "El nombre no puede estar vacío"
    
    return True, ""


def validate_send_config(interval, pause, campaign_type, campaign_title, message_type):
    """
    Valida la configuración de envío de mensajes.
    
    Args:
        interval (str): Intervalo entre mensajes
        pause (str): Pausa después de lote
        campaign_type (str): Tipo de campaña
        campaign_title (str): Título de campaña
        message_type (str): Tipo de mensaje
        
    Returns:
        tuple: (is_valid, error_message)
    """
    # Validar que todos los campos estén completos
    if not interval or not pause or not message_type or not campaign_type:
        return False, "Por favor completa todos los campos en el menú de configuración"
    
    # Validar que interval y pause sean números enteros
    if not interval.isdigit() or not pause.isdigit():
        return False, "Por favor ingresa valores numéricos válidos para la duración y la pausa"
    
    # Validar intervalo mínimo
    is_valid, error_msg = validate_interval(interval)
    if not is_valid:
        return False, error_msg
    
    # Validar que se haya seleccionado una campaña si no es Default
    if campaign_type != "Default" and not campaign_title:
        return False, "Por favor selecciona una campaña"
    
    return True, ""
