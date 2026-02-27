from dataclasses import dataclass, field
from typing import List

@dataclass
class Card:
    rank: str
    suit: str

@dataclass
class PokerTable:
    hero_cards: List[Card] = field(default_factory=list)  # пока пусто
    hero_position: str = ""  # пока не определяем
    community_cards: List[Card] = field(default_factory=list)