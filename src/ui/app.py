"""
Ventana principal de la aplicación.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from .styles import *
from .components.contacts_view import ContactsView
from .components.campaigns_view import CampaignsView
from .components.browsers_view import BrowsersView
from .components.send_view import SendView
from .components.update_dialog import UpdateDialog, UpdateProgressDialog
from ..services.update_service import UpdateService
import os

class App(tk.Tk):
    """Clase principal de la aplicación."""
    
    def __init__(self):
        super().__init__()
        self.title("Sistema de Marketing WhatsApp Pro")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # Inicializar servicio de actualización
        version_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "version.json"
        )
        self.update_service = UpdateService(version_file)
        
        # Configurar estilos
        self.style = ttk.Style()
        self.style.theme_use('clam') # Un tema más limpio que default
        
        self.setup_ui()
        
        # Verificar actualizaciones al inicio (después de un pequeño delay)
        self.after(2000, self.check_for_updates_silent)
        
    def setup_ui(self):
        """Configura el layout principal."""
        # Contenedor principal
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Sidebar
        self.sidebar = ttk.Frame(main_container, width=SIDEBAR_WIDTH, relief=tk.RAISED)
        self.sidebar.pack(fill=tk.Y, side=tk.LEFT)
        self.sidebar.pack_propagate(False) # Mantener ancho fijo
        
        # Área de contenido
        self.content_area = ttk.Frame(main_container)
        self.content_area.pack(fill=tk.BOTH, expand=True, side=tk.RIGHT)
        
        # Botones del menú
        self.create_sidebar_button("Contactos", self.show_contacts)
        self.create_sidebar_button("Campañas", self.show_campaigns)
        self.create_sidebar_button("Navegadores", self.show_browsers)
        ttk.Separator(self.sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10)
        self.create_sidebar_button("ENVIAR MENSAJES", self.show_send, style="Accent.TButton")
        
        # Separador y botón de actualización al final
        ttk.Separator(self.sidebar, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=5, pady=10, side=tk.BOTTOM)
        
        # Info de versión y botón actualizar
        version_frame = ttk.Frame(self.sidebar)
        version_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        lbl_version = ttk.Label(
            version_frame,
            text=f"v{self.update_service.get_current_version()}",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        lbl_version.pack()
        
        btn_update = ttk.Button(
            version_frame,
            text="Buscar Actualizaciones",
            command=self.check_for_updates_manual
        )
        btn_update.pack(fill=tk.X, pady=5)
        
        # Mostrar vista inicial
        self.show_send()
        
    def create_sidebar_button(self, text, command, style=None):
        """Helper para botones del sidebar."""
        btn = ttk.Button(self.sidebar, text=text, command=command)
        btn.pack(fill=tk.X, padx=5, pady=5)
        return btn
        
    def clear_content(self):
        """Limpia el área de contenido."""
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
    def show_contacts(self):
        self.clear_content()
        ContactsView(self.content_area).pack(fill=tk.BOTH, expand=True)
        
    def show_campaigns(self):
        self.clear_content()
        CampaignsView(self.content_area).pack(fill=tk.BOTH, expand=True)
        
    def show_browsers(self):
        self.clear_content()
        BrowsersView(self.content_area).pack(fill=tk.BOTH, expand=True)
        
    def show_send(self):
        self.clear_content()
        SendView(self.content_area).pack(fill=tk.BOTH, expand=True)
    
    # ========== MÉTODOS DE ACTUALIZACIÓN ==========
    
    def check_for_updates_silent(self):
        """Verifica actualizaciones en segundo plano al iniciar."""
        import threading
        
        def _check_thread():
            try:
                has_update, update_info = self.update_service.check_for_updates()
                if has_update:
                    # Programar la UI en el hilo principal
                    self.after(0, lambda: self._show_update_dialog(update_info))
            except Exception as e:
                print(f"Error checking updates: {e}")

        # Iniciar verificación en hilo separado
        threading.Thread(target=_check_thread, daemon=True).start()

    def check_for_updates_manual(self):
        """Verifica actualizaciones manualmente (botón)."""
        import threading
        
        # Feedback visual inmediato
        messagebox.showinfo("Buscando...", "Verificando actualizaciones...")
        
        def _check_thread():
            try:
                has_update, update_info = self.update_service.check_for_updates()
                # Volver al hilo principal para mostrar resultados
                self.after(0, lambda: self._handle_manual_check_result(has_update, update_info))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Error verificando: {e}"))

        threading.Thread(target=_check_thread, daemon=True).start()

    def _handle_manual_check_result(self, has_update, update_info):
        """Maneja el resultado de la verificación manual en el hilo principal."""
        if has_update:
            self._show_update_dialog(update_info)
        else:
            messagebox.showinfo(
                "Sin Actualizaciones",
                f"Estás usando la última versión ({self.update_service.get_current_version()})"
            )

    def _show_update_dialog(self, update_info):
        """Muestra el diálogo de actualización y maneja la respuesta."""
        dialog = UpdateDialog(self, update_info)
        self.wait_window(dialog)
        
        if dialog.result:
            # Si el usuario aceptó, iniciar proceso de actualización
            self.perform_update(update_info)

    def perform_update(self, update_info):
        """Ejecuta el proceso de actualización con barra de progreso."""
        import threading
        
        # Diálogo de progreso (modal)
        progress_dialog = UpdateProgressDialog(self)
        
        def _update_progress(value):
            # Actualizar UI en hilo principal
            self.after(0, lambda: progress_dialog.update_progress(value, f"Descargando... {value}%"))

        def _install_thread():
            try:
                # 1. Descargar
                self.after(0, lambda: progress_dialog.update_progress(0, "Iniciando descarga..."))
                
                success = self.update_service.download_update(
                    update_info, 
                    progress_callback=_update_progress
                )
                
                if not success:
                    self.after(0, lambda: self._on_update_error(progress_dialog, "Error en la descarga"))
                    return

                # 2. Instalar
                self.after(0, lambda: progress_dialog.update_progress(100, "Instalando..."))
                
                if self.update_service.install_update():
                    self.after(0, lambda: self._on_update_success(progress_dialog))
                else:
                    self.after(0, lambda: self._on_update_error(progress_dialog, "Error en la instalación"))
                    
            except Exception as e:
                self.after(0, lambda: self._on_update_error(progress_dialog, str(e)))
            finally:
                self.update_service.cleanup()

        # Iniciar thread de instalación
        threading.Thread(target=_install_thread, daemon=True).start()

    def _on_update_success(self, progress_dialog):
        """Maneja el éxito de la actualización."""
        progress_dialog.destroy()
        messagebox.showinfo(
            "¡Actualización Lista!",
            "La aplicación se ha actualizado correctamente.\nSe reiniciará ahora."
        )
        self.update_service.restart_application()

    def _on_update_error(self, progress_dialog, message):
        """Maneja errores de actualización."""
        progress_dialog.destroy()
        messagebox.showerror("Error de Actualización", message)

