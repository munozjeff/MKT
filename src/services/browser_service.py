"""
Servicio para gestión de perfiles de navegador y control de concurrencia.
"""
import os
import shutil
from typing import List, Set
from ..models.browser_profile import BrowserProfile
from ..config.settings import PROFILES_DIR, ensure_directories

class BrowserService:
    """
    Gestiona los perfiles de navegador (creación, eliminación) 
    y su estado de ejecución (ocupado/libre).
    """
    
    _instance = None
    _active_profiles: Set[str] = set()
    
    def __new__(cls):
        """Patrón Singleton para mantener el estado de los perfiles activos."""
        if cls._instance is None:
            cls._instance = super(BrowserService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicialización interna."""
        ensure_directories()
    
    def get_all_profiles(self) -> List[BrowserProfile]:
        """
        Obtiene todos los perfiles existentes en el disco.
        
        Returns:
            List[BrowserProfile]: Lista de perfiles ordenados por nombre
        """
        if not os.path.exists(PROFILES_DIR):
            return []
            
        profiles = []
        for name in os.listdir(PROFILES_DIR):
            full_path = os.path.join(PROFILES_DIR, name)
            if os.path.isdir(full_path):
                profiles.append(BrowserProfile(name=name))
        
        return sorted(profiles, key=lambda p: p.name)
    
    def get_available_profiles(self) -> List[BrowserProfile]:
        """
        Obtiene solo los perfiles que no están actualmente en uso.
        
        Returns:
            List[BrowserProfile]: Lista de perfiles libres
        """
        all_profiles = self.get_all_profiles()
        return [p for p in all_profiles if p.name not in self._active_profiles]
    
    def create_profile(self, name: str) -> bool:
        """
        Crea un nuevo perfil de navegador.
        
        Args:
            name (str): Nombre del nuevo perfil
            
        Returns:
            bool: True si se creó, False si ya existe o error
        """
        if not name or not name.strip():
            return False
            
        profile = BrowserProfile(name=name.strip())
        if profile.exists():
            return False
            
        try:
            os.makedirs(profile.path)
            return True
        except Exception as e:
            print(f"Error creando perfil {name}: {e}")
            return False
    
    def delete_profile(self, name: str) -> bool:
        """
        Elimina un perfil existente.
        
        Args:
            name (str): Nombre del perfil a eliminar
            
        Returns:
            bool: True si se eliminó, False si está en uso o error
        """
        if self.is_profile_active(name):
            return False
            
        profile = BrowserProfile(name=name)
        if not profile.exists():
            return False
            
        try:
            shutil.rmtree(profile.path)
            return True
        except Exception as e:
            print(f"Error eliminando perfil {name}: {e}")
            return False
    
    def lock_profile(self, name: str) -> bool:
        """
        Marca un perfil como ocupado.
        
        Args:
            name (str): Nombre del perfil
            
        Returns:
            bool: True si se pudo bloquear, False si ya estaba ocupado
        """
        if name in self._active_profiles:
            return False
        self._active_profiles.add(name)
        return True
    
    def unlock_profile(self, name: str):
        """
        Libera un perfil ocupado.
        
        Args:
            name (str): Nombre del perfil
        """
        if name in self._active_profiles:
            self._active_profiles.remove(name)
            
    def is_profile_active(self, name: str) -> bool:
        """
        Verifica si un perfil está actualmente en uso.
        
        Args:
            name (str): Nombre del perfil
            
        Returns:
            bool: True si está ocupado
        """
        return name in self._active_profiles
