"""
Modelo de datos para campañas.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Campaign:
    """Representa una campaña de marketing."""
    
    title: str
    message: str
    image: str = ""
    campaign_type: str = "campaigns"  # "campaigns" o "custom_campaign"
    
    def to_dict(self):
        """
        Convierte la campaña a un diccionario.
        
        Returns:
            dict: Diccionario con los datos de la campaña
        """
        return {
            "title": self.title,
            "message": self.message,
            "image": self.image
        }
    
    @classmethod
    def from_dict(cls, data, campaign_type="campaigns"):
        """
        Crea una campaña desde un diccionario.
        
        Args:
            data (dict): Diccionario con los datos de la campaña
            campaign_type (str): Tipo de campaña
            
        Returns:
            Campaign: Instancia de Campaign
        """
        return cls(
            title=data.get("title", ""),
            message=data.get("message", ""),
            image=data.get("image", ""),
            campaign_type=campaign_type
        )
    
    def __str__(self):
        """Representación en string de la campaña."""
        return f"{self.title}"
    
    def __eq__(self, other):
        """Compara dos campañas por su título y tipo."""
        if not isinstance(other, Campaign):
            return False
        return self.title == other.title and self.campaign_type == other.campaign_type
    
    def has_image(self):
        """
        Verifica si la campaña tiene una imagen asociada.
        
        Returns:
            bool: True si tiene imagen, False si no
        """
        return bool(self.image and self.image.strip())
