from dataclasses import dataclass, field
from typing import List, Optional

from domain.geometry import Rect

@dataclass
class Action:
    player_seat: int
    action: str   # "fold", "call", "raise", "check"
    amount: float = 0.0

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

    # вспомогательные поля
    zone: Optional[Rect] = None
    last_ocr_time: float = 0.0

@dataclass
class PokerTable:
    players: List[Player] = field(default_factory=list)
    community_cards: List[Card] = field(default_factory=list)
    actions: List[Action] = field(default_factory=list)
    pot: float = 0.0
    street: str = "preflop"  # preflop, flop, turn, river