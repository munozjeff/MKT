"""
Modelo de datos para contactos.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Contact:
    """Representa un contacto en el sistema."""
    
    telefono: str
    nombre: str
    
    def to_dict(self):
        """
        Convierte el contacto a un diccionario.
        
        Returns:
            dict: Diccionario con los datos del contacto
        """
        return {
            "telefono": self.telefono,
            "nombre": self.nombre
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Crea un contacto desde un diccionario.
        
        Args:
            data (dict): Diccionario con los datos del contacto
            
        Returns:
            Contact: Instancia de Contact
        """
        return cls(
            telefono=data.get("telefono", ""),
            nombre=data.get("nombre", "")
        )
    
    def __str__(self):
        """Representación en string del contacto."""
        return f"{self.nombre} ({self.telefono})"
    
    def __eq__(self, other):
        """Compara dos contactos por su número de teléfono."""
        if not isinstance(other, Contact):
            return False
        return self.telefono == other.telefono
