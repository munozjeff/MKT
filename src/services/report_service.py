"""
Servicio para generación de informes.
"""
import os
import threading
from datetime import datetime
import pandas as pd
from typing import List, Dict
from ..config.settings import get_report_path, REPORTS_DIR, ensure_directories


class ReportService:
    """Servicio para generar informes de envío."""
    
    def __init__(self):
        """Inicializa el servicio de informes."""
        self.current_report = []
        self.lock = threading.Lock()
    
    def add_entry(self, numero: str, estado: str):
        """
        Agrega una entrada al informe actual (Thread-safe).
        
        Args:
            numero (str): Número de teléfono
            estado (str): Estado del envío ("Enviado", "Sin whatsapp", etc.)
        """
        with self.lock:
            self.current_report.append({
                "Numero": numero,
                "Estado": estado
            })
    
    def clear_report(self):
        """Limpia el informe actual (Thread-safe)."""
        with self.lock:
            self.current_report = []
    
    def get_report_data(self) -> List[Dict]:
        """
        Obtiene los datos del informe actual.
        
        Returns:
            List[Dict]: Lista de entradas del informe
        """
        return self.current_report.copy()
    
    def save_report(self, report_data: List[Dict] = None, filename_prefix: str = None) -> str:
        """
        Guarda el informe en un archivo Excel.
        
        Args:
            report_data (List[Dict], optional): Datos del informe. Si es None, usa el informe actual
            filename_prefix (str, optional): Prefijo para el nombre del archivo
            
        Returns:
            str: Ruta del archivo guardado
        """
        if report_data is None:
            report_data = self.current_report
        
        # Convertir a DataFrame
        df = pd.DataFrame(report_data)
        
        # Obtener ruta del archivo
        if filename_prefix:
            ensure_directories()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.xlsx"
            report_path = os.path.join(REPORTS_DIR, filename)
        else:
            report_path = get_report_path()
        
        # Guardar el archivo
        df.to_excel(report_path, index=False)
        
        return report_path
    
    def get_failed_numbers(self, phone_list: List[str]) -> List[str]:
        """
        Obtiene los números que no están en el informe (no se enviaron).
        
        Args:
            phone_list (List[str]): Lista completa de números que se intentaron enviar
            
        Returns:
            List[str]: Lista de números que no se enviaron
        """
        # Extraer números del informe
        sent_numbers = {entry["Numero"] for entry in self.current_report if "Numero" in entry}
        
        # Encontrar números que no están en el informe
        failed_numbers = [phone for phone in phone_list if phone not in sent_numbers]
        
        return failed_numbers
    
    def get_success_count(self) -> int:
        """
        Obtiene la cantidad de mensajes enviados exitosamente.
        
        Returns:
            int: Cantidad de mensajes enviados
        """
        return sum(1 for entry in self.current_report if entry.get("Estado") == "Enviado")
    
    def get_failed_count(self) -> int:
        """
        Obtiene la cantidad de mensajes que fallaron.
        
        Returns:
            int: Cantidad de mensajes fallidos
        """
        return sum(1 for entry in self.current_report if entry.get("Estado") != "Enviado")
    
    def get_total_count(self) -> int:
        """
        Obtiene el total de intentos de envío.
        
        Returns:
            int: Total de intentos
        """
        return len(self.current_report)
