from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np
from domain.state import PokerTable, Player
from domain.geometry import Rect, Point


class BaseRoom(ABC):
    
    def __init__(self, seats: int, hero_nickname: str):
        self.seats = seats
        self.hero_nickname = hero_nickname
        self.table = PokerTable(players=[Player(seat=i) for i in range(seats)])
    
    def compute_zones(self, frame: np.ndarray) -> Dict[str, Any]:
        """Вычисляет все зоны для кадра"""
        h, w = frame.shape[:2]
        table_rect = Rect(0, 0, w, h)
        table_center = self.compute_table_center(frame.shape)

        player_zones = self.compute_player_zones(table_rect, frame)
        
        return {
            "table_center": table_center,
            "community_zone": self.compute_community_zone(table_center, table_rect),
            "player_zones": player_zones,
            "bet_zones": self.compute_bet_zones(
                player_zones,
                table_center, 
                frame
            )
        }
    
    @abstractmethod
    def compute_table_center(self, frame_shape) -> Point:
        pass
    
    @abstractmethod
    def compute_community_zone(self, table_center: Point, table_rect: Rect) -> Rect:
        pass
    
    @abstractmethod
    def compute_player_zones(self, table_rect: Rect, frame: np.ndarray = None) -> list[Rect]:
        pass
    
    @abstractmethod
    def compute_bet_zones(self, player_zones: list[Rect], table_center: Point, frame: np.ndarray = None) -> list[Rect]:
        pass
    
    # === ОБРАБОТКА ===
    
    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> None:
        """Полная обработка кадра: зоны + экстракция + обновление state"""
        pass
    
    @abstractmethod
    def get_table_info(self, hwnd: int) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def is_hero_turn(self, frame: np.ndarray) -> bool:
        pass
    
    @abstractmethod
    def should_parse_bets(self) -> bool:
        pass
    
    # === ХУКИ ===
    
    def on_hero_turn(self) -> None:
        pass
    
    def on_new_hand(self) -> None:
        self.table.preflop_action = None
        for player in self.table.players:
            player.last_bet = 0.0