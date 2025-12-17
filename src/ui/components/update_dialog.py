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
        self.geometry("500x400") # Ventana más alta
        self.resizable(False, False)
        
        # 1. Frame de botones (LO EMPAQUETAMOS PRIMERO al fondo de la ventana)
        btn_frame = ttk.Frame(self, padding=20)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Botón Actualizar (Grande y claro - Usando tk.Button nativo)
        self.btn_update = tk.Button(
            btn_frame,
            text="⬇️  DESCARGAR E INSTALAR AHORA",
            command=self.on_update,
            font=("Segoe UI", 11, "bold"),
            bg="#0078D4", # Azul Microsoft
            fg="white",
            cursor="hand2",
            pady=10
        )
        self.btn_update.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        
        # Botón Cancelar
        ttk.Button(
            btn_frame,
            text="Recordármelo más tarde",
            command=self.on_cancel
        ).pack(side=tk.TOP)

        # 2. Frame principal (Ocupa el resto del espacio ARRIBA de los botones)
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Título
        lbl_title = ttk.Label(
            main_frame,
            text="¡Nueva Versión Disponible!",
            font=("Segoe UI", 16, "bold")
        )
        lbl_title.pack(side=tk.TOP, pady=(0, 10))
        
        # Info de versión
        info_frame = ttk.LabelFrame(main_frame, text="Detalles", padding=15)
        info_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Versión y fecha
        ttk.Label(info_frame, text=f"Versión: {self.update_info.get('version', 'N/A')}", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Fecha: {self.update_info.get('release_date', 'N/A')}").pack(anchor=tk.W)
        
        # Notas
        ttk.Label(info_frame, text="Notas:", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        text_notes = tk.Text(info_frame, height=5, wrap=tk.WORD, bg="#f5f5f5", relief=tk.FLAT)
        text_notes.insert("1.0", self.update_info.get('release_notes', 'Sin notas de versión.'))
        text_notes.config(state=tk.DISABLED)
        # Scrollbar para las notas
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=text_notes.yview)
        text_notes.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_notes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.btn_update.focus_set()
        
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
