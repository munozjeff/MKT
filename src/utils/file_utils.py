"""
Utilidades para manejo de archivos.
"""
import os
import shutil
import pandas as pd


def load_excel(file_path):
    """
    Carga un archivo Excel y extrae información de contactos.
    
    Args:
        file_path (str): Ruta del archivo Excel
        
    Returns:
        tuple: (phone_numbers, user_data_by_phone, contact_data_by_phone)
        
    Raises:
        ValueError: Si el archivo no contiene la columna 'Celular'
        Exception: Si hay error al leer el archivo
    """
    df = pd.read_excel(file_path)
    
    # Verificar si la columna 'Celular' existe
    if 'Celular' not in df.columns:
        raise ValueError("El archivo Excel debe contener una columna 'Celular'")
    
    # Crear listas y diccionarios para almacenar los datos
    valid_phone_numbers = []
    user_data_by_phone = {}
    contact_data_by_phone = {}
    
    for _, row in df.iterrows():
        raw_phone = row['Celular']
        
        # Validar y limpiar número
        if pd.isna(raw_phone):
            continue
            
        # Convertir a string y limpiar posibles decimales .0 de floats
        s_phone = str(raw_phone).strip()
        if s_phone.endswith('.0'):
            s_phone = s_phone[:-2]
            
        # Validar que sea numérico y empiece por 3
        if not s_phone.isdigit() or not s_phone.startswith('3'):
            continue
            
        phone_number = s_phone # Usar el número limpio como clave
        valid_phone_numbers.append(phone_number)
        
        user_data = row.drop(labels=['Celular']).to_dict()
        
        # Filtrar y almacenar las columnas que contienen la palabra "Contacto"
        contact_data = {k: int(v) for k, v in user_data.items() if 'Contacto' in k and pd.notna(v)}
        non_contact_data = {k: v for k, v in user_data.items() if 'Contacto' not in k}
        
        user_data_by_phone[phone_number] = non_contact_data
        contact_data_by_phone[phone_number] = contact_data
    
    return valid_phone_numbers, user_data_by_phone, contact_data_by_phone


def verify_pdf_file(folder, filename):
    """
    Verifica si un archivo PDF existe en una carpeta.
    
    Args:
        folder (str): Ruta de la carpeta
        filename (str): Nombre del archivo
        
    Returns:
        str: Ruta completa del archivo si existe, cadena vacía si no
    """
    # Asegurarse de que el nombre del archivo incluye la extensión .pdf
    if not filename.endswith('.pdf'):
        return ""

    # Combinar la ruta y el nombre del archivo
    ruta_completa = os.path.join(folder, filename)
    
    # Verificar si el archivo existe
    if os.path.isfile(ruta_completa):
        return ruta_completa
    else:
        return ""


def copy_image(source_path, destination_dir, filename=None):
    """
    Copia una imagen a un directorio de destino.
    
    Args:
        source_path (str): Ruta de la imagen original
        destination_dir (str): Directorio de destino
        filename (str, optional): Nombre del archivo destino. Si es None, usa el nombre original
        
    Returns:
        str: Ruta absoluta de la imagen copiada
    """
    ensure_directory(destination_dir)
    
    if filename is None:
        filename = os.path.basename(source_path)
    
    destination_path = os.path.join(destination_dir, filename)
    
    # Copiar la imagen si no existe
    if not os.path.exists(destination_path):
        shutil.copyfile(source_path, destination_path)
    
    # Convertir la ruta en absoluta y normalizada
    return os.path.abspath(destination_path).replace("\\", "/")


def ensure_directory(path):
    """
    Asegura que un directorio existe, creándolo si es necesario.
    
    Args:
        path (str): Ruta del directorio
    """
    os.makedirs(path, exist_ok=True)


def get_absolute_path(relative_path):
    """
    Convierte una ruta relativa en absoluta.
    
    Args:
        relative_path (str): Ruta relativa
        
    Returns:
        str: Ruta absoluta normalizada
    """
    return os.path.abspath(relative_path).replace("\\", "/")
