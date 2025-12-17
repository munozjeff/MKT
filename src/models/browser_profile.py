"""
Modelo de datos para perfiles de navegador.
"""
from dataclasses import dataclass
import os
from ..config.settings import PROFILES_DIR

@dataclass
class BrowserProfile:
    """Representa un perfil de navegador persistente."""
    
    name: str
    
    @property
    def path(self) -> str:
        """
        Obtiene la ruta absoluta del directorio del perfil.
        
        Returns:
            str: Ruta del directorio de datos del usuario
        """
        return os.path.join(PROFILES_DIR, self.name)
    
    def exists(self) -> bool:
        """
        Verifica si el directorio del perfil ya existe.
        
        Returns:
            bool: True si existe
        """
        return os.path.exists(self.path)

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, BrowserProfile):
            return False
        return self.name == other.name
