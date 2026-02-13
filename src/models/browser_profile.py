"""
Modelo de datos para perfiles de navegador.
"""
from dataclasses import dataclass, field
import os
import json
from typing import List
from ..config.settings import PROFILES_DIR

@dataclass
class BrowserProfile:
    """Representa un perfil de navegador persistente."""
    
    name: str
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Cargar metadatos al inicializar."""
        self.load_metadata()

    @property
    def path(self) -> str:
        """
        Obtiene la ruta absoluta del directorio del perfil.
        
        Returns:
            str: Ruta del directorio de datos del usuario
        """
        return os.path.join(PROFILES_DIR, self.name)
    
    @property
    def metadata_path(self) -> str:
        """Ruta del archivo de metadatos."""
        return os.path.join(self.path, "metadata.json")

    def exists(self) -> bool:
        """
        Verifica si el directorio del perfil ya existe.
        
        Returns:
            bool: True si existe
        """
        return os.path.exists(self.path)

    def load_metadata(self):
        """Carga los metadatos desde el archivo json."""
        if not self.exists() or not os.path.exists(self.metadata_path):
            return
            
        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tags = data.get('tags', [])
        except Exception as e:
            print(f"Error cargando metadatos para {self.name}: {e}")

    def save_metadata(self):
        """Guarda los metadatos en el archivo json."""
        if not self.exists():
            return
            
        data = {
            'tags': self.tags
        }
        
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando metadatos para {self.name}: {e}")

    def add_tag(self, tag: str):
        """Añade una etiqueta si no existe."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.save_metadata()

    def remove_tag(self, tag: str):
        """Elimina una etiqueta si existe."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.save_metadata()

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if not isinstance(other, BrowserProfile):
            return False
        return self.name == other.name
