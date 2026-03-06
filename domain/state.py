from dataclasses import dataclass, field
from typing import List

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
    cards: List[Card] = field(default_factory=list)

@dataclass
class PokerTable:
    players: List[Player] = field(default_factory=list)
    community_cards: List[Card] = field(default_factory=list)