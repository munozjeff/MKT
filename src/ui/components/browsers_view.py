"""
Vista para gestión de perfiles de navegador.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from ...services.browser_service import BrowserService
from ...services.whatsapp_service import WhatsAppService
from ..styles import *


class BrowsersView(ttk.Frame):
    """Vista de gestión de perfiles de navegador."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.browser_service = BrowserService()
        self.setup_ui()
        self.load_profiles()
    
    def setup_ui(self):
        """Configura la interfaz gráfica."""
        # Título
        lbl_title = ttk.Label(self, text="Gestión de Navegadores", font=FONT_TITLE)
        lbl_title.pack(pady=PADDING_MEDIUM)
        
        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_LARGE)
        
        # Frame de lista (Izquierda)
        list_frame = ttk.LabelFrame(main_frame, text="Perfiles Disponibles")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING_MEDIUM))
        
        # Tabla de perfiles
        columns = ("Nombre", "Estado", "Ruta")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("Nombre", text="Nombre del Perfil")
        self.tree.heading("Estado", text="Estado")
        self.tree.heading("Ruta", text="Ruta de Datos")
        self.tree.column("Nombre", width=150)
        self.tree.column("Estado", width=100)
        self.tree.column("Ruta", width=250)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame de acciones (Derecha)
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(PADDING_MEDIUM, 0))
        
        # Crear nuevo perfil
        lbl_new = ttk.Label(action_frame, text="Nuevo Perfil:")
        lbl_new.pack(anchor=tk.W, pady=(0, 5))
        
        self.entry_name = ttk.Entry(action_frame)
        self.entry_name.pack(fill=tk.X, pady=(0, 10))
        
        btn_create = ttk.Button(action_frame, text="Crear Perfil", command=self.create_profile)
        btn_create.pack(fill=tk.X, pady=(0, 20))
        
        # Separador
        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Acciones sobre perfil seleccionado
        btn_open = ttk.Button(action_frame, text="Abrir Navegador", command=self.open_profile)
        btn_open.pack(fill=tk.X, pady=5)
        
        btn_delete = ttk.Button(action_frame, text="Eliminar Perfil", command=self.delete_profile)
        btn_delete.pack(fill=tk.X, pady=5)
        
        btn_refresh = ttk.Button(action_frame, text="Actualizar Lista", command=self.load_profiles)
        btn_refresh.pack(fill=tk.X, pady=(20, 5))

    def load_profiles(self):
        """Carga los perfiles en la tabla."""
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        profiles = self.browser_service.get_all_profiles()
        
        for profile in profiles:
            is_active = self.browser_service.is_profile_active(profile.name)
            status = "Ocupado" if is_active else "Disponible"
            
            # Solo mostrar parte final de la ruta para que no sea tan larga
            short_path = "..." + profile.path[-30:] if len(profile.path) > 30 else profile.path
            
            self.tree.insert("", "end", values=(profile.name, status, short_path))
            
    def create_profile(self):
        """Crea un nuevo perfil."""
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showerror(MSG_ERROR, "El nombre no puede estar vacío")
            return
            
        if self.browser_service.create_profile(name):
            messagebox.showinfo(MSG_SUCCESS, f"Perfil '{name}' creado correctamente")
            self.entry_name.delete(0, tk.END)
            self.load_profiles()
        else:
            messagebox.showerror(MSG_ERROR, "No se pudo crear el perfil (¿ya existe?)")
            
    def delete_profile(self):
        """Elimina el perfil seleccionado."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(MSG_WARNING, "Seleccione un perfil para eliminar")
            return
            
        item = self.tree.item(selected[0])
        name = item["values"][0]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar perfil '{name}'?\nSe perderán todos los datos de sesión."):
            if self.browser_service.delete_profile(name):
                messagebox.showinfo(MSG_SUCCESS, "Perfil eliminado")
                self.load_profiles()
            else:
                messagebox.showerror(MSG_ERROR, "No se pudo eliminar el perfil (puede estar en uso)")

    def open_profile(self):
        """Abre el navegador con el perfil seleccionado para configuración manual."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(MSG_WARNING, "Seleccione un perfil para abrir")
            return
            
        item = self.tree.item(selected[0])
        name = item["values"][0]
        
        if self.browser_service.is_profile_active(name):
            messagebox.showwarning(MSG_WARNING, "Este perfil ya está en uso")
            return
            
        # Abrir en hilo separado
        threading.Thread(target=self._run_browser_manual, args=(name,)).start()
        
    def _run_browser_manual(self, profile_name):
        """Ejecuta el navegador manualmente y maneja el bloqueo."""
        if not self.browser_service.lock_profile(profile_name):
            return
            
        try:
            # Actualizar UI en hilo principal
            self.after(0, self.load_profiles)
            
            profiles = self.browser_service.get_all_profiles()
            profile = next((p for p in profiles if p.name == profile_name), None)
            
            if not profile:
                return
                
            service = WhatsAppService()
            if service.initialize_driver(profile.path):
                # Mantener abierto hasta que el usuario lo cierre manualmente
                # En Selenium directo no hay "wait until closed" fácil sin loop, 
                # así que monitoreamos
                while True:
                    time.sleep(1)
                    try:
                        # Verificar si el navegador sigue vivo
                        service.driver.title
                    except:
                        break
            
        except Exception as e:
            print(f"Error abriendo navegador: {e}")
        finally:
            self.browser_service.unlock_profile(profile_name)
            # Actualizar UI
            self.after(0, self.load_profiles)
