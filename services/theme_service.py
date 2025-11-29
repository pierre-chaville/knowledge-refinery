"""Business logic for themes"""
from typing import List, Optional
from sqlmodel import Session
from db import crud
from db.models import Theme

class ThemeService:
    """Service for theme operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_theme(self, name: str) -> Theme:
        """Create a new theme"""
        return crud.create_theme(self.session, name)
    
    def get_theme(self, theme_id: int) -> Optional[Theme]:
        """Get theme by ID"""
        return crud.get_theme(self.session, theme_id)
    
    def get_all_themes(self) -> List[Theme]:
        """Get all themes"""
        return crud.get_all_themes(self.session)
    
    def get_themes_by_ids(self, theme_ids: List[int]) -> List[Theme]:
        """Get themes by list of IDs"""
        return crud.get_themes_by_ids(self.session, theme_ids)
    
    def update_theme(self, theme_id: int, name: str) -> Optional[Theme]:
        """Update a theme"""
        return crud.update_theme(self.session, theme_id, name)
    
    def delete_theme(self, theme_id: int) -> bool:
        """Delete a theme"""
        return crud.delete_theme(self.session, theme_id)

