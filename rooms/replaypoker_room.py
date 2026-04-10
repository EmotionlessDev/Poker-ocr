from typing import Dict, Any
import numpy as np
from rooms.base_room import BaseRoom
from rooms.replaypoker_geometry import ReplayPokerGeometry
from detectors.hero_turn_detector import HeroTurnDetector
from extractors.player_extractor import PlayerExtractor
from extractors.card_extractor import CardExtractor
from extractors.bet_extractor import BetExtractor
from detectors.button_detector import DealerButtonDetector
from services.position_assigner import PositionAssigner
from detectors.seat_state_detector import SeatStateDetector
from extractors.nickname_extractor import NicknameExtractor
from app.nn_client import NeuralNetClient


class ReplayPokerRoom(BaseRoom):
    """ReplayPoker-specific реализация"""
    
    def __init__(self, seats: int, hero_nickname: str):
        super().__init__(seats, hero_nickname)
        
        # Room-specific компоненты
        self.geometry = ReplayPokerGeometry(seats)
        self.nn_client = NeuralNetClient()
        
        # Детекторы и экстракторы
        self.hero_turn_detector = HeroTurnDetector()
        self.seat_detector = SeatStateDetector()
        self.nickname_extractor = NicknameExtractor()
        self.player_extractor = PlayerExtractor(
            hero_nickname, 
            self.seat_detector, 
            self.nickname_extractor
        )
        self.card_extractor = CardExtractor(self.nn_client)
        self.bet_extractor = BetExtractor()
        self.button_detector = DealerButtonDetector("./assets/dealer_button.png")
        self.position_assigner = PositionAssigner()
        
        # Кэш
        self._is_hero_turn_cache = False
    
    def compute_zones(self, frame: np.ndarray) -> Dict[str, Any]:
        """Вычисляет зоны для ReplayPoker"""
        h, w = frame.shape[:2]
        table_rect = type('Rect', (), {'x1': 0, 'y1': 0, 'x2': w, 'y2': h, 'width': w, 'height': h})()
        table_center = self.geometry.compute_table_center(frame.shape)
        
        return {
            "table_center": table_center,
            "community_zone": self.geometry.compute_community_zone(table_center, table_rect),
            "player_zones": self.geometry.compute_player_zones(table_rect, frame),
            "bet_zones": self.geometry.compute_bet_zones(
                self.geometry.compute_player_zones(table_rect), 
                table_center, 
                frame
            )
        }
    
    def process_frame(self, frame: np.ndarray, pipeline_result: Dict[str, Any]) -> None:
        """Обрабатывает кадр"""
        player_zones = pipeline_result.get("player_zones", [])
        comm_zone = pipeline_result.get("community_zone")
        bet_zones = pipeline_result.get("bet_zones", [])
        
        # Обновляем игроков
        self.player_extractor.extract(frame, player_zones, self.table.players)
        
        # Детектим баттон
        center = self.button_detector.detect(frame)
        if center:
            self._assign_button(center)
        
        # Назначаем позиции
        self.position_assigner.assign(self.table.players)
        
        # Карты героя
        hero = next((p for p in self.table.players if p.is_hero), None)
        if hero and hero.zone:
            hero.cards = self.card_extractor.extract_hero(frame, hero.zone)
        
        # Community cards
        if comm_zone:
            self.table.community_cards = self.card_extractor.extract_board(frame, comm_zone)
        
        # Ставки (если нужно)
        if self.should_parse_bets():
            self._parse_bets(frame, bet_zones)
    
    def _assign_button(self, center):
        """Назначает баттон ближайшему игроку"""
        bx, by = center
        best, best_dist = None, float("inf")
        
        for p in self.table.players:
            if p.zone is None:
                continue
            px = (p.zone.x1 + p.zone.x2) // 2
            py = (p.zone.y1 + p.zone.y2) // 2
            dist = (px - bx) ** 2 + (py - by) ** 2
            if dist < best_dist:
                best_dist, best = dist, p
        
        if best:
            for p in self.table.players:
                p.is_button = False
            best.is_button = True
    
    def _parse_bets(self, frame, bet_zones):
        """Парсит ставки"""
        import time
        current_time = time.time()
        
        for p, bet_zone in zip(self.table.players, bet_zones):
            if not p.is_active or bet_zone is None:
                continue
            bet = self.bet_extractor.extract(frame, bet_zone)
            if bet is not None and bet > 0:
                p.last_bet = bet
                p.last_bet_seen_time = current_time
            else:
                p.last_bet = 0.0
    
    def get_table_info(self, hwnd: int) -> Dict[str, Any]:
        return self.geometry.get_table_info_from_hwnd(hwnd)
    
    def is_hero_turn(self, frame: np.ndarray) -> bool:
        self._is_hero_turn_cache = self.hero_turn_detector.detect(frame)
        return self._is_hero_turn_cache
    
    def should_parse_bets(self) -> bool:
        return self._is_hero_turn_cache
    
    def on_hero_turn(self) -> None:
        """Хук для анализа префлопа"""
        # Можно вызвать analyze_preflop здесь или в state_manager
        pass