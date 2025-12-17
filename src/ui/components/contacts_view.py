"""
Vista para gestión de contactos.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from ...services.contact_service import ContactService
from ...models.contact import Contact
from ..styles import *
from ...utils.validators import validate_contact_data


class ContactsView(ttk.Frame):
    """Vista de gestión de contactos."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.contact_service = ContactService()
        self.setup_ui()
        self.load_contacts()
        
    def setup_ui(self):
        """Configura la interfaz gráfica."""
        # Títutlo
        lbl_title = ttk.Label(self, text="Gestión de Contactos", font=FONT_TITLE)
        lbl_title.pack(pady=PADDING_MEDIUM)
        
        # Frame principal dividido
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING_LARGE)
        
        # Frame de lista (Izquierda)
        list_frame = ttk.LabelFrame(main_frame, text="Lista de Contactos")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PADDING_MEDIUM))
        
        # Tabla de contactos
        columns = ("Teléfono", "Nombre")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.heading("Teléfono", text="Número de Teléfono")
        self.tree.heading("Nombre", text="Nombre")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Frame de edición (Derecha)
        edit_frame = ttk.LabelFrame(main_frame, text="Editar / Agregar")
        edit_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(PADDING_MEDIUM, 0))
        
        # Campos
        ttk.Label(edit_frame, text=LBL_PHONE).pack(anchor=tk.W, padx=PADDING_SMALL, pady=(PADDING_MEDIUM, 0))
        self.entry_phone = ttk.Entry(edit_frame)
        self.entry_phone.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        ttk.Label(edit_frame, text=LBL_NAME).pack(anchor=tk.W, padx=PADDING_SMALL)
        self.entry_name = ttk.Entry(edit_frame)
        self.entry_name.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        # Botones
        btn_add = ttk.Button(edit_frame, text=BTN_ADD, command=self.add_contact)
        btn_add.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_LARGE)
        
        btn_update = ttk.Button(edit_frame, text="Actualizar Seleccionado", command=self.update_contact)
        btn_update.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        btn_delete = ttk.Button(edit_frame, text=BTN_DELETE, command=self.delete_contact)
        btn_delete.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
        btn_clear = ttk.Button(edit_frame, text="Limpiar Campos", command=self.clear_fields)
        btn_clear.pack(fill=tk.X, padx=PADDING_SMALL, pady=PADDING_SMALL)
        
    def load_contacts(self):
        """Carga los contactos en la tabla."""
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        contacts = self.contact_service.load_contacts()
        for contact in contacts:
            self.tree.insert("", "end", values=(contact.telefono, contact.nombre))
            
    def on_double_click(self, event):
        """Maneja doble clic en tabla."""
        selected = self.tree.selection()
        if not selected:
            return
            
        item = self.tree.item(selected[0])
        phone, name = item["values"]
        
        self.entry_phone.delete(0, tk.END)
        self.entry_phone.insert(0, str(phone))
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, name)
        
        # Guardar referencia para edición
        self.selected_phone = str(phone)
        
    def clear_fields(self):
        """Limpia los campos."""
        self.entry_phone.delete(0, tk.END)
        self.entry_name.delete(0, tk.END)
        if hasattr(self, 'selected_phone'):
            del self.selected_phone
            
    def add_contact(self):
        """Agrega un contacto nuevo."""
        phone = self.entry_phone.get().strip()
        name = self.entry_name.get().strip()
        
        is_valid, msg = validate_contact_data(phone, name)
        if not is_valid:
            messagebox.showerror(MSG_ERROR, msg)
            return
            
        contact = Contact(telefono=phone, nombre=name)
        if self.contact_service.add_contact(contact):
            messagebox.showinfo(MSG_SUCCESS, "Contacto agregado correctamente")
            self.load_contacts()
            self.clear_fields()
        else:
            messagebox.showerror(MSG_ERROR, "El contacto ya existe o hubo un error")
            
    def update_contact(self):
        """Actualiza el contacto seleccionado."""
        if not hasattr(self, 'selected_phone'):
            messagebox.showwarning(MSG_WARNING, "Seleccione un contacto de la lista primero")
            return
            
        phone = self.entry_phone.get().strip()
        name = self.entry_name.get().strip()
        
        is_valid, msg = validate_contact_data(phone, name)
        if not is_valid:
            messagebox.showerror(MSG_ERROR, msg)
            return
            
        contact = Contact(telefono=phone, nombre=name)
        if self.contact_service.update_contact(self.selected_phone, contact):
            messagebox.showinfo(MSG_SUCCESS, "Contacto actualizado correctamente")
            self.load_contacts()
            self.clear_fields()
        else:
            messagebox.showerror(MSG_ERROR, "Error al actualizar contacto")
            
    def delete_contact(self):
        """Elimina el contacto seleccionado."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning(MSG_WARNING, "Seleccione un contacto para eliminar")
            return
            
        item = self.tree.item(selected[0])
        phone = str(item["values"][0])
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar contacto {phone}?"):
            if self.contact_service.delete_contact(phone):
                messagebox.showinfo(MSG_SUCCESS, "Contacto eliminado")
                self.load_contacts()
                self.clear_fields()
            else:
                messagebox.showerror(MSG_ERROR, "Error al eliminar contacto")
