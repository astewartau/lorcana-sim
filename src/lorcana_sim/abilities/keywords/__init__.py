"""Keyword ability implementations and registry."""

from typing import Dict, Type, Optional
from ...models.abilities.base_ability import KeywordAbility, AbilityType

class UnknownKeywordAbility(KeywordAbility):
    """Fallback for unknown keyword abilities."""
    
    def can_activate(self, game_state) -> bool:
        return False
    
    def execute(self, game_state, targets) -> None:
        pass

class KeywordRegistry:
    """Registry of all keyword ability implementations"""
    
    _implementations: Dict[str, Type[KeywordAbility]] = {}
    
    @classmethod
    def register(cls, keyword: str, implementation: Type[KeywordAbility]):
        """Register a keyword implementation"""
        cls._implementations[keyword] = implementation
    
    @classmethod
    def get_implementation(cls, keyword: str) -> Type[KeywordAbility]:
        """Get the implementation class for a keyword"""
        return cls._implementations.get(keyword, UnknownKeywordAbility)
    
    @classmethod
    def create_keyword_ability(cls, keyword: str, value: Optional[int] = None, 
                             **kwargs) -> KeywordAbility:
        """Factory method to create keyword ability instances"""
        impl_class = cls.get_implementation(keyword)
        return impl_class(
            name=keyword,
            type=AbilityType.KEYWORD,
            effect=f'{keyword} keyword ability',
            full_text=kwargs.get('full_text', ''),
            keyword=keyword,
            value=value
        )
    
    @classmethod
    def get_registered_keywords(cls) -> list[str]:
        """Get list of all registered keywords"""
        return list(cls._implementations.keys())

# Import and register keyword implementations
from .singer import SingerAbility
from .evasive import EvasiveAbility
from .bodyguard import BodyguardAbility
from .shift import ShiftAbility
from .support import SupportAbility
from .ward import WardAbility
from .rush import RushAbility
from .resist import ResistAbility

KeywordRegistry.register('Singer', SingerAbility)
KeywordRegistry.register('Evasive', EvasiveAbility)
KeywordRegistry.register('Bodyguard', BodyguardAbility)
KeywordRegistry.register('Shift', ShiftAbility)
KeywordRegistry.register('Support', SupportAbility)
KeywordRegistry.register('Ward', WardAbility)
KeywordRegistry.register('Rush', RushAbility)
KeywordRegistry.register('Resist', ResistAbility)

__all__ = [
    'KeywordRegistry', 'SingerAbility', 'EvasiveAbility', 'BodyguardAbility',
    'ShiftAbility', 'SupportAbility', 'WardAbility', 'RushAbility', 'ResistAbility'
]