import time
from domain.state import Player, PokerTable
from app.pipeline import PokerVisionPipeline
from app.nn_client import NeuralNetClient
from detectors.button_detector import DealerButtonDetector

from extractors.player_extractor import PlayerExtractor
from extractors.card_extractor import CardExtractor
from services.position_assigner import PositionAssigner
from detectors.seat_state_detector import SeatStateDetector
from extractors.nickname_extractor import NicknameExtractor
from extractors.bet_extractor import BetExtractor

import numpy as np

class PokerStateManager:
    def __init__(self, room: str, seats: int, hero_nickname: str, button_template="./assets/dealer_button.png"):
        self.pipeline = PokerVisionPipeline(room, seats)
        self.nn_client = NeuralNetClient()

        # components
        self.seat_detector = SeatStateDetector()
        self.nickname_extractor = NicknameExtractor()
        self.player_extractor = PlayerExtractor(hero_nickname, self.seat_detector, self.nickname_extractor)
        self.card_extractor = CardExtractor(self.nn_client)
        self.position_assigner = PositionAssigner()
        self.button_detector = DealerButtonDetector(button_template)
        self.bet_extractor = BetExtractor()

        # state
        self.table = PokerTable(players=[Player(seat=i) for i in range(seats)])
        self.last_update = 0.0

    def update_from_frame(self, frame: np.ndarray):
        """
        Orchestration: minimal logic here — call vision -> extractors -> services -> update table
        """
        result = self.pipeline.process(frame)
        if not result:
            return

        player_zones = result.get("player_zones", [])
        comm_zone = result.get("community_zone")
        bet_zones = result.get("bet_zones", [])

        # 1) update players (OCR throttled inside extractor)
        self.player_extractor.extract(frame, player_zones, self.table.players)

        # 2) detect dealer button and assign to nearest player
        center = self.button_detector.detect(frame)
        if center:
            self._assign_button_to_closest_player(center)

        # 3) assign positions (depends on is_button flags)
        self.position_assigner.assign(self.table.players)

        # 4) hero cards (only when hero exists)
        hero = next((p for p in self.table.players if p.is_hero), None)
        if hero and hero.zone is not None:
            hero.cards = self.card_extractor.extract_hero(frame, hero.zone)

        # 5) community cards
        if comm_zone is not None:
            self.table.community_cards = self.card_extractor.extract_board(frame, comm_zone)
        # 6) bets
        for p, bet_zone in zip(self.table.players, bet_zones):
            if bet_zone is not None and p.is_active:
                p.last_bet = self.bet_extractor.extract(frame, bet_zone)



    def _assign_button_to_closest_player(self, center):
        bx, by = center
        best = None
        best_dist = float("inf")
        for p in self.table.players:
            if p.zone is None:
                continue
            px = (p.zone.x1 + p.zone.x2) // 2
            py = (p.zone.y1 + p.zone.y2) // 2
            dist = (px - bx) ** 2 + (py - by) ** 2
            if dist < best_dist:
                best_dist = dist
                best = p
        if best:
            # reset previous
            for p in self.table.players:
                p.is_button = False
            best.is_button = True