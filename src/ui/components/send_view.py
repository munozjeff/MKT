"""
Vista para configuración y lanzamiento de envíos.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from ...services.browser_service import BrowserService
from ...services.campaign_service import CampaignService
from ...services.contact_service import ContactService
from ...services.automation_runner import AutomationRunner
from ...services.distributed_runner import DistributedAutomationRunner
from ...services.rotation_runner import RotationAutomationRunner
from ...services.sms_automation_runner import SmsAutomationRunner
from ...services.distributed_sms_runner import DistributedSmsRunner
from ...services.rotation_sms_runner import RotationSmsRunner
from ...utils.file_utils import load_excel
from ..styles import *

class SendView(ttk.Frame):
    """Vista principal de envío de mensajes."""
    
    def __init__(self, parent, channel="WhatsApp"):
        super().__init__(parent)
        self.browser_service = BrowserService()
        self.campaign_service = CampaignService()
        self.contact_service = ContactService()
        self._channel = channel
        
        self.setup_ui()
        self.load_data()
        # Aplicar estado inicial del canal (habilita/deshabilita monitor)
        self.on_channel_change()

    def setup_ui(self):
        """Configura la interfaz."""
        canal_label = "WhatsApp" if self._channel == "WhatsApp" else "SMS (Google Messages)"
        lbl_title = ttk.Label(self, text=f"Enviar Mensajes - {canal_label}", font=FONT_TITLE)
        lbl_title.pack(pady=PADDING_MEDIUM)
        
        # Contenedor principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM)
        
        # -- Panel Configuración (Izquierda) --
        config_frame = ttk.LabelFrame(main_frame, text="Configuración de Envío")
        config_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING_MEDIUM))
        
        # === SECCIÓN SUPERIOR (Ancho Completo) ===
        top_frame = ttk.Frame(config_frame)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        grid_opts_top = {'padx': 5, 'pady': 5, 'sticky': tk.W}
        
        # Canal fijado (viene del botón del menú, no se cambia aquí)
        self.var_channel = tk.StringVar(value=self._channel)

        # 0. Selector de Modo
        ttk.Label(top_frame, text="Modo de Envío:").grid(row=0, column=0, **grid_opts_top)
        self.var_mode = tk.StringVar(value="Individual")
        frame_mode = ttk.Frame(top_frame)
        frame_mode.grid(row=0, column=1, columnspan=2, **grid_opts_top)
        
        rb_ind = ttk.Radiobutton(frame_mode, text="Individual", variable=self.var_mode, value="Individual", command=self.on_mode_change)
        rb_ind.pack(side=tk.LEFT, padx=5)
        rb_dist = ttk.Radiobutton(frame_mode, text="Distribuido", variable=self.var_mode, value="Distribuido", command=self.on_mode_change)
        rb_dist.pack(side=tk.LEFT, padx=5)
        rb_rot = ttk.Radiobutton(frame_mode, text="Rotación", variable=self.var_mode, value="Rotacion", command=self.on_mode_change)
        rb_rot.pack(side=tk.LEFT, padx=5)
        
        # 1. Perfil de Navegador
        self.lbl_profile = ttk.Label(top_frame, text="Perfil:")
        self.lbl_profile.grid(row=1, column=0, **grid_opts_top)
        
        # Contenedor para selector de perfiles (Single vs Multi)
        self.frame_profiles = ttk.Frame(top_frame)
        self.frame_profiles.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Modo Individual: Combobox
        self.combo_profiles = ttk.Combobox(self.frame_profiles, state="readonly")
        self.btn_refresh = ttk.Button(self.frame_profiles, text="↻", width=3, command=self.refresh_profiles)
        
        # Modo Distribuido: Checkboxes con Scroll
        self.frame_dist_container = ttk.Frame(self.frame_profiles, borderwidth=1, relief="solid")
        
        # Frame cabecera para "Seleccionar Todos"
        self.frame_dist_header = ttk.Frame(self.frame_dist_container)
        self.frame_dist_header.pack(fill=tk.X, padx=2, pady=2)
        
        self.var_select_all = tk.BooleanVar(value=False)
        self.chk_select_all = ttk.Checkbutton(self.frame_dist_header, text="Seleccionar Todos", variable=self.var_select_all, command=self.toggle_all_profiles)
        self.chk_select_all.pack(side=tk.LEFT)
        
        # Canvas scrollable para lista de perfiles
        self.canvas_profiles = tk.Canvas(self.frame_dist_container, height=100)
        self.scroll_profiles = ttk.Scrollbar(self.frame_dist_container, orient="vertical", command=self.canvas_profiles.yview)
        self.canvas_profiles.configure(yscrollcommand=self.scroll_profiles.set)
        
        self.scroll_profiles.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_profiles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.inner_frame_profiles = ttk.Frame(self.canvas_profiles)
        self.canvas_profiles.create_window((0, 0), window=self.inner_frame_profiles, anchor="nw")
        
        self.inner_frame_profiles.bind("<Configure>", lambda e: self.canvas_profiles.configure(scrollregion=self.canvas_profiles.bbox("all")))
        
        # Variables de estado para checkboxes
        self.profile_vars = {} # {profile_name: BooleanVar}
        
        
        # === SECCIÓN INFERIOR (Dos Columnas) ===
        columns_frame = ttk.Frame(config_frame)
        columns_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_col = ttk.Frame(columns_frame)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_col = ttk.Frame(columns_frame)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        grid_opts = {'padx': 5, 'pady': 5, 'sticky': tk.W}
        
        # --- COLUMNA IZQUIERDA (Archivo, Mensaje, Tiempos) ---
        
        # 2. Archivo Excel
        ttk.Label(left_col, text="Archivo Excel:").grid(row=0, column=0, **grid_opts)
        self.lbl_file = ttk.Label(left_col, text="No seleccionado", foreground="gray")
        self.lbl_file.grid(row=0, column=1, **grid_opts)
        ttk.Button(left_col, text="Cargar", command=self.load_excel_file).grid(row=0, column=2, padx=2)
        
        # 3. Tipo de Mensaje / Campaña
        ttk.Label(left_col, text=LBL_MESSAGE_TYPE).grid(row=1, column=0, **grid_opts)
        self.combo_msg_type = ttk.Combobox(left_col, values=MESSAGE_TYPES, state="readonly")
        self.combo_msg_type.grid(row=1, column=1, **grid_opts)
        self.combo_msg_type.bind("<<ComboboxSelected>>", self.on_msg_type_change)
        
        ttk.Label(left_col, text=LBL_CAMPAIGN_TYPE).grid(row=2, column=0, **grid_opts)
        self.combo_camp_type = ttk.Combobox(left_col, values=CAMPAIGN_TYPES, state="readonly")
        self.combo_camp_type.grid(row=2, column=1, **grid_opts)
        self.combo_camp_type.bind("<<ComboboxSelected>>", self.on_camp_type_change)
        
        # Selector de campaña principal (Predeterminada o Personalizada)
        self.lbl_camp_select = ttk.Label(left_col, text="Campaña:")
        self.lbl_camp_select.grid(row=3, column=0, **grid_opts)
        self.combo_campaign = ttk.Combobox(left_col, state="readonly")
        self.combo_campaign.grid(row=3, column=1, **grid_opts)
        
        # Selector de campaña personalizada (solo visible cuando tipo = Personalizada)
        self.lbl_custom_campaign = ttk.Label(left_col, text="Campaña Personalizada:")
        self.combo_custom_campaign = ttk.Combobox(left_col, state="readonly")
        
        # Carpeta Facturas (Oculto)
        self.lbl_folder = ttk.Label(left_col, text="Carpeta Facturas:")
        self.btn_folder = ttk.Button(left_col, text="Seleccionar", command=self.select_folder)
        self.lbl_folder_path = ttk.Label(left_col, text="", font=FONT_SMALL)
        
        # Tipo de Base (Oculto)
        self.lbl_base_type = ttk.Label(left_col, text=LBL_BASE_TYPE)
        self.combo_base_type = ttk.Combobox(left_col, values=BASE_TYPES, state="readonly")
        self.combo_base_type.bind("<<ComboboxSelected>>", self.on_base_type_change)
        
        # Intervalo Contacto (Oculto)
        self.lbl_contact_int = ttk.Label(left_col, text=LBL_CONTACT_INTERVAL)
        self.ent_contact_int = ttk.Entry(left_col, width=10)
        
        # 4. Tiempos
        ttk.Label(left_col, text=LBL_INTERVAL).grid(row=8, column=0, **grid_opts)
        self.ent_interval = ttk.Entry(left_col, width=10)
        self.ent_interval.insert(0, "50") # Default actualizado
        self.ent_interval.grid(row=8, column=1, **grid_opts)
        
        ttk.Label(left_col, text=LBL_PAUSE).grid(row=9, column=0, **grid_opts)
        self.ent_pause = ttk.Entry(left_col, width=10)
        self.ent_pause.insert(0, "10") # Default actualizado
        self.ent_pause.grid(row=9, column=1, **grid_opts)
        
        # --- COLUMNA DERECHA (Monitor, Auto-Respuesta, Rotación) ---
        
        # 5. Monitor de Mensajes Nuevos
        self.var_monitor_enabled = tk.BooleanVar(value=False)
        self.chk_monitor = ttk.Checkbutton(
            right_col, 
            text="Activar Monitor", 
            variable=self.var_monitor_enabled,
            command=self.on_monitor_toggle
        )
        self.chk_monitor.grid(row=0, column=0, columnspan=3, **grid_opts)
        
        # Campo de Grupo (Prioridad)
        ttk.Label(right_col, text="🥇 Grupo Notif. (prioridad):").grid(row=1, column=0, **grid_opts)
        self.ent_monitor_group = ttk.Entry(right_col, width=22, state="disabled")
        self.ent_monitor_group.grid(row=1, column=1, **grid_opts)
        ttk.Label(right_col, text="(nombre exacto del grupo)", font=("Arial", 8)).grid(row=1, column=2, padx=2, sticky=tk.W)
        
        # Campo de Celular Respaldo
        ttk.Label(right_col, text="🥈 Celular Respaldo:").grid(row=2, column=0, **grid_opts)
        self.ent_monitor_backup = ttk.Entry(right_col, width=22, state="disabled")
        self.ent_monitor_backup.grid(row=2, column=1, **grid_opts)
        ttk.Label(right_col, text="(Ej: +573001234567)", font=("Arial", 8)).grid(row=2, column=2, padx=2, sticky=tk.W)
        
        # 6. Auto-Respuesta (solo si Monitor activo)
        self.var_autoreply_enabled = tk.BooleanVar(value=False)
        self.chk_autoreply = ttk.Checkbutton(
            right_col,
            text="Auto-Respuesta",
            variable=self.var_autoreply_enabled,
            command=self.on_autoreply_toggle,
            state="disabled"
        )
        self.chk_autoreply.grid(row=3, column=0, **grid_opts)
        
        self.ent_autoreply_text = ttk.Entry(right_col, width=30, state="disabled")
        self.ent_autoreply_text.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Frame para configuración de Rotación (inicialmente oculto)
        self.frame_rotation_config = ttk.Frame(right_col)
        
        ttk.Label(self.frame_rotation_config, text="Perfiles Simultáneos:").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.ent_simultaneous = ttk.Entry(self.frame_rotation_config, width=10)
        self.ent_simultaneous.insert(0, "5")
        self.ent_simultaneous.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(self.frame_rotation_config, text="Mensajes por Perfil:").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.ent_msgs_per_profile = ttk.Entry(self.frame_rotation_config, width=10)
        self.ent_msgs_per_profile.insert(0, "10")
        self.ent_msgs_per_profile.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Label(self.frame_rotation_config, text="Cooldown (minutos):").grid(row=2, column=0, padx=5, pady=2, sticky=tk.W)
        self.ent_profile_cooldown = ttk.Entry(self.frame_rotation_config, width=10)
        self.ent_profile_cooldown.insert(0, "60")  # Default 1 hora
        self.ent_profile_cooldown.grid(row=2, column=1, padx=5, pady=2)
        ttk.Label(self.frame_rotation_config, text="(tiempo antes de reutilizar perfil)", font=("Arial", 8)).grid(row=2, column=2, padx=2, pady=2, sticky=tk.W)

        # ── Solo RCS (solo aplica a canal SMS) ──────────────────────────────
        self.var_only_rcs = tk.BooleanVar(value=False)
        self.chk_only_rcs = ttk.Checkbutton(
            right_col,
            text="📡 Solo RCS (omitir SMS convencional)",
            variable=self.var_only_rcs
        )
        # Se muestra u oculta en on_channel_change()
        
        # === BOTÓN LANZAR (Parte inferior de config_frame, fuera de las columnas) ===
        bottom_frame = ttk.Frame(config_frame)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)
        
        self.btn_launch = ttk.Button(bottom_frame, text="LANZAR TAREA", command=self.launch_task)
        self.btn_launch.pack(fill=tk.X)
        
        # -- Panel Tareas Activas (Derecha) --
        tasks_frame = ttk.LabelFrame(main_frame, text="Tareas Activas")
        tasks_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.task_container = ttk.Frame(tasks_frame)
        self.task_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def load_data(self):
        self.refresh_profiles()
        self.on_mode_change() # Set initial state
        # Iniciar sin selección
        self.combo_msg_type.set('')
        self.combo_camp_type.set('')
        
    def on_mode_change(self):
        mode = self.var_mode.get()
        # Limpiar
        self.combo_profiles.pack_forget()
        self.btn_refresh.pack_forget()
        self.frame_dist_container.pack_forget()
        self.frame_rotation_config.grid_forget()
        
        if mode == "Individual":
            self.combo_profiles.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.btn_refresh.pack(side=tk.LEFT, padx=2)
            self.lbl_profile.config(text="Perfil:")
        elif mode == "Distribuido":
            self.frame_dist_container.pack(fill=tk.BOTH, expand=True)
            self.btn_refresh.pack(side=tk.RIGHT, padx=2)
            self.lbl_profile.config(text="Perfiles:")
        elif mode == "Rotacion":
            self.frame_dist_container.pack(fill=tk.BOTH, expand=True)
            self.btn_refresh.pack(side=tk.RIGHT, padx=2)
            self.lbl_profile.config(text="Perfiles:")
            self.frame_rotation_config.grid(row=3, column=0, columnspan=3, pady=10, sticky="ew")
    
    def toggle_all_profiles(self):
        val = self.var_select_all.get()
        for var in self.profile_vars.values():
            var.set(val)
            
    def refresh_profiles(self):
        profiles = self.browser_service.get_available_profiles()
        values = [p.name for p in profiles]
        
        # Obtener todas las etiquetas únicas
        all_tags = set()
        for p in profiles:
            for tag in p.tags:
                all_tags.add(tag)
        sorted_tags = sorted(list(all_tags))
        
        # Actualizar Combo (Individual)
        self.combo_profiles['values'] = values
        self.combo_profiles.set('') # Limpiar selección por defecto
            
        # Actualizar Checkboxes (Distribuido)
        # Limpiar anteriores
        for widget in self.inner_frame_profiles.winfo_children():
            widget.destroy()
        self.profile_vars.clear()
        self.var_select_all.set(False)
        
        # Limpiar selector de etiquetas anterior si existe
        if hasattr(self, 'frame_tag_filter'):
            self.frame_tag_filter.destroy()
            
        # Crear selector de etiquetas en el header
        self.frame_tag_filter = ttk.Frame(self.frame_dist_header)
        self.frame_tag_filter.pack(side=tk.RIGHT, padx=5)
        
        ttk.Label(self.frame_tag_filter, text="Etiqueta:", font=("Arial", 8)).pack(side=tk.LEFT)
        self.combo_tags = ttk.Combobox(self.frame_tag_filter, values=["(Todas)"] + sorted_tags, state="readonly", width=10, font=("Arial", 8))
        self.combo_tags.pack(side=tk.LEFT, padx=2)
        self.combo_tags.set("(Todas)")
        self.combo_tags.bind("<<ComboboxSelected>>", lambda e: self.select_by_tag(profiles))
        
        for p_name in values:
            var = tk.BooleanVar(value=False)
            self.profile_vars[p_name] = var
            
            # Formato nombre con etiquetas
            p_obj = next((p for p in profiles if p.name == p_name), None)
            display_text = p_name
            if p_obj and p_obj.tags:
                display_text += f" [{', '.join(p_obj.tags)}]"
                
            chk = ttk.Checkbutton(self.inner_frame_profiles, text=display_text, variable=var)
            chk.pack(anchor="w", padx=5)

    def select_by_tag(self, profiles):
        """Marca los perfiles que coincidan con la etiqueta seleccionada."""
        tag = self.combo_tags.get()
        
        # Si selecciona (Todas), no hacemos nada especial (o podríamos deseleccionar todo? Mejor no tocar para no borrar manual)
        if tag == "(Todas)":
            return
            
        # Marcar los coincidentes
        count = 0
        for p in profiles:
            if tag in p.tags:
                if p.name in self.profile_vars:
                    self.profile_vars[p.name].set(True)
                    count += 1
            else:
                # Opcional: Desmarcar los que no coinciden? 
                # El usuario pidió "seleccionar todos los de un grupo", no necesariamente deseleccionar el resto.
                # Pero para "filtrar" suele esperarse que solo queden esos.
                # Vamos a desmarcar los que no tengan el tag para que sea una selección limpia del grupo.
                if p.name in self.profile_vars:
                    self.profile_vars[p.name].set(False)
        
        # Feedback visual si no hay coincidencias (raro si viene del combo)
        if count == 0:
            pass
    
    def on_monitor_toggle(self):
        """Enable/disable monitor inputs and auto-reply checkbox."""
        enabled = self.var_monitor_enabled.get()
        state = "normal" if enabled else "disabled"
        self.ent_monitor_group.config(state=state)
        self.ent_monitor_backup.config(state=state)
        self.chk_autoreply.config(state=state)
        
        # Clear and disable auto-reply if monitor is disabled
        if not enabled:
            self.var_autoreply_enabled.set(False)
            self.on_autoreply_toggle()

    def on_autoreply_toggle(self):
        """Enable/disable auto-reply text input."""
        enabled = self.var_autoreply_enabled.get()
        self.ent_autoreply_text.config(state="normal" if enabled else "disabled")

    def on_channel_change(self):
        """Muestra u oculta la sección Monitor según el canal seleccionado.
        El monitor solo aplica a WhatsApp, no a Google Messages.
        El checkbox 'Solo RCS' solo aplica a SMS."""
        is_whatsapp = self.var_channel.get() == "WhatsApp"
        monitor_state = "normal" if is_whatsapp else "disabled"

        # Habilitar/deshabilitar el checkbox del monitor
        self.chk_monitor.config(state=monitor_state)

        if not is_whatsapp:
            # Desactivar monitor y limpiar campos al cambiar a SMS
            self.var_monitor_enabled.set(False)
            self.on_monitor_toggle()  # propaga el disable a los campos hijo

        # Indicador visual en la etiqueta del monitor
        if is_whatsapp:
            self.chk_monitor.config(text="Activar Monitor")
            # Ocultar Solo RCS en WhatsApp
            self.chk_only_rcs.grid_forget()
        else:
            self.chk_monitor.config(text="Activar Monitor (solo WhatsApp)")
            # Mostrar Solo RCS en modo SMS
            self.chk_only_rcs.grid(row=5, column=0, columnspan=3, padx=5, pady=(8, 2), sticky=tk.W)
            
    def load_excel_file(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if path:
            self.excel_path = path
            self.lbl_file.config(text=os.path.basename(path), foreground="black")
            
    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.facturas_folder = path
            self.lbl_folder_path.config(text=os.path.basename(path))

    def on_msg_type_change(self, event):
        val = self.combo_msg_type.get()
        # Limpiar extras
        self.lbl_folder.grid_forget()
        self.btn_folder.grid_forget()
        self.lbl_folder_path.grid_forget()
        self.lbl_base_type.grid_forget()
        self.combo_base_type.grid_forget()
        self.lbl_contact_int.grid_forget()
        self.ent_contact_int.grid_forget()
        
        if val == "Facturas":
            self.lbl_folder.grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
            self.btn_folder.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
            self.lbl_folder_path.grid(row=6, column=2, padx=5, pady=5)
        elif val == "Anti Spam":
            self.lbl_base_type.grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
            self.combo_base_type.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)
            self.combo_base_type.set('')
            
    def on_base_type_change(self, event):
        val = self.combo_base_type.get()
        if val == "Con Intervalos":
            self.lbl_contact_int.grid(row=8, column=0, padx=5, pady=5, sticky=tk.W)
            self.ent_contact_int.grid(row=8, column=1, padx=5, pady=5, sticky=tk.W)
        else:
            self.lbl_contact_int.grid_forget()
            self.ent_contact_int.grid_forget()
            
    def on_camp_type_change(self, event):
        val = self.combo_camp_type.get()
        # Limpiar selección campaña previa
        self.combo_campaign.set('')
        self.combo_custom_campaign.set('')
        
        # Ocultar todos primero
        self.lbl_camp_select.grid_forget()
        self.combo_campaign.grid_forget()
        self.lbl_custom_campaign.grid_forget()
        self.combo_custom_campaign.grid_forget()
        
        if val == "Default" or not val:
            # No mostrar nada
            pass
        elif val == "Personalizada":
            # Mostrar AMBOS: Campaña Predeterminada (fallback) y Campaña Personalizada
            # 1. Campaña Predeterminada (Fallback)
            self.lbl_camp_select.config(text="Campaña por Defecto (Fallback):")
            self.lbl_camp_select.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
            self.combo_campaign.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
            campaigns = self.campaign_service.get_campaign_titles("campaigns")
            self.combo_campaign['values'] = campaigns
            self.combo_campaign.set('') # Sin selección
            
            # 2. Campaña Personalizada
            self.lbl_custom_campaign.grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
            self.combo_custom_campaign.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
            custom_campaigns = self.campaign_service.get_campaign_titles("custom_campaign")
            self.combo_custom_campaign['values'] = custom_campaigns
            self.combo_custom_campaign.set('') # Sin selección
        else:
            # Tipo "Predeterminada" - Solo mostrar selector de campaña predeterminada
            self.lbl_camp_select.config(text="Campaña:")
            self.lbl_camp_select.grid(row=5, column=0, padx=5, pady=5, sticky=tk.W)
            self.combo_campaign.grid(row=5, column=1, padx=5, pady=5, sticky=tk.W)
            
            # Cargar campañas predeterminadas
            campaigns = self.campaign_service.get_campaign_titles("campaigns")
            self.combo_campaign['values'] = campaigns
            self.combo_campaign.set('') # Sin selección

    def launch_task(self):
        mode = self.var_mode.get()
        selected_profiles = []
        
        # 1. Obtener Perfiles
        if mode == "Individual":
            p_name = self.combo_profiles.get()
            if p_name: selected_profiles.append(p_name)
        else:
            # Obtener desde Checkvars
            for p_name, var in self.profile_vars.items():
                if var.get():
                    selected_profiles.append(p_name)
            
        if not selected_profiles:
            messagebox.showerror(MSG_ERROR, "Seleccione al menos un perfil")
            return
            
        # 2. Validaciones generales
        if not hasattr(self, 'excel_path'):
            messagebox.showerror(MSG_ERROR, "Cargue un archivo Excel")
            return
            
        try:
            phones, user_data, contact_data = load_excel(self.excel_path)
        except Exception as e:
            messagebox.showerror(MSG_ERROR, f"Error Excel: {e}")
            return
            
        config = {
            "interval": self.ent_interval.get(),
            "pause": self.ent_pause.get(),
            "message_type": self.combo_msg_type.get(),
            "campaign_type": self.combo_camp_type.get(),
            "only_rcs": self.var_only_rcs.get() if not (self.var_channel.get() == "WhatsApp") else False,
        }
        
        # Monitor Configuration
        monitor_group = None
        monitor_backup = None
        auto_reply_text = None
        
        if self.var_monitor_enabled.get():
            monitor_group = self.ent_monitor_group.get().strip()
            monitor_backup = self.ent_monitor_backup.get().strip()
            
            if not monitor_group:
                messagebox.showwarning("Advertencia", "Monitor activado pero sin nombre de grupo para notificaciones.")
                return
            
            if not monitor_backup:
                messagebox.showwarning("Advertencia", "Monitor activado pero sin número celular de respaldo.")
                return
            
            if self.var_autoreply_enabled.get():
                auto_reply_text = self.ent_autoreply_text.get().strip()
                if not auto_reply_text:
                    messagebox.showwarning("Advertencia", "Auto-respuesta activada pero sin mensaje configurado.")
                    return
        
        config["monitor_group"] = monitor_group
        config["monitor_backup"] = monitor_backup
        config["auto_reply_text"] = auto_reply_text
        
        if not config["message_type"]:
             messagebox.showerror(MSG_ERROR, "Seleccione Tipo de Mensaje")
             return
             
        if not config["campaign_type"]:
             messagebox.showerror(MSG_ERROR, "Seleccione Tipo de Campaña")
             return
        
        # Validaciones específicas
        if config["message_type"] == "Facturas":
            if not hasattr(self, 'facturas_folder'):
                messagebox.showerror(MSG_ERROR, "Seleccione carpeta facturas")
                return
            config["facturas_folder"] = self.facturas_folder
            
        if config["message_type"] == "Anti Spam":
            base_type = self.combo_base_type.get()
            if not base_type:
                messagebox.showerror(MSG_ERROR, "Seleccione tipo de base")
                return
            if base_type == "Con Intervalos":
                try:
                    interval_contact = int(self.ent_contact_int.get())
                    phones = self.contact_service.interpolate_contacts(phones, interval_contact)
                except ValueError:
                    messagebox.showerror(MSG_ERROR, "Intervalo contacto inválido")
                    return
        
        
        campaign = None
        fallback_campaign = None
        
        if config["campaign_type"] != "Default":
            if config["campaign_type"] == "Personalizada":
                # Modo Personalizada: Requiere AMBAS campañas
                # 1. Campaña Predeterminada (Fallback)
                fallback_title = self.combo_campaign.get()
                if not fallback_title:
                    messagebox.showerror(MSG_ERROR, "Seleccione una campaña por defecto (fallback)")
                    return
                fallback_campaign = self.campaign_service.get_campaign(fallback_title, "campaigns")
                if not fallback_campaign:
                    messagebox.showerror(MSG_ERROR, "Campaña fallback no encontrada")
                    return
                
                # 2. Campaña Personalizada (Principal)
                custom_title = self.combo_custom_campaign.get()
                if not custom_title:
                    messagebox.showerror(MSG_ERROR, "Seleccione una campaña personalizada")
                    return
                campaign = self.campaign_service.get_campaign(custom_title, "custom_campaign")
                if not campaign:
                    messagebox.showerror(MSG_ERROR, "Campaña personalizada no encontrada")
                    return
            else:
                # Modo Predeterminada: Solo una campaña
                camp_title = self.combo_campaign.get()
                if not camp_title:
                    messagebox.showerror(MSG_ERROR, "Seleccione una campaña")
                    return
                campaign = self.campaign_service.get_campaign(camp_title, "campaigns")
                if not campaign:
                    messagebox.showerror(MSG_ERROR, "Campaña no encontrada")
                    return

        # 3. Bloquear perfiles
        locked_profiles = []
        for p_name in selected_profiles:
            if self.browser_service.lock_profile(p_name):
                locked_profiles.append(p_name)
            else:
                pass 
        
        if len(locked_profiles) != len(selected_profiles):
            # Liberar los que se bloquearon
            for p_name in locked_profiles:
                self.browser_service.unlock_profile(p_name)
            messagebox.showerror(MSG_ERROR, "Algunos perfiles seleccionados están ocupados. Actualice la lista.")
            self.refresh_profiles()
            return
            
        # 4. Iniciar Runner
        all_profiles_objs = self.browser_service.get_all_profiles()
        target_profiles = [p for p in all_profiles_objs if p.name in locked_profiles]
        
        # UI Card - Cada tarea en su propio frame
        if mode == "Individual":
            task_title = f"Individual: {locked_profiles[0]}"
        elif mode == "Distribuido":
            task_title = f"Distribuido ({len(locked_profiles)} perfiles)"
        else:  # Rotacion
            task_title = f"Rotación ({len(locked_profiles)} perfiles, {self.ent_simultaneous.get()} simultáneos)"
        task_frame = ttk.LabelFrame(self.task_container, text=task_title)
        task_frame.pack(fill=tk.X, pady=5, anchor=tk.N)  # anchor=tk.N para apilar hacia arriba
        
        lbl_status = ttk.Label(task_frame, text="Iniciando...", width=40)
        lbl_status.pack(side=tk.LEFT, padx=5)
        
        progress = ttk.Progressbar(task_frame, length=100, mode='determinate')
        progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Flag para saber si el widget fue destruido
        task_active = {'active': True}
        
        def update_ui(idx, total, text):
            def _update():
                # Validar que el widget aún existe antes de actualizar
                if not task_active['active']:
                    return
                try:
                    if total > 0:
                        progress['maximum'] = total
                        progress['value'] = idx
                        # Mostrar progreso "X de Y" junto con la acción
                        progress_text = f"[{idx}/{total}] {text}"
                    else:
                        progress_text = text
                    lbl_status.config(text=progress_text)
                except tk.TclError:
                    # Widget ya fue destruido
                    task_active['active'] = False
            self.after(0, _update)

        def on_profile_blocked(profile_name):
            """Llamado cuando un worker detecta QR y bloquea el perfil mid-run."""
            def _refresh():
                try:
                    self.refresh_profiles()
                except Exception:
                    pass
            self.after(0, _refresh)
            
        def on_complete(report_path):
            def _finish():
                try:
                    lbl_status.config(text="Completado")
                    for p_name in locked_profiles:
                        self.browser_service.unlock_profile(p_name)
                    btn_cancel.config(state="disabled")
                    messagebox.showinfo("Tarea Finalizada", f"Informe guardado: {os.path.basename(report_path)}")
                    self.refresh_profiles()
                except tk.TclError:
                    # Widget ya destruido, solo desbloquear perfiles
                    for p_name in locked_profiles:
                        self.browser_service.unlock_profile(p_name)
                    self.refresh_profiles()
            self.after(0, _finish)
            
        channel = self.var_channel.get()
        is_sms = (channel == "SMS (Google Messages)")

        if mode == "Individual":
            if is_sms:
                runner = SmsAutomationRunner(
                    browser_profile=target_profiles[0],
                    config=config,
                    phone_numbers=phones,
                    user_data=user_data,
                    contact_data=contact_data,
                    campaign=campaign,
                    fallback_campaign=fallback_campaign,
                    progress_callback=update_ui,
                    completion_callback=on_complete,
                    profile_blocked_callback=on_profile_blocked
                )
            else:
                runner = AutomationRunner(
                    browser_profile=target_profiles[0],
                    config=config,
                    phone_numbers=phones,
                    user_data=user_data,
                    contact_data=contact_data,
                    campaign=campaign,
                    fallback_campaign=fallback_campaign,
                    progress_callback=update_ui,
                    completion_callback=on_complete
                )
        elif mode == "Distribuido":
            if is_sms:
                runner = DistributedSmsRunner(
                    browser_profiles=target_profiles,
                    config=config,
                    phone_numbers=phones,
                    user_data=user_data,
                    contact_data=contact_data,
                    campaign=campaign,
                    fallback_campaign=fallback_campaign,
                    progress_callback=update_ui,
                    completion_callback=on_complete,
                    profile_blocked_callback=on_profile_blocked
                )
            else:
                runner = DistributedAutomationRunner(
                    browser_profiles=target_profiles,
                    config=config,
                    phone_numbers=phones,
                    user_data=user_data,
                    contact_data=contact_data,
                    campaign=campaign,
                    fallback_campaign=fallback_campaign,
                    progress_callback=update_ui,
                    completion_callback=on_complete
                )
        else:  # Rotacion
            # Validar parámetros de rotación
            try:
                simultaneous = int(self.ent_simultaneous.get())
                msgs_per_profile = int(self.ent_msgs_per_profile.get())
                cooldown_minutes = int(self.ent_profile_cooldown.get())
            except ValueError:
                for p_name in locked_profiles:
                    self.browser_service.unlock_profile(p_name)
                messagebox.showerror(MSG_ERROR, "Valores numéricos inválidos para Rotación")
                return
            
            if simultaneous > len(locked_profiles):
                for p_name in locked_profiles:
                    self.browser_service.unlock_profile(p_name)
                messagebox.showerror(MSG_ERROR, f"Perfiles simultáneos ({simultaneous}) no puede ser mayor que perfiles seleccionados ({len(locked_profiles)})")
                return
            
            if simultaneous < 1:
                for p_name in locked_profiles:
                    self.browser_service.unlock_profile(p_name)
                messagebox.showerror(MSG_ERROR, "Debe haber al menos 1 perfil simultáneo")
                return
            
            if msgs_per_profile < 1:
                for p_name in locked_profiles:
                    self.browser_service.unlock_profile(p_name)
                messagebox.showerror(MSG_ERROR, "Debe enviar al menos 1 mensaje por perfil")
                return
            
            if cooldown_minutes < 0:
                for p_name in locked_profiles:
                    self.browser_service.unlock_profile(p_name)
                messagebox.showerror(MSG_ERROR, "El cooldown no puede ser negativo")
                return

            if is_sms:
                runner = RotationSmsRunner(
                    browser_profiles=target_profiles,
                    simultaneous_profiles=simultaneous,
                    messages_per_profile=msgs_per_profile,
                    profile_cooldown_minutes=cooldown_minutes,
                    config=config,
                    phone_numbers=phones,
                    user_data=user_data,
                    contact_data=contact_data,
                    campaign=campaign,
                    fallback_campaign=fallback_campaign,
                    progress_callback=update_ui,
                    completion_callback=on_complete,
                    profile_blocked_callback=on_profile_blocked
                )
            else:
                runner = RotationAutomationRunner(
                    browser_profiles=target_profiles,
                    simultaneous_profiles=simultaneous,
                    messages_per_profile=msgs_per_profile,
                    profile_cooldown_minutes=cooldown_minutes,
                    config=config,
                    phone_numbers=phones,
                    user_data=user_data,
                    contact_data=contact_data,
                    campaign=campaign,
                    fallback_campaign=fallback_campaign,
                    progress_callback=update_ui,
                    completion_callback=on_complete
                )
        
        btn_cancel = ttk.Button(task_frame, text="Cancelar", command=lambda: self.cancel_task(runner, locked_profiles, task_active))
        btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        runner.start()
        self.refresh_profiles()
    
    def cancel_task(self, runner, profiles, task_active):
        if messagebox.askyesno("Confirmar", "Detener tarea?"):
            runner.stop()
            task_active['active'] = False  # Marcar como inactivo
            # Liberar perfiles
            for p_name in profiles:
                self.browser_service.unlock_profile(p_name)
            self.refresh_profiles()

