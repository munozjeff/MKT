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

    def rename_profile_with_phone(self, current_name: str, phone_number: str) -> tuple[bool, str]:
        """
        Renombra un perfil usando el número de teléfono como prefijo.

        Regla de renombrado:
          - Solo actúa si el nombre actual contiene '_' (guion bajo).
          - Reemplaza el texto que está ANTES del primer '_' con el número de teléfono.
          - Ejemplo: 'perfil_15'      → '+57 321 7166019_15'
          - Ejemplo: 'perfil_1_2'     → '+57 321 7166019_1_2'
          - Si no hay '_' en el nombre, omite el renombrado (retorna False).
          - Si el nuevo nombre ya existe en disco, también omite (retorna False).

        El perfil puede estar en uso (activo). En ese caso se actualiza el registro
        de perfiles activos en memoria para que el unlock posterior no falle.

        Args:
            current_name (str): Nombre actual del perfil.
            phone_number (str): Número de teléfono extraído de WhatsApp.

        Returns:
            tuple[bool, str]: (éxito, nuevo_nombre_o_mensaje_de_error)
        """
        import os
        import re

        # --- Validaciones previas ---
        phone_clean = phone_number.strip() if phone_number else ""
        if not phone_clean:
            return False, "Número de teléfono vacío."

        if '_' not in current_name:
            return False, f"El perfil '{current_name}' no contiene '_', se omite renombrado."

        # Construir nuevo nombre: reemplazar solo lo que está antes del primer '_'
        underscore_idx = current_name.index('_')
        suffix = current_name[underscore_idx:]          # e.g. "_15" o "_1_2"
        new_name = f"{phone_clean}{suffix}"             # e.g. "+57 321 7166019_15"

        if new_name == current_name:
            return False, f"El nombre nuevo '{new_name}' es igual al actual, sin cambios."

        old_path = os.path.join(PROFILES_DIR, current_name)
        new_path = os.path.join(PROFILES_DIR, new_name)

        if not os.path.exists(old_path):
            return False, f"Directorio del perfil '{current_name}' no encontrado."

        if os.path.exists(new_path):
            return False, f"Ya existe un perfil con el nombre '{new_name}'."

        # --- Renombrar directorio ---
        try:
            os.rename(old_path, new_path)
            print(f"[RenombrePerfil] '{current_name}' → '{new_name}' (directorio renombrado)")
        except Exception as e:
            return False, f"Error al renombrar directorio: {e}"

        # --- Actualizar registro de activos en memoria (si estaba activo) ---
        if current_name in self._active_profiles:
            self._active_profiles.discard(current_name)
            self._active_profiles.add(new_name)
            print(f"[RenombrePerfil] Registro de activos actualizado: '{current_name}' → '{new_name}'")

        return True, new_name
