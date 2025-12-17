"""
Servicio para gestión de contactos.
"""
import json
import os
from typing import List, Optional
from ..models.contact import Contact
from ..config.settings import CONTACTS_FILE, ensure_directories


class ContactService:
    """Servicio para gestionar contactos."""
    
    def __init__(self):
        """Inicializa el servicio de contactos."""
        ensure_directories()
        self.contacts_file = CONTACTS_FILE
    
    def load_contacts(self) -> List[Contact]:
        """
        Carga todos los contactos desde el archivo JSON.
        
        Returns:
            List[Contact]: Lista de contactos
        """
        if not os.path.exists(self.contacts_file):
            return []
        
        try:
            with open(self.contacts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Contact.from_dict(item) for item in data]
        except Exception as e:
            print(f"Error al cargar contactos: {e}")
            return []
    
    def save_contacts(self, contacts: List[Contact]) -> bool:
        """
        Guarda la lista de contactos en el archivo JSON.
        
        Args:
            contacts (List[Contact]): Lista de contactos a guardar
            
        Returns:
            bool: True si se guardó correctamente, False si no
        """
        try:
            os.makedirs(os.path.dirname(self.contacts_file), exist_ok=True)
            with open(self.contacts_file, "w", encoding="utf-8") as f:
                data = [contact.to_dict() for contact in contacts]
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar contactos: {e}")
            return False
    
    def add_contact(self, contact: Contact) -> bool:
        """
        Agrega un nuevo contacto.
        
        Args:
            contact (Contact): Contacto a agregar
            
        Returns:
            bool: True si se agregó correctamente, False si ya existe
        """
        contacts = self.load_contacts()
        
        # Verificar si el contacto ya existe
        if any(c.telefono == contact.telefono for c in contacts):
            return False
        
        contacts.append(contact)
        return self.save_contacts(contacts)
    
    def update_contact(self, old_phone: str, new_contact: Contact) -> bool:
        """
        Actualiza un contacto existente.
        
        Args:
            old_phone (str): Número de teléfono del contacto a actualizar
            new_contact (Contact): Nuevos datos del contacto
            
        Returns:
            bool: True si se actualizó correctamente, False si no se encontró
        """
        contacts = self.load_contacts()
        
        for i, contact in enumerate(contacts):
            if contact.telefono == old_phone:
                contacts[i] = new_contact
                return self.save_contacts(contacts)
        
        return False
    
    def delete_contact(self, phone: str) -> bool:
        """
        Elimina un contacto por su número de teléfono.
        
        Args:
            phone (str): Número de teléfono del contacto a eliminar
            
        Returns:
            bool: True si se eliminó correctamente, False si no se encontró
        """
        contacts = self.load_contacts()
        original_count = len(contacts)
        
        contacts = [c for c in contacts if c.telefono != phone]
        
        if len(contacts) < original_count:
            return self.save_contacts(contacts)
        
        return False
    
    def get_contact(self, phone: str) -> Optional[Contact]:
        """
        Obtiene un contacto específico por su número de teléfono.
        
        Args:
            phone (str): Número de teléfono del contacto
            
        Returns:
            Optional[Contact]: Contacto si se encuentra, None si no
        """
        contacts = self.load_contacts()
        
        for contact in contacts:
            if contact.telefono == phone:
                return contact
        
        return None
    
    def get_phone_numbers(self) -> List[str]:
        """
        Obtiene solo los números de teléfono de todos los contactos.
        
        Returns:
            List[str]: Lista de números de teléfono
        """
        contacts = self.load_contacts()
        return [contact.telefono for contact in contacts]

    def interpolate_contacts(self, original_list: List[str], interval: int) -> List[str]:
        """
        Interpola contactos guardados en la lista original cada 'interval' posiciones.
        
        Args:
            original_list (List[str]): Lista original de números
            interval (int): Intervalo de inserción
            
        Returns:
            List[str]: Nueva lista con contactos interpolados
        """
        contact_list = self.get_phone_numbers()
        if not contact_list:
            return original_list
            
        result = []
        contact_index = 0
        for i, phone in enumerate(original_list):
            result.append(phone)
            # Insertar un número de contacto cada intervalo
            if (i + 1) % interval == 0:
                result.append(contact_list[contact_index])
                contact_index = (contact_index + 1) % len(contact_list)
        return result
