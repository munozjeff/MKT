"""
Diálogo de actualización para notificar al usuario sobre nuevas versiones.
"""
import tkinter as tk
from tkinter import ttk, messagebox


class UpdateDialog(tk.Toplevel):
    """Ventana de diálogo para notificar actualizaciones."""
    
    def __init__(self, parent, update_info: dict):
        super().__init__(parent)
        
        self.update_info = update_info
        self.result = False  # True si el usuario acepta actualizar
        
        self.setup_ui()
        
        # Hacer modal
        self.transient(parent)
        self.grab_set()
        
        # Centrar en pantalla
        self.center_window()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.title("Actualización Disponible")
        self.geometry("500x300")
        self.resizable(False, False)
        
        # Frame principal
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono y título
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Título
        lbl_title = ttk.Label(
            title_frame,
            text="¡Nueva Versión Disponible!",
            font=("Segoe UI", 14, "bold")
        )
        lbl_title.pack()
        
        # Información de versión
        info_frame = ttk.LabelFrame(main_frame, text="Detalles de la Actualización", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Nueva versión
        lbl_new = ttk.Label(
            info_frame,
            text=f"Nueva Versión: {self.update_info.get('version', 'N/A')}",
            font=("Segoe UI", 10, "bold")
        )
        lbl_new.pack(anchor=tk.W, pady=5)
        
        # Fecha de lanzamiento
        release_date = self.update_info.get('release_date', 'N/A')
        lbl_date = ttk.Label(
            info_frame,
            text=f"Fecha de Lanzamiento: {release_date}"
        )
        lbl_date.pack(anchor=tk.W, pady=2)
        
        # Notas de versión (si existen)
        notes = self.update_info.get('release_notes', '')
        if notes:
            lbl_notes_title = ttk.Label(
                info_frame,
                text="Novedades:",
                font=("Segoe UI", 9, "bold")
            )
            lbl_notes_title.pack(anchor=tk.W, pady=(10, 5))
            
            # Text widget para las notas
            text_notes = tk.Text(
                info_frame,
                height=5,
                wrap=tk.WORD,
                relief=tk.FLAT,
                background="#f0f0f0"
            )
            text_notes.insert("1.0", notes)
            text_notes.config(state=tk.DISABLED)
            text_notes.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Mensaje de advertencia
        lbl_warning = ttk.Label(
            main_frame,
            text="La aplicación se reiniciará después de actualizar.",
            foreground="gray",
            font=("Segoe UI", 8, "italic")
        )
        lbl_warning.pack(pady=(0, 10))
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        btn_cancel = ttk.Button(
            btn_frame,
            text="Más Tarde",
            command=self.on_cancel
        )
        btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        btn_update = ttk.Button(
            btn_frame,
            text="Actualizar Ahora",
            command=self.on_update
        )
        btn_update.pack(side=tk.RIGHT, padx=5)
        
        # Focus en botón actualizar
        btn_update.focus_set()
        
    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
        
    def on_update(self):
        """Usuario acepta actualizar."""
        self.result = True
        self.destroy()
        
    def on_cancel(self):
        """Usuario rechaza actualizar."""
        self.result = False
        self.destroy()


class UpdateProgressDialog(tk.Toplevel):
    """Ventana de progreso durante la actualización."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setup_ui()
        
        # Hacer modal
        self.transient(parent)
        self.grab_set()
        
        # Centrar en pantalla
        self.center_window()
        
        # No permitir cerrar
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        
    def setup_ui(self):
        """Configura la interfaz del diálogo."""
        self.title("Actualizando...")
        self.geometry("400x150")
        self.resizable(False, False)
        
        # Frame principal
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        lbl_title = ttk.Label(
            main_frame,
            text="Descargando Actualización",
            font=("Segoe UI", 11, "bold")
        )
        lbl_title.pack(pady=(0, 20))
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            main_frame,
            mode='determinate',
            length=350
        )
        self.progress.pack(pady=10)
        
        # Etiqueta de estado
        self.lbl_status = ttk.Label(
            main_frame,
            text="Iniciando descarga...",
            foreground="gray"
        )
        self.lbl_status.pack()
        
    def update_progress(self, value: int, status: str = None):
        """
        Actualiza la barra de progreso.
        
        Args:
            value: Valor de progreso (0-100)
            status: Mensaje de estado opcional
        """
        self.progress['value'] = value
        if status:
            self.lbl_status.config(text=status)
        self.update()
        
    def center_window(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
