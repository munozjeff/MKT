"""
Vista para gestión de perfiles de navegador.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from datetime import datetime
from ...services.browser_service import BrowserService
from ...services.whatsapp_service import WhatsAppService
from ...services.google_messages_service import GoogleMessagesService
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
        
        # Tabla de perfiles — columnas independientes para Estado WA y Estado SMS
        columns = ("Nombre", "Estado", "WA", "SMS", "Etiquetas", "Ruta")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("Nombre",   text="Nombre del Perfil")
        self.tree.heading("Estado",   text="Uso")
        self.tree.heading("WA",       text="WhatsApp")
        self.tree.heading("SMS",      text="SMS")
        self.tree.heading("Etiquetas",text="Etiquetas")
        self.tree.heading("Ruta",     text="Ruta de Datos")
        self.tree.column("Nombre",    width=145)
        self.tree.column("Estado",    width=70)
        self.tree.column("WA",        width=100)
        self.tree.column("SMS",       width=100)
        self.tree.column("Etiquetas", width=120)
        self.tree.column("Ruta",      width=200)

        # Estilos de fila
        self.tree.tag_configure("bloq_both",  background="#FFB3B3", foreground="#5C0000")
        self.tree.tag_configure("bloq_sms",   background="#FFD6CC", foreground="#8B0000")
        self.tree.tag_configure("bloqueado",  background="#FFF3CC", foreground="#7A4F00")
        self.tree.tag_configure("disponible", background="",        foreground="")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Menú contextual
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Editar Etiquetas", command=self.edit_tags)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Abrir Navegador (WhatsApp)", command=self.open_profile)
        self.context_menu.add_command(label="Abrir Navegador (Google Messages)", command=self.open_profile_google_messages)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🔒 Alternar Bloqueo WhatsApp", command=self.toggle_wa_blocked)
        self.context_menu.add_command(label="⚠️ Alternar Bloqueo SMS",       command=self.toggle_sms_blocked)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Eliminar Perfil", command=self.delete_profile)
        
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Frame de acciones (Derecha)
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(PADDING_MEDIUM, 0))
        
        # Crear nuevo perfil
        lbl_new = ttk.Label(action_frame, text="Nuevo Perfil (vacío = nombre temporal):")
        lbl_new.pack(anchor=tk.W, pady=(0, 5))
        
        self.entry_name = ttk.Entry(action_frame)
        self.entry_name.pack(fill=tk.X, pady=(0, 10))
        
        btn_create = ttk.Button(action_frame, text="Crear Perfil", command=self.create_profile)
        btn_create.pack(fill=tk.X, pady=(0, 20))
        
        # Separador
        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Acciones sobre perfil seleccionado
        btn_tags = ttk.Button(action_frame, text="Editar Etiquetas", command=self.edit_tags)
        btn_tags.pack(fill=tk.X, pady=5)
        
        btn_open = ttk.Button(action_frame, text="Abrir WhatsApp", command=self.open_profile)
        btn_open.pack(fill=tk.X, pady=5)
        
        btn_open_gm = ttk.Button(action_frame, text="Abrir Google Messages", command=self.open_profile_google_messages)
        btn_open_gm.pack(fill=tk.X, pady=5)
        
        btn_delete = ttk.Button(action_frame, text="Eliminar Perfil", command=self.delete_profile)
        btn_delete.pack(fill=tk.X, pady=5)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Bloqueo manual
        ttk.Label(action_frame, text="Bloqueo manual:", font=("Arial", 8, "bold")).pack(anchor=tk.W)
        btn_toggle_wa = ttk.Button(action_frame, text="🔒 Alternar Bloqueo WA",
                                   command=self.toggle_wa_blocked)
        btn_toggle_wa.pack(fill=tk.X, pady=2)
        btn_toggle_sms = ttk.Button(action_frame, text="⚠️ Alternar Bloqueo SMS",
                                    command=self.toggle_sms_blocked)
        btn_toggle_sms.pack(fill=tk.X, pady=2)

        ttk.Separator(action_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        btn_refresh = ttk.Button(action_frame, text="Actualizar Lista", command=self.load_profiles)
        btn_refresh.pack(fill=tk.X, pady=(0, 5))
        
        btn_export = ttk.Button(action_frame, text="Exportar Bloqueados", command=self.export_blocked_profiles)
        btn_export.pack(fill=tk.X, pady=5)
        
        btn_export_all = ttk.Button(action_frame, text="Exportar Todos", command=self.export_all_profiles)
        btn_export_all.pack(fill=tk.X, pady=5)
        
        # Estadísticas
        self.stats_frame = ttk.LabelFrame(action_frame, text="Estadísticas por Etiqueta")
        self.stats_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        self.stats_text = tk.Text(self.stats_frame, height=10, width=25, font=("Consolas", 10), state='disabled', bg="#f0f0f0")
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _sort_profiles_by_tags(self, profiles):
        """
        Ordena perfiles agrupando por conjunto de etiquetas (frozenset, orden no importa).
        
        Criterio:
          1. Más etiquetas primero (grupos más específicos al inicio).
          2. Dentro del mismo número de etiquetas, ordenar grupos alfabéticamente.
          3. Dentro de cada grupo, ordenar perfiles por nombre.
          4. Perfiles sin etiquetas al final.
        """
        def sort_key(profile):
            tag_set = frozenset(t.upper() for t in profile.tags)
            n_tags = len(tag_set)
            # Negamos n_tags para que más etiquetas vayan primero
            group_label = tuple(sorted(tag_set))  # clave de grupo reproducible
            return (-n_tags, group_label, profile.name.lower())
        
        return sorted(profiles, key=sort_key)

    def load_profiles(self):
        """Carga los perfiles en la tabla con columnas independientes de estado WA y SMS."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        profiles = self.browser_service.get_all_profiles()
        profiles_sorted = self._sort_profiles_by_tags(profiles)
        
        for profile in profiles_sorted:
            is_active  = self.browser_service.is_profile_active(profile.name)
            upper_tags = [t.upper() for t in profile.tags]

            is_wa_blocked  = "BLOQUEADO"     in upper_tags
            is_sms_blocked = "BLOQUEADO_SMS" in upper_tags

            # Columna "Uso" (solo indica si el perfil está ocupado por una tarea en curso)
            uso = "Ocupado" if is_active else "Libre"

            # Columna WhatsApp
            wa_status = "🔒 Bloqueado" if is_wa_blocked else "✅ Disponible"

            # Columna SMS
            sms_status = "⚠️ Bloqueado" if is_sms_blocked else "✅ Disponible"

            # Etiquetas: excluir las que ya tienen columna propia
            display_tags = [
                t for t in profile.tags
                if t.upper() not in ("BLOQUEADO", "BLOQUEADO_SMS")
            ]
            tags_str = ", ".join(sorted(display_tags)) if display_tags else ""

            short_path = "..." + profile.path[-28:] if len(profile.path) > 28 else profile.path

            # Color de fila según estado de bloqueo
            if is_wa_blocked and is_sms_blocked:
                row_tag = "bloq_both"
            elif is_sms_blocked:
                row_tag = "bloq_sms"
            elif is_wa_blocked:
                row_tag = "bloqueado"
            else:
                row_tag = "disponible"

            self.tree.insert("", "end",
                             values=(profile.name, uso, wa_status, sms_status, tags_str, short_path),
                             tags=(row_tag,))
            
        # Estadísticas (solo etiquetas que no sean de bloqueo)
        tag_counts = {}
        SKIP = {"BLOQUEADO", "BLOQUEADO_SMS"}
        for profile in profiles:
            visible = [t for t in profile.tags if t.upper() not in SKIP]
            if not visible:
                tag_counts["(Sin etiqueta)"] = tag_counts.get("(Sin etiqueta)", 0) + 1
            else:
                for tag in visible:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        self.update_stats(tag_counts)
            
    def show_context_menu(self, event):
        """Muestra el menú contextual."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def toggle_wa_blocked(self):
        """Alterna manualmente el bloqueo de WhatsApp para el/los perfiles seleccionados."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(MSG_WARNING, "Seleccione al menos un perfil")
            return
        all_profiles = self.browser_service.get_all_profiles()
        for item_id in selected_items:
            name = self.tree.item(item_id)["values"][0]
            profile = next((p for p in all_profiles if p.name == name), None)
            if not profile:
                continue
            if "BLOQUEADO" in [t.upper() for t in profile.tags]:
                profile.remove_tag("BLOQUEADO")
                print(f"[Navegadores] {name}: BLOQUEADO WA eliminado manualmente")
            else:
                profile.add_tag("BLOQUEADO")
                print(f"[Navegadores] {name}: BLOQUEADO WA agregado manualmente")
        self.load_profiles()

    def toggle_sms_blocked(self):
        """Alterna manualmente el bloqueo de SMS para el/los perfiles seleccionados."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(MSG_WARNING, "Seleccione al menos un perfil")
            return
        all_profiles = self.browser_service.get_all_profiles()
        for item_id in selected_items:
            name = self.tree.item(item_id)["values"][0]
            profile = next((p for p in all_profiles if p.name == name), None)
            if not profile:
                continue
            if "BLOQUEADO_SMS" in [t.upper() for t in profile.tags]:
                profile.remove_tag("BLOQUEADO_SMS")
                print(f"[Navegadores] {name}: BLOQUEADO_SMS eliminado manualmente")
            else:
                profile.add_tag("BLOQUEADO_SMS")
                print(f"[Navegadores] {name}: BLOQUEADO_SMS agregado manualmente")
        self.load_profiles()

    def create_profile(self):
        """Crea un nuevo perfil. Si el nombre está vacío genera uno temporal."""
        name = self.entry_name.get().strip()
        if not name:
            # Nombre temporal con sufijo de tiempo; el '_' activa el renombrado automático
            name = f"perfil_{datetime.now().strftime('%H%M%S')}"
            
        if self.browser_service.create_profile(name):
            messagebox.showinfo(MSG_SUCCESS, f"Perfil '{name}' creado correctamente")
            self.entry_name.delete(0, tk.END)
            self.load_profiles()
        else:
            messagebox.showerror(MSG_ERROR, "No se pudo crear el perfil (¿ya existe?)")
            
    def delete_profile(self):
        """Elimina el/los perfil(es) seleccionado(s)."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(MSG_WARNING, "Seleccione al menos un perfil para eliminar")
            return
            
        profiles_to_delete = []
        for item_id in selected_items:
            item = self.tree.item(item_id)
            profiles_to_delete.append(item["values"][0])
            
        count = len(profiles_to_delete)
        msg = f"¿Eliminar {count} perfil(es)?\nSe perderán todos los datos de sesión de:\n"
        # Mostrar los primeros 5 nombres
        msg += "\n".join(profiles_to_delete[:5])
        if count > 5:
            msg += f"\n... y {count - 5} más."
            
        if messagebox.askyesno("Confirmar Eliminación", msg):
            success_count = 0
            for name in profiles_to_delete:
                if self.browser_service.delete_profile(name):
                    success_count += 1
                else:
                    print(f"No se pudo eliminar {name} (posiblemente en uso)")
            
            if success_count > 0:
                messagebox.showinfo(MSG_SUCCESS, f"Se eliminaron {success_count} perfiles.")
                self.load_profiles()
            else:
                messagebox.showerror(MSG_ERROR, "No se pudo eliminar ningún perfil (verifique si están en uso).")

    def open_profile(self):
        """Abre el navegador con el perfil seleccionado para configuración manual."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(MSG_WARNING, "Seleccione un perfil para abrir")
            return
            
        for item_id in selected_items:
            item = self.tree.item(item_id)
            name = item["values"][0]
            
            if self.browser_service.is_profile_active(name):
                print(f"Perfil {name} ya está en uso, omitiendo.")
                continue
                
            # Abrir en hilo separado
            threading.Thread(target=self._run_browser_manual, args=(name,)).start()
            # Pequeño delay para no saturar si son muchos
            time.sleep(1)

    def open_profile_google_messages(self):
        """Abre el navegador con el perfil seleccionado directamente en Google Messages."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(MSG_WARNING, "Seleccione un perfil para abrir")
            return

        for item_id in selected_items:
            item = self.tree.item(item_id)
            name = item["values"][0]

            if self.browser_service.is_profile_active(name):
                print(f"Perfil {name} ya está en uso, omitiendo.")
                continue

            threading.Thread(
                target=self._run_browser_google_messages, args=(name,)
            ).start()
            time.sleep(1)

    def _run_browser_google_messages(self, profile_name):
        """Abre el navegador con Google Messages y mantiene el perfil bloqueado mientras Chrome esté abierto.
        Si el perfil tiene la etiqueta BLOQUEADO_SMS y el usuario se re-autentica exitosamente, se elimina
        automáticamente la etiqueta para que el perfil vuelva a estar disponible para enviar SMS.
        """
        if not self.browser_service.lock_profile(profile_name):
            return

        try:
            self.after(0, self.load_profiles)

            profiles = self.browser_service.get_all_profiles()
            profile = next((p for p in profiles if p.name == profile_name), None)

            if not profile:
                return

            # Verificar si el perfil está marcado como BLOQUEADO_SMS
            was_qr_blocked = "BLOQUEADO_SMS" in [t.upper() for t in profile.tags]
            unblocked_done = False

            service = GoogleMessagesService()
            if service.initialize_driver(profile.path):
                while True:
                    time.sleep(1)
                    try:
                        service.driver.title  # Verifica si Chrome sigue vivo
                    except Exception:
                        break

                    # Si el perfil estaba bloqueado por QR, verificar si ya se re-autenticó
                    if was_qr_blocked and not unblocked_done:
                        try:
                            if service.is_logged_in():
                                profile.remove_tag("BLOQUEADO_SMS")
                                unblocked_done = True
                                print(f"[GoogleMessages] Perfil '{profile_name}' re-autenticado — BLOQUEADO_SMS eliminado.")
                                self.after(0, self.load_profiles)
                        except Exception as e:
                            print(f"[GoogleMessages] Error verificando re-auth: {e}")

        except Exception as e:
            print(f"Error abriendo Google Messages: {e}")
        finally:
            self.browser_service.unlock_profile(profile_name)
            self.after(0, self.load_profiles)

    def edit_tags(self):
        """Abre diálogo para editar etiquetas (soporta selección múltiple)."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning(MSG_WARNING, "Seleccione al menos un perfil para editar etiquetas")
            return
            
        profile_names = []
        for item_id in selected_items:
            item = self.tree.item(item_id)
            profile_names.append(item["values"][0])
            
        # Dialogo
        dialog = tk.Toplevel(self)
        title_text = f"Etiquetas: {profile_names[0]}" if len(profile_names) == 1 else f"Etiquetas ({len(profile_names)} perfiles)"
        dialog.title(title_text)
        dialog.geometry("450x250")
        dialog.transient(self)
        dialog.grab_set()
        
        # Info
        ttk.Label(dialog, text="Etiquetas (separadas por coma):").pack(pady=(10, 5))
        
        # Entrada
        entry = ttk.Entry(dialog, width=50)
        entry.pack(pady=5, padx=20)
        
        # Si es solo uno, pre-cargar sus etiquetas
        single_profile = None
        if len(profile_names) == 1:
            all_profiles = self.browser_service.get_all_profiles()
            single_profile = next((p for p in all_profiles if p.name == profile_names[0]), None)
            if single_profile and single_profile.tags:
                entry.insert(0, ", ".join(single_profile.tags))
        
        entry.focus()
        
        # Opciones para múltiple selección
        action_var = tk.StringVar(value="overwrite")
        
        if len(profile_names) > 1:
            frame_opts = ttk.LabelFrame(dialog, text="Acción")
            frame_opts.pack(fill=tk.X, padx=20, pady=10)
            
            ttk.Radiobutton(frame_opts, text="Sobrescribir (reemplazar existentes)", variable=action_var, value="overwrite").pack(anchor="w", padx=5, pady=2)
            ttk.Radiobutton(frame_opts, text="Añadir (mantener existentes)", variable=action_var, value="add").pack(anchor="w", padx=5, pady=2)
        
        def save():
            new_tags_str = entry.get()
            new_tags = [t.strip() for t in new_tags_str.split(',') if t.strip()]
            action = action_var.get()
            
            all_profiles = self.browser_service.get_all_profiles()
            # Filiprar solo los seleccionados
            target_profiles = [p for p in all_profiles if p.name in profile_names]
            
            for profile in target_profiles:
                if len(profile_names) == 1 or action == "overwrite":
                    profile.tags = new_tags
                elif action == "add":
                    # Añadir sin duplicar
                    current_set = set(profile.tags)
                    for t in new_tags:
                        current_set.add(t)
                    profile.tags = sorted(list(current_set))
                    
                profile.save_metadata()
                
            self.load_profiles()
            dialog.destroy()
            messagebox.showinfo(MSG_SUCCESS, "Etiquetas actualizadas")
            
        ttk.Button(dialog, text="Guardar", command=save).pack(pady=20)
        
    def _check_whatsapp_logged_in(self, service) -> bool:
        """Verifica si WhatsApp está disponible buscando el botón Nuevo chat.
        
        Intenta primero con CSS selector y luego con XPath como fallback.
        """
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            short_wait = WebDriverWait(service.driver, 3)
            try:
                short_wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[title='Nuevo chat'], [aria-label='Nuevo chat']")
                ))
                return True
            except:
                service.driver.find_element(
                    By.XPATH, "//span[@data-icon='new-chat-outline']/ancestor::button[1]"
                )
                return True
        except:
            return False

    def _rename_profile_with_whatsapp_number(self, service, profile_name: str) -> tuple:
        """
        Flujo reutilizable para renombrar un perfil usando el número de WhatsApp.

        Ciclo completo para evitar WinError 5 (acceso denegado por lock de Chrome):
          1. Verifica que el nombre contenga '_'; si no, se omite sin tocar nada.
          2. Extrae el número de teléfono (browser abierto — lectura, sin problema).
          3. Cierra el navegador para liberar el lock del directorio.
          4. Renombra el directorio en disco.
          5. Reabre el navegador con la nueva ruta (o la anterior si falló).

        Args:
            service: Instancia activa de WhatsAppService con driver abierto.
            profile_name (str): Nombre actual del perfil.

        Returns:
            tuple(str, WhatsAppService): (nombre_final, nueva_instancia_service)
            El llamador DEBE reemplazar su variable `service` con la retornada.
        """
        # Regla: solo tiene sentido si hay '_' en el nombre
        if '_' not in profile_name:
            print(f"[RenombrePerfil] '{profile_name}' no contiene '_', se omite renombrado.")
            return profile_name, service

        print(f"[RenombrePerfil] Iniciando flujo de renombrado para '{profile_name}'...")

        try:
            # ── Paso 1: Breve pausa para que el navbar termine de renderizar
            print("[RenombrePerfil] Esperando 1s para que el navbar de WhatsApp cargue...")
            time.sleep(1)

            # ── Paso 2: Extraer número (browser abierto, sólo lectura) ──────────────
            phone_number = service.extract_whatsapp_phone_number()

            if not phone_number:
                print("[RenombrePerfil] No se obtuvo número; renombrado cancelado.")
                return profile_name, service

            # ── Paso 2: Cerrar browser para liberar lock del directorio ─────────────
            print("[RenombrePerfil] Cerrando navegador para liberar lock de directorio...")
            service.close()
            time.sleep(2)  # Dar tiempo al SO para soltar todos los handles

            # ── Paso 3: Renombrar en disco (browser ya cerrado) ────────────────────
            success, result = self.browser_service.rename_profile_with_phone(
                current_name=profile_name,
                phone_number=phone_number
            )

            # El perfil a reabrir es el nuevo nombre si tuvo éxito, o el original si falló
            target_name = result if success else profile_name

            if success:
                print(f"[RenombrePerfil] ✅ Perfil renombrado: '{profile_name}' → '{target_name}'")
                self.after(0, self.load_profiles)
            else:
                print(f"[RenombrePerfil] ⚠️ Renombrado fallido: {result}. Reabriendo con nombre original.")

            # ── Paso 4: Reabrir navegador con la ruta correcta ────────────────────
            all_profiles = self.browser_service.get_all_profiles()
            target_profile = next((p for p in all_profiles if p.name == target_name), None)

            new_service = WhatsAppService()
            if target_profile:
                print(f"[RenombrePerfil] Reabriendo navegador con perfil '{target_name}'...")
                new_service.initialize_driver(target_profile.path)
            else:
                print(f"[RenombrePerfil] ⚠️ No se encontró perfil '{target_name}' para reabrir.")

            return target_name, new_service

        except Exception as e:
            print(f"[RenombrePerfil] ❌ Error en flujo de renombrado: {e}")
            return profile_name, service

    def _run_browser_manual(self, profile_name):
        """Ejecuta el navegador manualmente, maneja bloqueo y renombrado por número de teléfono."""
        if not self.browser_service.lock_profile(profile_name):
            return

        # Usamos una variable mutable para que el bloque finally use el nombre actualizado
        # después de un posible renombrado.
        current_name = [profile_name]  # Lista de un elemento para mutabilidad en closures

        try:
            # Actualizar UI en hilo principal
            self.after(0, self.load_profiles)

            profiles = self.browser_service.get_all_profiles()
            profile = next((p for p in profiles if p.name == profile_name), None)

            if not profile:
                return

            # Verificar si el perfil estaba bloqueado al iniciarse
            was_blocked = "BLOQUEADO" in profile.tags
            unblocked_done = False
            renamed_done = False

            service = WhatsAppService()
            if service.initialize_driver(profile.path):
                while True:
                    time.sleep(1)
                    try:
                        # Verificar si el navegador sigue vivo
                        service.driver.title
                    except:
                        break

                    # --- Lógica de desbloqueo y/o renombrado ---
                    # Solo intenta si la sesión está activa y el botón Nuevo chat es visible
                    if not unblocked_done or not renamed_done:
                        try:
                            session_ok = service.is_session_active()
                            if session_ok and self._check_whatsapp_logged_in(service):

                                # 1. Desbloquear etiqueta BLOQUEADO (si aplica)
                                if was_blocked and not unblocked_done:
                                    profile.remove_tag("BLOQUEADO")
                                    unblocked_done = True
                                    print(f"[Navegadores] Perfil '{current_name[0]}' desbloqueado exitosamente.")
                                    self.after(0, self.load_profiles)

                                # 2. Renombrar perfil con número de teléfono (si aplica)
                                if not renamed_done:
                                    # Retorna (nuevo_nombre, nueva_instancia_service)
                                    # El browser se cierra y reabre dentro del flujo
                                    new_name, service = self._rename_profile_with_whatsapp_number(
                                        service=service,
                                        profile_name=current_name[0]
                                    )
                                    renamed_done = True  # Solo intentamos UNA vez
                                    if new_name != current_name[0]:
                                        # El nombre cambió: actualizar referencia para el finally
                                        current_name[0] = new_name

                        except Exception as e:
                            print(f"Error en verificación pós-sesión: {e}")

        except Exception as e:
            print(f"Error abriendo navegador: {e}")
        finally:
            # Usamos current_name[0] porque puede haber cambiado si se renombró
            self.browser_service.unlock_profile(current_name[0])
            # Actualizar UI
            self.after(0, self.load_profiles)

    def export_blocked_profiles(self):
        """Exporta los perfiles con etiqueta BLOQUEADO o BLOQUEADO_SMS, con el mismo orden de agrupación."""
        all_profiles = self.browser_service.get_all_profiles()
        blocked = [
            p for p in all_profiles
            if any(t.upper() in ("BLOQUEADO", "BLOQUEADO_SMS") for t in p.tags)
        ]
        
        if not blocked:
            messagebox.showinfo("Exportar", "No hay perfiles con la etiqueta 'BLOQUEADO'.")
            return
            
        blocked_sorted = self._sort_profiles_by_tags(blocked)
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Guardar perfiles bloqueados",
            initialfile="perfiles_bloqueados.txt"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for p in blocked_sorted:
                        tags_str = ", ".join(sorted(p.tags)) if p.tags else ""
                        line = f"{p.name}\t{tags_str}" if tags_str else p.name
                        f.write(line + "\n")
                messagebox.showinfo(MSG_SUCCESS, f"Se exportaron {len(blocked_sorted)} perfiles a:\n{file_path}")
            except Exception as e:
                messagebox.showerror(MSG_ERROR, f"Error al exportar: {e}")

    def export_all_profiles(self):
        """Exporta todos los perfiles con el mismo orden de agrupación por etiquetas."""
        profiles = self.browser_service.get_all_profiles()
        
        if not profiles:
            messagebox.showinfo("Exportar", "No hay perfiles disponibles para exportar.")
            return
            
        profiles_sorted = self._sort_profiles_by_tags(profiles)
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            title="Guardar todos los perfiles",
            initialfile="todos_los_perfiles.txt"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for p in profiles_sorted:
                        tags_str = ", ".join(sorted(p.tags)) if p.tags else ""
                        line = f"{p.name}\t{tags_str}" if tags_str else p.name
                        f.write(line + "\n")
                messagebox.showinfo(MSG_SUCCESS, f"Se exportaron {len(profiles_sorted)} perfiles a:\n{file_path}")
            except Exception as e:
                messagebox.showerror(MSG_ERROR, f"Error al exportar: {e}")

    def update_stats(self, tag_counts):
        """Actualiza el widget de estadísticas."""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)
        
        if not tag_counts:
            self.stats_text.insert(tk.END, "No hay perfiles.")
        else:
            # Ordenar por nombre de etiqueta
            sorted_tags = sorted(tag_counts.items(), key=lambda x: x[0].lower())
            for tag, count in sorted_tags:
                self.stats_text.insert(tk.END, f"• {tag}: {count}\n")
                
        self.stats_text.config(state='disabled')
