import logging
from typing import Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OverlayData:
    """Данные для отображения в оверлее"""
    # Parsing debug
    hero_cards: str = ""
    hero_position: str = ""
    hero_bet: float = 0.0
    
    # Table state
    blinds: str = ""
    pot: float = 0.0
    street: str = "preflop"
    
    # Players
    active_players: int = 0
    raises_count: int = 0
    
    # Advice
    advice_action: str = ""
    advice_confidence: str = ""
    advice_reason: str = ""
    
    # Status
    is_hero_turn: bool = False
    parsing_status: str = "OK"  # "OK", "ERROR", "WAITING"


class OverlayController:
    """
    Контроллер оверлея.
    PokerStateManager вызывает update(), UI подписывается на изменения.
    """
    
    def __init__(self):
        self._on_update_callback: Optional[Callable[[OverlayData], None]] = None
        self._last_data: Optional[OverlayData] = None
    
    def set_update_callback(self, callback: Callable[[OverlayData], None]):
        """UI регистрирует callback для получения обновлений"""
        self._on_update_callback = callback
    
    def update(self, data: OverlayData):
        """PokerStateManager вызывает при обновлении состояния"""
        # Отправляем в UI только если данные изменились (оптимизация)
        if self._last_data != data and self._on_update_callback:
            self._on_update_callback(data)
            self._last_data = data
    
    def create_overlay_data(self, state_manager) -> OverlayData:
        """Создаёт OverlayData из PokerStateManager"""
        table = state_manager.table
        hero = next((p for p in table.players if p.is_hero), None)
        
        return OverlayData(
            # Hero
            hero_cards=", ".join([f"{c.rank}{c.suit[0]}" for c in hero.cards]) if hero and hero.cards else "",
            hero_position=hero.position if hero else "",
            hero_bet=hero.last_bet if hero else 0.0,
            
            # Table
            blinds=table.blinds_str,
            pot=table.pot,
            street=table.street,
            
            # Players
            active_players=sum(1 for p in table.players if p.is_active),
            raises_count=sum(1 for p in table.players if p.is_active and p.last_bet > table.big_blind * 2),
            
            # Status
            is_hero_turn=table.is_hero_turn,
            parsing_status="OK" if hero and hero.cards else "WAITING"
        )