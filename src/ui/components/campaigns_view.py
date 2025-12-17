"""
Vista para gestión de campañas.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
from ...services.campaign_service import CampaignService
from ...models.campaign import Campaign
from ...utils.file_utils import copy_image
from ...config.settings import IMAGES_DIR, CAMPAIGN_TYPE_PREDETERMINADA, CAMPAIGN_TYPE_PERSONALIZADA
from ..styles import *


class CampaignEditor(ttk.Frame):
    """Editor de campañas individual (reutilizable)."""
    
    def __init__(self, parent, campaign_type, title_text):
        super().__init__(parent)
        self.campaign_type = campaign_type
        self.title_text = title_text
        self.campaign_service = CampaignService()
        self.current_image = None
        self.image_tk = None
        
        self.setup_ui()
        self.load_campaigns()
        
    def setup_ui(self):
        """Configura la interfaz."""
        # Frame principal
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
        
        # Panel izquierdo (Formulario)
        form_frame = ttk.LabelFrame(main_frame, text="Detalles de Campaña")
        form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING_MEDIUM))
        
        # Título
        ttk.Label(form_frame, text=LBL_CAMPAIGN_TITLE).pack(anchor=tk.W, padx=PADDING_SMALL, pady=(PADDING_SMALL, 0))
        self.entry_title = ttk.Entry(form_frame)
        self.entry_title.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        # Contenido
        ttk.Label(form_frame, text=LBL_CAMPAIGN_CONTENT).pack(anchor=tk.W, padx=PADDING_SMALL)
        self.text_content = tk.Text(form_frame, height=8, font=FONT_NORMAL)
        self.text_content.pack(fill=tk.BOTH, expand=True, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        # Imagen
        img_frame = ttk.Frame(form_frame)
        img_frame.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        btn_img = ttk.Button(img_frame, text=BTN_LOAD_IMAGE, command=self.load_image)
        btn_img.pack(side=tk.LEFT)
        
        self.lbl_img_status = ttk.Label(img_frame, text="Sin imagen")
        self.lbl_img_status.pack(side=tk.LEFT, padx=PADDING_SMALL)
        
        # Preview imagen
        self.preview_lbl = ttk.Label(form_frame)
        self.preview_lbl.pack(pady=PADDING_SMALL)
        
        # Botones acción
        btn_frame = ttk.Frame(form_frame)
        btn_frame.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_MEDIUM)
        
        ttk.Button(btn_frame, text=BTN_SAVE, command=self.save_campaign).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text=BTN_DELETE_CAMPAIGN, command=self.delete_campaign).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Panel derecho (Lista)
        list_frame = ttk.LabelFrame(main_frame, text="Campañas Guardadas")
        list_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0), ipadx=20)
        
        columns = ("Título",)
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("Título", text="Título")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_select)
        
    def load_campaigns(self):
        """Carga lista."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        campaigns = self.campaign_service.load_campaigns(self.campaign_type)
        for cmap in campaigns:
            self.tree.insert("", "end", values=(cmap.title,))
            
    def load_image(self):
        """Carga imagen."""
        file_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if file_path:
            self.current_image_path = file_path
            self.show_preview(file_path)
            self.lbl_img_status.config(text=os.path.basename(file_path))
            
    def show_preview(self, path):
        """Muestra preview."""
        try:
            img = Image.open(path)
            img.thumbnail((150, 150))
            self.image_tk = ImageTk.PhotoImage(img)
            self.preview_lbl.config(image=self.image_tk)
        except Exception as e:
            print(f"Error preview: {e}")
            
    def save_campaign(self):
        """Guarda."""
        title = self.entry_title.get().strip()
        content = self.text_content.get("1.0", tk.END).strip()
        
        if not title or not content:
            messagebox.showerror(MSG_ERROR, "Título y contenido requeridos")
            return
            
        final_img_path = ""
        if hasattr(self, 'current_image_path') and self.current_image_path:
            # Copiar a carpeta interna
            try:
                final_img_path = copy_image(self.current_image_path, IMAGES_DIR)
            except Exception as e:
                messagebox.showerror(MSG_ERROR, f"Error guardando imagen: {e}")
                return
        elif hasattr(self, 'existing_image_path'):
            final_img_path = self.existing_image_path
            
        campaign = Campaign(
            title=title,
            message=content,
            image=final_img_path,
            campaign_type=self.campaign_type
        )
        
        if self.campaign_service.save_campaign(campaign):
            messagebox.showinfo(MSG_SUCCESS, "Campaña guardada")
            self.load_campaigns()
            self.clear_form()
        else:
            messagebox.showerror(MSG_ERROR, "Error al guardar")
            
    def delete_campaign(self):
        """Elimina."""
        selected = self.tree.selection()
        if not selected:
            return
            
        title = self.tree.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirmar", f"Eliminar '{title}'?"):
            if self.campaign_service.delete_campaign(title, self.campaign_type):
                messagebox.showinfo(MSG_SUCCESS, "Eliminada")
                self.load_campaigns()
                self.clear_form()
                
    def on_select(self, event):
        """Selección."""
        selected = self.tree.selection()
        if not selected:
            return
            
        title = self.tree.item(selected[0])["values"][0]
        campaign = self.campaign_service.get_campaign(title, self.campaign_type)
        
        if campaign:
            self.entry_title.delete(0, tk.END)
            self.entry_title.insert(0, campaign.title)
            self.text_content.delete("1.0", tk.END)
            self.text_content.insert("1.0", campaign.message)
            
            if campaign.image and os.path.exists(campaign.image):
                self.existing_image_path = campaign.image
                self.show_preview(campaign.image)
                self.lbl_img_status.config(text=os.path.basename(campaign.image))
            else:
                self.preview_lbl.config(image="")
                self.lbl_img_status.config(text="Sin imagen")
                if hasattr(self, 'existing_image_path'):
                    del self.existing_image_path
                    
    def clear_form(self):
        """Limpia."""
        self.entry_title.delete(0, tk.END)
        self.text_content.delete("1.0", tk.END)
        self.preview_lbl.config(image="")
        self.lbl_img_status.config(text="Sin imagen")
        if hasattr(self, 'current_image_path'):
            del self.current_image_path
        if hasattr(self, 'existing_image_path'):
            del self.existing_image_path


class CampaignsView(ttk.Frame):
    """Vista principal con pestañas para campañas."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        lbl_title = ttk.Label(self, text="Gestión de Campañas", font=FONT_TITLE)
        lbl_title.pack(pady=PADDING_MEDIUM)
        
        tab_control = ttk.Notebook(self)
        
        tab1 = CampaignEditor(tab_control, "campaigns", "Predeterminadas")
        tab2 = CampaignEditor(tab_control, "custom_campaign", "Dinámicas")
        
        tab_control.add(tab1, text="Predeterminadas")
        tab_control.add(tab2, text="Dinámicas")
        
        tab_control.pack(expand=1, fill="both", padx=PADDING_MEDIUM, pady=PADDING_MEDIUM)
