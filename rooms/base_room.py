from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import numpy as np
from domain.state import PokerTable, Player
from domain.geometry import Rect, Point


class BaseRoom(ABC):
    """
    Абстракция покер-рума.
    Инкапсулирует всю room-specific логику.
    """
    
    def __init__(self, seats: int, hero_nickname: str):
        self.seats = seats
        self.hero_nickname = hero_nickname
        self.table = PokerTable(players=[Player(seat=i) for i in range(seats)])
    
    @abstractmethod
    def process_frame(self, frame: np.ndarray, pipeline_result: Dict[str, Any]) -> None:
        """
        Обрабатывает кадр: обновляет игроков, карты, ставки.
        Вызывается из PokerStateManager.
        """
        pass
    
    @abstractmethod
    def get_table_info(self, hwnd: int) -> Dict[str, Any]:
        """Получает информацию о столе (блайнды, название)"""
        pass
    
    @abstractmethod
    def is_hero_turn(self, frame: np.ndarray) -> bool:
        """Проверяет, дошла ли очередь до героя"""
        pass
    
    @abstractmethod
    def should_parse_bets(self) -> bool:
        """Определяет, нужно ли парсить ставки в текущий момент"""
        pass
    
    @abstractmethod
    def compute_zones(self, frame: np.ndarray) -> Dict[str, Any]:
        """Вычисляет зоны (игроки, ставки, комьюнити)"""
        pass
    
    def on_hero_turn(self) -> None:
        """Хук: вызывается когда очередь героя (для анализа)"""
        pass
    
    def on_new_hand(self) -> None:
        """Хук: вызывается при начале новой раздачи"""
        self.table.preflop_action = None
        for player in self.table.players:
            player.last_bet = 0.0