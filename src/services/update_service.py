"""
Servicio de actualización automática de la aplicación.
Verifica, descarga e instala actualizaciones desde GitHub.
"""
import os
import sys
import json
import requests
import zipfile
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
import threading
import tempfile


class UpdateService:
    """Servicio para gestionar actualizaciones de la aplicación."""
    
    def __init__(self, version_file: str = None):
        """
        Inicializa el servicio de actualización.
        
        Args:
            version_file: Ruta al archivo version.json
        """
        if version_file is None:
            # Obtener ruta raíz del proyecto
            self.root_dir = Path(__file__).parent.parent.parent
            version_file = self.root_dir / "version.json"
        else:
            self.root_dir = Path(version_file).parent
            
        self.version_file = Path(version_file)
        self.current_version = self._load_version()
        self.temp_dir = Path(tempfile.gettempdir()) / "mkt_update"
        
    def _load_version(self) -> dict:
        """Carga la información de versión actual."""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Versión por defecto si no existe el archivo
                return {
                    "version": "1.0.0",
                    "build": "unknown",
                    "release_date": "unknown"
                }
        except Exception as e:
            print(f"Error cargando versión: {e}")
            return {"version": "1.0.0", "build": "unknown"}
    
    def get_current_version(self) -> str:
        """Retorna la versión actual de la aplicación."""
        return self.current_version.get("version", "1.0.0")
    
    def check_for_updates(self) -> Tuple[bool, Optional[dict]]:
        """
        Verifica si hay actualizaciones disponibles.
        
        Returns:
            Tuple[bool, dict]: (hay_actualización, info_nueva_versión)
        """
        try:
            update_url = self.current_version.get("update_url")
            if not update_url:
                print("No se encontró URL de actualización")
                return False, None
            
            # Descargar información de versión remota
            import time
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            
            # Agregar parámetro para romper caché
            url_parts = list(urlparse(update_url))
            query = parse_qs(url_parts[4])
            query['t'] = [str(int(time.time()))]
            url_parts[4] = urlencode(query, doseq=True)
            no_cache_url = urlunparse(url_parts)
            
            print(f"Checking update from: {no_cache_url}")
            response = requests.get(no_cache_url, timeout=10)
            response.raise_for_status()
            
            remote_version = response.json()
            
            # Comparar versiones
            current = self._parse_version(self.current_version.get("version", "0.0.0"))
            remote = self._parse_version(remote_version.get("version", "0.0.0"))
            
            if remote > current:
                return True, remote_version
            else:
                return False, None
                
        except Exception as e:
            print(f"Error verificando actualizaciones: {e}")
            return False, None
    
    def _parse_version(self, version_str: str) -> tuple:
        """Convierte string de versión a tupla para comparar."""
        try:
            parts = version_str.split('.')
            return tuple(int(p) for p in parts)
        except:
            return (0, 0, 0)
    
    def download_update(self, update_info: dict, progress_callback=None) -> bool:
        """
        Descarga la actualización.
        
        Args:
            update_info: Información de la nueva versión
            progress_callback: Función para reportar progreso (0-100)
            
        Returns:
            bool: True si se descargó exitosamente
        """
        try:
            download_url = update_info.get("download_url")
            if not download_url:
                print("No se encontró URL de descarga")
                return False
            
            # Crear directorio temporal
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            zip_path = self.temp_dir / "update.zip"
            
            # Descargar archivo
            print(f"Descargando actualización desde {download_url}")
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_callback(progress)
            
            print(f"Descarga completada: {zip_path}")
            return True
            
        except Exception as e:
            print(f"Error descargando actualización: {e}")
            return False
    
    def install_update(self) -> bool:
        """
        Instala la actualización descargada.
        
        Returns:
            bool: True si se instaló exitosamente
        """
        # ⚠️ DIRECTOIOS PROTEGIDOS - NUNCA SE SOBRESCRIBEN
        PROTECTED_DIRS = [
            'venv',           # Entorno virtual
            'data',           # Datos en inglés
            'datos',          # Datos en español
            'reports',        # Informes en inglés
            'informes',       # Informes en español
            'profiles',       # Perfiles de navegador en inglés
            'perfiles',       # Perfiles de navegador en español
            '.git',           # Control de versiones
            '__pycache__',    # Cache de Python
            'logs',           # Logs
            'temp',           # Temporales
            'backup',         # Backups anteriores
        ]
        
        # Extensiones de archivos protegidos
        PROTECTED_EXTENSIONS = [
            '.pyc',           # Python compilado
            '.log',           # Archivos de log
            '.db',            # Bases de datos SQLite
            '.sqlite',        # Bases de datos SQLite
        ]
        
        try:
            zip_path = self.temp_dir / "update.zip"
            if not zip_path.exists():
                print("No se encontró archivo de actualización")
                return False
            
            # Extraer actualización
            extract_dir = self.temp_dir / "extracted"
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"Extrayendo actualización...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Encontrar el directorio raíz dentro del zip
            # GitHub suele crear un directorio con el nombre del repo
            subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
            if subdirs:
                source_dir = subdirs[0]
            else:
                source_dir = extract_dir
            
            # Crear backup del directorio actual (sin datos de usuario)
            backup_dir = self.root_dir.parent / f"{self.root_dir.name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            
            print(f"Creando backup en {backup_dir}")
            # Ignorar datos de usuario en el backup también
            backup_ignore = shutil.ignore_patterns(
                '*.pyc', '__pycache__', '.git',
                'venv', 'data', 'datos', 'reports', 'informes', 
                'profiles', 'perfiles', '*.log', '*.db'
            )
            shutil.copytree(self.root_dir, backup_dir, ignore=backup_ignore)
            
            # Preparar patrón de ignorado para la copia
            print(f"Instalando actualización...")
            
            # Función personalizada para verificar si un archivo/directorio debe ignorarse
            def should_ignore(name: str, is_dir: bool = False) -> bool:
                """Verifica si un elemento debe ser ignorado durante la actualización."""
                # Verificar directorios protegidos
                if is_dir and name.lower() in [d.lower() for d in PROTECTED_DIRS]:
                    print(f"  ⚠️  PROTEGIDO: Ignorando directorio '{name}'")
                    return True
                
                # Verificar extensiones protegidas
                if not is_dir:
                    for ext in PROTECTED_EXTENSIONS:
                        if name.endswith(ext):
                            return True
                
                # Verificar patrones especiales
                if name.startswith('.') and name not in ['.gitignore', '.env.example']:
                    return True
                
                if '__pycache__' in name:
                    return True
                
                return False
            
            # Copiar archivos actualizados con validación estricta
            files_updated = 0
            files_skipped = 0
            
            for item in source_dir.iterdir():
                item_name = item.name
                dest = self.root_dir / item_name
                
                # VALIDACIÓN 1: Verificar si el directorio/archivo está protegido
                if should_ignore(item_name, item.is_dir()):
                    files_skipped += 1
                    continue
                
                # VALIDACIÓN 2: Si el directorio de destino existe y está protegido, no tocarlo
                if dest.exists() and dest.is_dir():
                    if dest.name.lower() in [d.lower() for d in PROTECTED_DIRS]:
                        print(f"  ⚠️  PROTEGIDO: No se tocará el directorio existente '{dest.name}'")
                        files_skipped += 1
                        continue
                
                try:
                    if item.is_file():
                        # Copiar archivo individual
                        shutil.copy2(item, dest)
                        files_updated += 1
                        print(f"  ✓ Actualizado: {item_name}")
                    elif item.is_dir():
                        # Para directorios, usar copytree con ignore
                        ignore_func = shutil.ignore_patterns(
                            '*.pyc', '__pycache__', '.git', '*.log', '*.db'
                        )
                        
                        if dest.exists():
                            # Backup del directorio antes de eliminarlo
                            temp_backup = self.temp_dir / f"pre_update_{item_name}"
                            if temp_backup.exists():
                                shutil.rmtree(temp_backup)
                            shutil.move(str(dest), str(temp_backup))
                        
                        shutil.copytree(item, dest, ignore=ignore_func)
                        files_updated += 1
                        print(f"  ✓ Actualizado directorio: {item_name}")
                        
                except Exception as e:
                    print(f"  ✗ Error actualizando {item_name}: {e}")
                    continue
            
            # Actualizar version.json
            new_version_file = source_dir / "version.json"
            if new_version_file.exists():
                shutil.copy2(new_version_file, self.version_file)
                print(f"  ✓ Versión actualizada")
            
            print(f"\n✅ Actualización completada:")
            print(f"   - Archivos actualizados: {files_updated}")
            print(f"   - Archivos protegidos: {files_skipped}")
            print(f"   ⚠️  Directorios protegidos NO tocados: {', '.join(PROTECTED_DIRS[:7])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error instalando actualización: {e}")
            # Restaurar backup si algo falló
            try:
                backup_dir = self.root_dir.parent / f"{self.root_dir.name}_backup"
                if backup_dir.exists():
                    print("🔄 Restaurando backup...")
                    # Eliminar solo lo que no es usuario
                    for item in self.root_dir.iterdir():
                        if item.name.lower() not in [d.lower() for d in PROTECTED_DIRS]:
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                    
                    # Restaurar desde backup
                    for item in backup_dir.iterdir():
                        dest = self.root_dir / item.name
                        if item.is_file():
                            shutil.copy2(item, dest)
                        elif item.is_dir():
                            if dest.exists():
                                shutil.rmtree(dest)
                            shutil.copytree(item, dest)
                    print("✅ Backup restaurado exitosamente")
            except Exception as restore_error:
                print(f"❌ Error restaurando backup: {restore_error}")
            
            return False
    
    def cleanup(self):
        """Limpia archivos temporales de actualización."""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print("Archivos temporales eliminados")
        except Exception as e:
            print(f"Error limpiando temporales: {e}")
    
    def restart_application(self):
        """Reinicia la aplicación después de actualizar."""
        try:
            print("Reiniciando aplicación...")
            
            # Obtener el script principal
            if getattr(sys, 'frozen', False):
                # Si está empaquetado con PyInstaller
                executable = sys.executable
            else:
                # Si se ejecuta con Python
                executable = sys.executable
                script = self.root_dir / "main.py"
                if not script.exists():
                    script = self.root_dir / "app.py"
            
            # Reiniciar
            if getattr(sys, 'frozen', False):
                subprocess.Popen([executable])
            else:
                subprocess.Popen([executable, str(script)])
            
            # Salir de la aplicación actual
            sys.exit(0)
            
        except Exception as e:
            print(f"Error reiniciando aplicación: {e}")
    
    def check_and_update_async(self, on_update_available=None, on_update_complete=None, on_error=None):
        """
        Verifica y actualiza de forma asíncrona.
        
        Args:
            on_update_available: Callback cuando hay actualización (recibe dict con info)
            on_update_complete: Callback cuando se completa
            on_error: Callback en caso de error
        """
        def _update_thread():
            try:
                # Verificar
                has_update, update_info = self.check_for_updates()
                
                if has_update and on_update_available:
                    # Notificar que hay actualización disponible
                    # El callback debería retornar True si el usuario quiere actualizar
                    should_update = on_update_available(update_info)
                    
                    if should_update:
                        # Descargar
                        if self.download_update(update_info):
                            # Instalar
                            if self.install_update():
                                if on_update_complete:
                                    on_update_complete()
                                # Reiniciar
                                self.restart_application()
                            else:
                                if on_error:
                                    on_error("Error instalando actualización")
                        else:
                            if on_error:
                                on_error("Error descargando actualización")
                
            except Exception as e:
                if on_error:
                    on_error(str(e))
            finally:
                self.cleanup()
        
        thread = threading.Thread(target=_update_thread, daemon=True)
        thread.start()
