"""
Servicio para gestión de campañas.
"""
import json
import os
from typing import List, Optional
from ..models.campaign import Campaign
from ..config.settings import CAMPAIGNS_DIR, ensure_directories
from ..utils.message_templates import replace_variables


class CampaignService:
    """Servicio para gestionar campañas."""
    
    def __init__(self):
        """Inicializa el servicio de campañas."""
        ensure_directories()
        self.campaigns_dir = CAMPAIGNS_DIR
    
    def _get_campaign_file(self, campaign_type: str) -> str:
        """
        Obtiene la ruta del archivo de campañas según el tipo.
        
        Args:
            campaign_type (str): Tipo de campaña ("campaigns" o "custom_campaign")
            
        Returns:
            str: Ruta del archivo
        """
        return os.path.join(self.campaigns_dir, f"{campaign_type}.json")
    
    def load_campaigns(self, campaign_type: str = "campaigns") -> List[Campaign]:
        """
        Carga todas las campañas de un tipo específico.
        
        Args:
            campaign_type (str): Tipo de campaña a cargar
            
        Returns:
            List[Campaign]: Lista de campañas
        """
        campaign_file = self._get_campaign_file(campaign_type)
        
        if not os.path.exists(campaign_file):
            return []
        
        try:
            with open(campaign_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Campaign.from_dict(item, campaign_type) for item in data]
        except Exception as e:
            print(f"Error al cargar campañas: {e}")
            return []
    
    def save_campaigns(self, campaigns: List[Campaign], campaign_type: str = "campaigns") -> bool:
        """
        Guarda la lista de campañas en el archivo JSON.
        
        Args:
            campaigns (List[Campaign]): Lista de campañas a guardar
            campaign_type (str): Tipo de campaña
            
        Returns:
            bool: True si se guardó correctamente, False si no
        """
        try:
            campaign_file = self._get_campaign_file(campaign_type)
            os.makedirs(os.path.dirname(campaign_file), exist_ok=True)
            
            with open(campaign_file, "w", encoding="utf-8") as f:
                data = [campaign.to_dict() for campaign in campaigns]
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error al guardar campañas: {e}")
            return False
    
    def save_campaign(self, campaign: Campaign) -> bool:
        """
        Guarda o actualiza una campaña.
        
        Args:
            campaign (Campaign): Campaña a guardar
            
        Returns:
            bool: True si se guardó correctamente, False si no
        """
        campaigns = self.load_campaigns(campaign.campaign_type)
        
        # Verificar si la campaña ya existe y actualizarla
        campaign_exists = False
        for i, existing_campaign in enumerate(campaigns):
            if existing_campaign.title == campaign.title:
                campaigns[i] = campaign
                campaign_exists = True
                break
        
        # Si no existe, añadir la nueva campaña
        if not campaign_exists:
            campaigns.append(campaign)
        
        return self.save_campaigns(campaigns, campaign.campaign_type)
    
    def delete_campaign(self, title: str, campaign_type: str = "campaigns") -> bool:
        """
        Elimina una campaña por su título.
        
        Args:
            title (str): Título de la campaña a eliminar
            campaign_type (str): Tipo de campaña
            
        Returns:
            bool: True si se eliminó correctamente, False si no se encontró
        """
        campaigns = self.load_campaigns(campaign_type)
        original_count = len(campaigns)
        
        campaigns = [c for c in campaigns if c.title != title]
        
        if len(campaigns) < original_count:
            return self.save_campaigns(campaigns, campaign_type)
        
        return False
    
    def get_campaign(self, title: str, campaign_type: str = "campaigns") -> Optional[Campaign]:
        """
        Obtiene una campaña específica por su título.
        
        Args:
            title (str): Título de la campaña
            campaign_type (str): Tipo de campaña
            
        Returns:
            Optional[Campaign]: Campaña si se encuentra, None si no
        """
        campaigns = self.load_campaigns(campaign_type)
        
        for campaign in campaigns:
            if campaign.title == title:
                return campaign
        
        return None
    
    def get_campaign_titles(self, campaign_type: str = "campaigns") -> List[str]:
        """
        Obtiene solo los títulos de las campañas.
        
        Args:
            campaign_type (str): Tipo de campaña
            
        Returns:
            List[str]: Lista de títulos
        """
        campaigns = self.load_campaigns(campaign_type)
        return [campaign.title for campaign in campaigns]
    
    def generate_dynamic_message(self, template: str, variables: dict, default_campaign: str = "") -> str:
        """
        Genera un mensaje dinámico reemplazando variables en la plantilla.
        
        Args:
            template (str): Plantilla del mensaje con variables [variable]
            variables (dict): Diccionario con valores de las variables
            default_campaign (str): Mensaje predeterminado si falta alguna variable
            
        Returns:
            str: Mensaje con variables reemplazadas
        """
        return replace_variables(template, variables, default_campaign)
