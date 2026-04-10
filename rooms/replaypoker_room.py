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
from domain.geometry import Rect, Point


class ReplayPokerRoom(BaseRoom):
    
    def __init__(self, seats: int, hero_nickname: str):
        super().__init__(seats, hero_nickname)
        
        # Геометрия
        self.geometry = ReplayPokerGeometry(seats)
        
        # Компоненты
        self.nn_client = NeuralNetClient()
        self.hero_turn_detector = HeroTurnDetector()
        self.seat_detector = SeatStateDetector()
        self.nickname_extractor = NicknameExtractor()
        self.player_extractor = PlayerExtractor(
            hero_nickname, self.seat_detector, self.nickname_extractor
        )
        self.card_extractor = CardExtractor(self.nn_client)
        self.bet_extractor = BetExtractor()
        self.button_detector = DealerButtonDetector("./assets/dealer_button.png")
        self.position_assigner = PositionAssigner()
        
        # Кэш
        self._is_hero_turn_cache = False
        self._last_zones: Dict[str, Any] = {}
    
    # === Геометрия (делегирование) ===
    
    def compute_table_center(self, frame_shape) -> Point:
        return self.geometry.compute_table_center(frame_shape)
    
    def compute_community_zone(self, table_center: Point, table_rect: Rect) -> Rect:
        return self.geometry.compute_community_zone(table_center, table_rect)
    
    def compute_player_zones(self, table_rect: Rect, frame: np.ndarray = None) -> list[Rect]:
        return self.geometry.compute_player_zones(table_rect, frame)
    
    def compute_bet_zones(self, player_zones: list[Rect], table_center: Point, frame: np.ndarray = None) -> list[Rect]:
        return self.geometry.compute_bet_zones(player_zones, table_center, frame)
    
    def get_table_info(self, hwnd: int) -> Dict[str, Any]:
        return self.geometry.get_table_info_from_hwnd(hwnd)
    
    # === Обработка кадра ===
    
    def process_frame(self, frame: np.ndarray) -> None:
        """Полная обработка: зоны + экстракция + state"""
        
        # 1. Вычисляем зоны
        zones = self.compute_zones(frame)
        self._last_zones = zones
        
        # 2. Обновляем игроков
        self.player_extractor.extract(frame, zones["player_zones"], self.table.players)
        
        # 3. Детектим баттон
        center = self.button_detector.detect(frame)
        if center:
            self._assign_button(center)
        
        # 4. Позиции
        self.position_assigner.assign(self.table.players)
        
        # 5. Карты героя
        hero = next((p for p in self.table.players if p.is_hero), None)
        if hero and hero.zone:
            hero.cards = self.card_extractor.extract_hero(frame, hero.zone)
        
        # 6. Community cards
        if zones["community_zone"]:
            self.table.community_cards = self.card_extractor.extract_board(
                frame, zones["community_zone"]
            )
        
        # 7. Ставки (если нужно)
        if self.should_parse_bets():
            self._parse_bets(frame, zones["bet_zones"])
    
    def _assign_button(self, center):
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
    
    # === Hero turn ===
    
    def is_hero_turn(self, frame: np.ndarray) -> bool:
        self._is_hero_turn_cache = self.hero_turn_detector.detect(frame)
        return self._is_hero_turn_cache
    
    def should_parse_bets(self) -> bool:
        return self._is_hero_turn_cache