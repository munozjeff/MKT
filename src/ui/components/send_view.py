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
from ...utils.file_utils import load_excel
from ..styles import *

class SendView(ttk.Frame):
    """Vista principal de envío de mensajes."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.browser_service = BrowserService()
        self.campaign_service = CampaignService()
        self.contact_service = ContactService()
        
        self.setup_ui()
        self.load_data()
        
    def setup_ui(self):
        """Configura la interfaz."""
        lbl_title = ttk.Label(self, text=BTN_SEND_MESSAGES, font=FONT_TITLE)
    def setup_ui(self):
        """Configura la interfaz."""
        lbl_title = ttk.Label(self, text=BTN_SEND_MESSAGES, font=FONT_TITLE)
        lbl_title.pack(pady=PADDING_MEDIUM)
        
        # Contenedor principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM)
        
        # -- Panel Configuración (Izquierda) --
        config_frame = ttk.LabelFrame(main_frame, text="Configuración de Envío")
        config_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING_MEDIUM))
        
        # Grid layout
        grid_opts = {'padx': 5, 'pady': 5, 'sticky': tk.W}
        
        # 0. Selector de Modo
        ttk.Label(config_frame, text="Modo de Envío:").grid(row=0, column=0, **grid_opts)
        self.var_mode = tk.StringVar(value="Individual")
        frame_mode = ttk.Frame(config_frame)
        frame_mode.grid(row=0, column=1, columnspan=2, **grid_opts)
        
        rb_ind = ttk.Radiobutton(frame_mode, text="Individual", variable=self.var_mode, value="Individual", command=self.on_mode_change)
        rb_ind.pack(side=tk.LEFT, padx=5)
        rb_dist = ttk.Radiobutton(frame_mode, text="Distribuido (Multi-Perfil)", variable=self.var_mode, value="Distribuido", command=self.on_mode_change)
        rb_dist.pack(side=tk.LEFT, padx=5)
        
        # 1. Perfil de Navegador
        self.lbl_profile = ttk.Label(config_frame, text="Perfil:")
        self.lbl_profile.grid(row=1, column=0, **grid_opts)
        
        # Contenedor para selector de perfiles (Single vs Multi)
        self.frame_profiles = ttk.Frame(config_frame)
        self.frame_profiles.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
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
        
        
        # 2. Archivo Excel
        ttk.Label(config_frame, text="Archivo Excel:").grid(row=2, column=0, **grid_opts)
        self.lbl_file = ttk.Label(config_frame, text="No seleccionado", foreground="gray")
        self.lbl_file.grid(row=2, column=1, **grid_opts)
        ttk.Button(config_frame, text="Cargar", command=self.load_excel_file).grid(row=2, column=2, padx=2)
        
        # 3. Tipo de Mensaje / Campaña
        ttk.Label(config_frame, text=LBL_MESSAGE_TYPE).grid(row=3, column=0, **grid_opts)
        self.combo_msg_type = ttk.Combobox(config_frame, values=MESSAGE_TYPES, state="readonly")
        self.combo_msg_type.grid(row=3, column=1, **grid_opts)
        self.combo_msg_type.bind("<<ComboboxSelected>>", self.on_msg_type_change)
        
        ttk.Label(config_frame, text=LBL_CAMPAIGN_TYPE).grid(row=4, column=0, **grid_opts)
        self.combo_camp_type = ttk.Combobox(config_frame, values=CAMPAIGN_TYPES, state="readonly")
        self.combo_camp_type.grid(row=4, column=1, **grid_opts)
        self.combo_camp_type.bind("<<ComboboxSelected>>", self.on_camp_type_change)
        
        # Selector de campaña principal (Predeterminada o Personalizada)
        self.lbl_camp_select = ttk.Label(config_frame, text="Campaña:")
        self.lbl_camp_select.grid(row=5, column=0, **grid_opts)
        self.combo_campaign = ttk.Combobox(config_frame, state="readonly")
        self.combo_campaign.grid(row=5, column=1, **grid_opts)
        
        # Selector de campaña personalizada (solo visible cuando tipo = Personalizada)
        self.lbl_custom_campaign = ttk.Label(config_frame, text="Campaña Personalizada:")
        self.combo_custom_campaign = ttk.Combobox(config_frame, state="readonly")
        
        # Carpeta Facturas (Oculto)
        self.lbl_folder = ttk.Label(config_frame, text="Carpeta Facturas:")
        self.btn_folder = ttk.Button(config_frame, text="Seleccionar", command=self.select_folder)
        self.lbl_folder_path = ttk.Label(config_frame, text="", font=FONT_SMALL)
        
        # Tipo de Base (Oculto)
        self.lbl_base_type = ttk.Label(config_frame, text=LBL_BASE_TYPE)
        self.combo_base_type = ttk.Combobox(config_frame, values=BASE_TYPES, state="readonly")
        self.combo_base_type.bind("<<ComboboxSelected>>", self.on_base_type_change)
        
        # Intervalo Contacto (Oculto)
        self.lbl_contact_int = ttk.Label(config_frame, text=LBL_CONTACT_INTERVAL)
        self.ent_contact_int = ttk.Entry(config_frame, width=10)
        
        # 4. Tiempos
        ttk.Label(config_frame, text=LBL_INTERVAL).grid(row=10, column=0, **grid_opts)
        self.ent_interval = ttk.Entry(config_frame, width=10)
        self.ent_interval.insert(0, "50") # Default actualizado
        self.ent_interval.grid(row=10, column=1, **grid_opts)
        
        ttk.Label(config_frame, text=LBL_PAUSE).grid(row=11, column=0, **grid_opts)
        self.ent_pause = ttk.Entry(config_frame, width=10)
        self.ent_pause.insert(0, "10") # Default actualizado
        self.ent_pause.grid(row=11, column=1, **grid_opts)
        
        # Botón Lanzar
        ttk.Button(config_frame, text="LANZAR TAREA", command=self.launch_task).grid(row=15, column=0, columnspan=3, pady=20, sticky="ew")
        
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
        
        if mode == "Individual":
            self.combo_profiles.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.btn_refresh.pack(side=tk.LEFT, padx=2)
            self.lbl_profile.config(text="Perfil:")
        else:
            self.frame_dist_container.pack(fill=tk.BOTH, expand=True)
            self.btn_refresh.pack(side=tk.RIGHT, padx=2)
            self.lbl_profile.config(text="Perfiles:")
    
    def toggle_all_profiles(self):
        val = self.var_select_all.get()
        for var in self.profile_vars.values():
            var.set(val)
            
    def refresh_profiles(self):
        profiles = self.browser_service.get_available_profiles()
        values = [p.name for p in profiles]
        
        # Actualizar Combo (Individual)
        self.combo_profiles['values'] = values
        self.combo_profiles.set('') # Limpiar selección por defecto
            
        # Actualizar Checkboxes (Distribuido)
        # Limpiar anteriores
        for widget in self.inner_frame_profiles.winfo_children():
            widget.destroy()
        self.profile_vars.clear()
        self.var_select_all.set(False)
        
        for p_name in values:
            var = tk.BooleanVar(value=False)
            self.profile_vars[p_name] = var
            chk = ttk.Checkbutton(self.inner_frame_profiles, text=p_name, variable=var)
            chk.pack(anchor="w", padx=5)
            
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
            
        # 2. Validaciones generales (resto igual...)
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
            "campaign_type": self.combo_camp_type.get()
        }
        
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
        task_title = f"Individual: {locked_profiles[0]}" if mode == "Individual" else f"Distribuido ({len(locked_profiles)} perfiles)"
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
                    lbl_status.config(text=text)
                except tk.TclError:
                    # Widget ya fue destruido
                    task_active['active'] = False
            self.after(0, _update)
            
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
            
        if mode == "Individual":
            runner = AutomationRunner(
                browser_profile=target_profiles[0], # Solo uno
                config=config,
                phone_numbers=phones,
                user_data=user_data,
                contact_data=contact_data,
                campaign=campaign,
                fallback_campaign=fallback_campaign,  # Nueva: campaña de respaldo
                progress_callback=update_ui,
                completion_callback=on_complete
            )
        else:
            runner = DistributedAutomationRunner(
                browser_profiles=target_profiles, # Lista de perfiles
                config=config,
                phone_numbers=phones,
                user_data=user_data,
                contact_data=contact_data,
                campaign=campaign,
                fallback_campaign=fallback_campaign,  # Nueva: campaña de respaldo
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

