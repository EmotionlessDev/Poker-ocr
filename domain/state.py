from dataclasses import dataclass, field
from typing import List, Optional
from domain.geometry import Rect

@dataclass
class Card:
    rank: str
    suit: str

@dataclass
class Player:
    seat: int
    nickname: str = ""
    stack: float = 0.0
    position: str = ""
    is_hero: bool = False
    is_button: bool = False
    is_active: bool = False
    cards: List[Card] = field(default_factory=list)
    last_bet: float = 0.0
    zone: Optional[Rect] = None
    last_ocr_time: float = 0.0

@dataclass
class PreflopActionInfo:
    is_open_raise: bool = False
    is_3bet_pot: bool = False
    is_4bet_pot: bool = False
    
    first_raiser_seat: Optional[int] = None
    first_raiser_position: Optional[str] = None
    first_raiser_amount_bb: float = 0.0
    
    three_bettor_seat: Optional[int] = None
    three_bettor_position: Optional[str] = None
    three_bet_amount_bb: float = 0.0
    
    four_bettor_seat: Optional[int] = None
    four_bet_amount_bb: float = 0.0
    
    callers: List[int] = field(default_factory=list)
    total_raises: int = 0
    hero_to_call_bb: float = 0.0
    hero_last_action: Optional[str] = None

@dataclass
class PokerTable:
    players: List[Player] = field(default_factory=list)
    community_cards: List[Card] = field(default_factory=list)
    
    is_hero_turn: bool = False
    last_hero_turn_check: float = 0.0

    # Блайнды
    small_blind: float = 0.0
    big_blind: float = 0.0
    
    def set_blinds(self, sb: float, bb: float):
        """Устанавливает блайнды"""
        self.small_blind = sb
        self.big_blind = bb
    
    @property
    def blinds_str(self) -> str:
        """Возвращает строку вида "100/200" """
        if self.small_blind > 0 and self.big_blind > 0:
            return f"{int(self.small_blind)}/{int(self.big_blind)}"
        return "Unknown"
    
    # Preflop информация
    preflop_action: PreflopActionInfo = field(default_factory=PreflopActionInfo)
    
    pot: float = 0.0
    street: str = "preflop"