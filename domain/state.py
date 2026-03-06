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
    cards: List[Card] = field(default_factory=list)

    # вспомогательные поля
    zone: Optional[Rect] = None
    last_ocr_time: float = 0.0

@dataclass
class PokerTable:
    players: List[Player] = field(default_factory=list)
    community_cards: List[Card] = field(default_factory=list)