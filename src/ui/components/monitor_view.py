"""
Vista para configuración y ejecución del Monitor de Mensajes.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from ...services.browser_service import BrowserService
from ...services.monitor_runner import MonitorRunner
from ..styles import *


class MonitorView(ttk.Frame):
    """Vista independiente para Monitor de Mensajes."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.browser_service = BrowserService()
        self.profile_vars = {}
        self.active_monitors = []  # Lista de monitores en ejecución
        
        # Contenedor principal con scroll
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # =============== SECCIÓN: Configuración ===============
        config_frame = ttk.LabelFrame(main_container, text="Configuración del Monitor", padding=5)
        config_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 1. Selector de Perfiles
        ttk.Label(config_frame, text="Perfiles a Monitorear:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 2))
        ttk.Label(
            config_frame,
            text="  Solo se muestran perfiles con WhatsApp disponible (sin etiqueta BLOQUEADO)",
            font=("Arial", 7),
            foreground="gray"
        ).pack(anchor=tk.W, pady=(0, 3))
        
        # Frame contenedor para checkboxes (REDUCIDO)
        self.frame_profiles_container = ttk.Frame(config_frame, borderwidth=1, relief="solid")
        self.frame_profiles_container.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Header con "Seleccionar Todos" y filtro de tags
        self.frame_header = ttk.Frame(self.frame_profiles_container)
        self.frame_header.pack(fill=tk.X, padx=5, pady=5)
        
        self.var_select_all = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.frame_header, text="Seleccionar Todos", variable=self.var_select_all, command=self.toggle_all_profiles).pack(side=tk.LEFT)
        
        ttk.Button(self.frame_header, text="↻", width=3, command=self.refresh_profiles).pack(side=tk.RIGHT, padx=2)
        
        # Canvas scrollable para perfiles (ALTURA REDUCIDA)
        canvas_profiles = tk.Canvas(self.frame_profiles_container, height=120)
        scroll_profiles = ttk.Scrollbar(self.frame_profiles_container, orient="vertical", command=canvas_profiles.yview)
        canvas_profiles.configure(yscrollcommand=scroll_profiles.set)
        
        scroll_profiles.pack(side=tk.RIGHT, fill=tk.Y)
        canvas_profiles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.inner_frame_profiles = ttk.Frame(canvas_profiles)
        canvas_profiles.create_window((0, 0), window=self.inner_frame_profiles, anchor="nw")
        self.inner_frame_profiles.bind("<Configure>", lambda e: canvas_profiles.configure(scrollregion=canvas_profiles.bbox("all")))
        
        # 2. Configuración de navegadores
        frame_config = ttk.Frame(config_frame)
        frame_config.pack(fill=tk.X, pady=5)
        
        ttk.Label(frame_config, text="Navegadores Simultáneos:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_simultaneous = ttk.Spinbox(frame_config, from_=1, to=10, width=10)
        self.ent_simultaneous.set(3)
        self.ent_simultaneous.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(frame_config, text="Intervalo de Monitoreo (seg):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.ent_interval = ttk.Entry(frame_config, width=10)
        self.ent_interval.insert(0, "20")
        self.ent_interval.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 3. Configuración de notificaciones (REDUCIDO)
        frame_notif = ttk.LabelFrame(config_frame, text="Notificaciones", padding=5)
        frame_notif.pack(fill=tk.X, pady=3)
        
        # Campo 1: Grupo (Prioridad)
        ttk.Label(frame_notif, text="🥇 Grupo para Notificaciones (prioridad):", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        self.ent_notification_group = ttk.Entry(frame_notif, width=35)
        self.ent_notification_group.pack(fill=tk.X, pady=2)
        ttk.Label(frame_notif, text="  Nombre exacto del grupo de WhatsApp donde se enviarán las alertas",
                  font=("Arial", 7), foreground="gray").pack(anchor=tk.W)
        
        # Campo 2: Celular Respaldo
        ttk.Label(frame_notif, text="🥈 Contacto para notificación (respaldo):", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(5, 0))
        self.ent_notification_backup = ttk.Entry(frame_notif, width=35)
        self.ent_notification_backup.pack(fill=tk.X, pady=2)
        ttk.Label(frame_notif, text="  Ej: +573001234567  (se usa si el grupo falla o no se encuentra)",
                  font=("Arial", 7), foreground="gray").pack(anchor=tk.W)
        
        # 4. Configuración de auto-respuesta (REDUCIDO)
        frame_autoreply = ttk.LabelFrame(config_frame, text="Auto-Respuesta", padding=5)
        frame_autoreply.pack(fill=tk.X, pady=3)
        
        self.var_autoreply = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_autoreply, text="Activar Auto-Respuesta", variable=self.var_autoreply, command=self.toggle_autoreply).pack(anchor=tk.W)
        
        ttk.Label(frame_autoreply, text="Mensaje de Auto-Respuesta:").pack(anchor=tk.W, pady=(3, 0))
        self.ent_autoreply_text = tk.Text(frame_autoreply, height=2, width=40, state="disabled")
        self.ent_autoreply_text.pack(fill=tk.X, pady=3)
        
        # =============== BOTÓN INICIAR (GRANDE Y CENTRADO) ===============
        frame_button = ttk.Frame(main_container)
        frame_button.pack(pady=10, fill=tk.X)
        
        btn_start = ttk.Button(
            frame_button,
            text="INICIAR MONITOR",
            command=self.start_monitor,
            style="Accent.TButton"
        )
        btn_start.config(width=20)  # Ancho en caracteres
        btn_start.pack(pady=5, ipady=8)  # ipady aumenta altura interna
        
        # =============== SECCIÓN: Tareas Activas ===============
        tasks_frame = ttk.LabelFrame(main_container, text="Monitores Activos", padding=10)
        tasks_frame.pack(fill=tk.BOTH, expand=True)
        
        self.task_container = ttk.Frame(tasks_frame)
        self.task_container.pack(fill=tk.BOTH, expand=True)
        
        # Cargar perfiles inicial
        self.refresh_profiles()
    
    def toggle_all_profiles(self):
        """Seleccionar/deseleccionar todos los perfiles."""
        val = self.var_select_all.get()
        for var in self.profile_vars.values():
            var.set(val)
    
    def toggle_autoreply(self):
        """Activar/desactivar campo de auto-respuesta."""
        if self.var_autoreply.get():
            self.ent_autoreply_text.config(state="normal")
        else:
            self.ent_autoreply_text.config(state="disabled")
    
    def refresh_profiles(self):
        """Cargar lista de perfiles con WhatsApp disponible (sin etiqueta BLOQUEADO)."""
        all_profiles = self.browser_service.get_available_profiles()
        
        # Filtrar: solo perfiles donde WhatsApp NO está bloqueado
        profiles = [
            p for p in all_profiles
            if "BLOQUEADO" not in [t.upper() for t in p.tags]
        ]
        
        # Obtener tags únicos (excluyendo las de bloqueo)
        all_tags = set()
        for p in profiles:
            for tag in p.tags:
                if tag.upper() not in ("BLOQUEADO", "BLOQUEADO_SMS"):
                    all_tags.add(tag)
        sorted_tags = sorted(list(all_tags))
        
        # Limpiar checkboxes anteriores
        for widget in self.inner_frame_profiles.winfo_children():
            widget.destroy()
        self.profile_vars.clear()
        self.var_select_all.set(False)
        
        # Limpiar selector de etiquetas anterior si existe
        if hasattr(self, 'frame_tag_filter'):
            self.frame_tag_filter.destroy()
        
        # Crear selector de etiquetas en el header (solo si hay tags)
        if sorted_tags:
            self.frame_tag_filter = ttk.Frame(self.frame_header)
            self.frame_tag_filter.pack(side=tk.RIGHT, padx=5)
            
            ttk.Label(self.frame_tag_filter, text="Etiqueta:", font=("Arial", 8)).pack(side=tk.LEFT)
            self.combo_tags = ttk.Combobox(
                self.frame_tag_filter,
                values=["(Todas)"] + sorted_tags,
                state="readonly",
                width=12,
                font=("Arial", 8)
            )
            self.combo_tags.pack(side=tk.LEFT, padx=2)
            self.combo_tags.set("(Todas)")
            self.combo_tags.bind("<<ComboboxSelected>>", lambda e: self.select_by_tag(profiles))
        
        # Crear checkboxes para cada perfil
        for profile in profiles:
            var = tk.BooleanVar(value=False)
            
            # Formato con etiquetas
            display_text = profile.name
            if profile.tags:
                display_text += f" [{', '.join(profile.tags)}]"
            
            chk = ttk.Checkbutton(
                self.inner_frame_profiles,
                text=display_text,
                variable=var
            )
            chk.pack(anchor=tk.W, padx=5, pady=2)
            self.profile_vars[profile.name] = var
    
    def select_by_tag(self, profiles):
        """Marca los perfiles que coincidan con la etiqueta seleccionada."""
        tag = self.combo_tags.get()
        
        if tag == "(Todas)":
            return
        
        # Marcar solo perfiles con la etiqueta seleccionada, desmarcar el resto
        for p in profiles:
            if tag in p.tags:
                if p.name in self.profile_vars:
                    self.profile_vars[p.name].set(True)
            else:
                if p.name in self.profile_vars:
                    self.profile_vars[p.name].set(False)

    
    def start_monitor(self):
        """Iniciar monitor con la configuración actual."""
        # 1. Validar perfiles seleccionados
        selected_profiles = [name for name, var in self.profile_vars.items() if var.get()]
        
        if not selected_profiles:
            messagebox.showerror("Error", "Seleccione al menos un perfil para monitorear")
            return
        
        # 2. Validar campos de notificación (ambos son obligatorios)
        notification_group = self.ent_notification_group.get().strip()
        notification_backup = self.ent_notification_backup.get().strip()
        
        if not notification_group:
            messagebox.showerror("Error", "Ingrese el nombre del grupo de WhatsApp para notificaciones (prioridad)")
            return
        
        if not notification_backup:
            messagebox.showerror("Error", "Ingrese el número celular de respaldo para notificaciones")
            return
        
        # 3. Obtener configuración
        try:
            simultaneous = int(self.ent_simultaneous.get())
            interval = int(self.ent_interval.get())
        except ValueError:
            messagebox.showerror("Error", "Valores numéricos inválidos")
            return
        
        if simultaneous < 1:
            messagebox.showerror("Error", "Debe haber al menos 1 navegador simultáneo")
            return
        
        if simultaneous > len(selected_profiles):
            messagebox.showerror("Error", f"Navegadores simultáneos ({simultaneous}) no puede ser mayor que perfiles seleccionados ({len(selected_profiles)})")
            return
        
        if interval < 5:
            messagebox.showerror("Error", "El intervalo debe ser de al menos 5 segundos")
            return
        
        # 4. Auto-respuesta
        auto_reply_text = None
        if self.var_autoreply.get():
            auto_reply_text = self.ent_autoreply_text.get("1.0", tk.END).strip()
            if not auto_reply_text:
                messagebox.showwarning("Advertencia", "Auto-respuesta activada pero sin mensaje configurado")
                return
        
        # 5. Bloquear perfiles
        locked_profiles = []
        for p_name in selected_profiles:
            if self.browser_service.lock_profile(p_name):
                locked_profiles.append(p_name)
        
        if len(locked_profiles) != len(selected_profiles):
            # Liberar los bloqueados
            for p_name in locked_profiles:
                self.browser_service.unlock_profile(p_name)
            messagebox.showerror("Error", "Algunos perfiles están ocupados. Actualice la lista.")
            self.refresh_profiles()
            return
        
        # 6. Obtener objetos de perfil
        all_profiles = self.browser_service.get_all_profiles()
        target_profiles = [p for p in all_profiles if p.name in locked_profiles]
        
        # 7. Crear configuración para MonitorRunner
        config = {
            "profiles": target_profiles,
            "simultaneous": simultaneous,
            "interval": interval,
            "auto_reply_text": auto_reply_text,
            "monitor_group": notification_group,
            "monitor_backup": notification_backup
        }
        
        # 8. Crear UI card de tarea
        task_title = f"Monitor: {len(locked_profiles)} perfil(es), {simultaneous} simultáneo(s)"
        task_frame = ttk.LabelFrame(self.task_container, text=task_title)
        task_frame.pack(fill=tk.X, pady=5, anchor=tk.N)
        
        lbl_status = ttk.Label(task_frame, text="Iniciando...", width=50)
        lbl_status.pack(side=tk.LEFT, padx=5)
        
        # 9. Crear y ejecutar MonitorRunner
        runner = MonitorRunner(config)
        
        def on_complete():
            def _finish():
                try:
                    lbl_status.config(text="Monitor finalizado")
                    for p_name in locked_profiles:
                        self.browser_service.unlock_profile(p_name)
                    btn_stop.config(state="disabled")
                    messagebox.showinfo("Monitor Finalizado", "Monitoreo completado")
                    self.refresh_profiles()
                except tk.TclError:
                    for p_name in locked_profiles:
                        self.browser_service.unlock_profile(p_name)
                    self.refresh_profiles()
            self.after(0, _finish)
        
        def run_monitor():
            try:
                lbl_status.config(text="Monitoreando...")
                runner.run()
            finally:
                on_complete()
        
        # Iniciar en thread
        threading.Thread(target=run_monitor, daemon=True).start()
        
        # 10. Botón detener
        def stop_monitor():
            runner.stop()
            lbl_status.config(text="Deteniendo...")
            btn_stop.config(state="disabled")
        
        btn_stop = ttk.Button(task_frame, text="Detener", command=stop_monitor)
        btn_stop.pack(side=tk.RIGHT, padx=5)
        
        self.active_monitors.append(runner)
        messagebox.showinfo("Monitor Iniciado", f"Monitor activo para {len(locked_profiles)} perfil(es)")
