from domain.state import Player, PokerTable, Card
from app.pipeline import PokerVisionPipeline
from app.nn_client import NeuralNetClient
from detectors.button_detector import DealerButtonDetector

import numpy as np
import pytesseract
import re
import cv2

# TODO: Вынести это в конфиг
POSITIONS_6MAX = [
    "BTN",
    "SB",
    "BB",
    "UTG",
    "MP",
    "CO"
]

# TODO: Обновлять раз в секунду, а не каждый кадр 
class PokerStateManager:
    def __init__(self, room: str, seats: int, hero_nickname: str):
        self.pipeline = PokerVisionPipeline(room, seats)
        self.nn_client = NeuralNetClient()

        self.hero_nickname = hero_nickname.lower()

        self.table = PokerTable(
            players=[Player(seat=i) for i in range(seats)]
        )

        self.hero_zone = None

        self.button_detector = DealerButtonDetector("../assets/dealer_button.png")

    def update_from_frame(self, frame: np.ndarray):
        result = self.pipeline.process(frame)
        if not result:
            return

        player_zones = result.get("player_zones", [])
        comm_zone = result["community_zone"]

        # TODO: В иделае эти методы тут быть не должны
        self._update_players(frame, player_zones)
        self._detect_dealer_button(frame)
        self._assign_positions()
        self._update_hero_cards(frame)
        self._update_community_cards(frame, comm_zone)

    def _update_players(self, frame, player_zones):
        for i, zone in enumerate(player_zones):

            if i >= len(self.table.players):
                continue

            player = self.table.players[i]

            crop = frame[max(0, zone.y1-20):zone.y2, zone.x1:zone.x2]

            text = pytesseract.image_to_string(crop)
            nickname = text.strip()

            if nickname:
                player.nickname = nickname

            if self._is_hero(nickname):
                player.is_hero = True
                self.hero_zone = zone

    def _is_hero(self, nickname: str):
        text_clean = re.sub(r'\W+', '', nickname).lower()
        hero_clean = re.sub(r'\W+', '', self.hero_nickname)

        return hero_clean in text_clean
    
    def _update_hero_cards(self, frame):
        if not self.hero_zone:
            return

        zone = self.hero_zone

        crop = frame[zone.y1:zone.y2, zone.x1:zone.x2]

        canvas = self._prepare_nn_canvas(crop)

        nn_result = self.nn_client.predict(canvas)

        cards = [
            Card(rank=c["rank"], suit=c["suit"])
            for c in nn_result.get("cards", [])
        ]

        hero = self._get_hero()

        if hero:
            hero.cards = cards

    def _prepare_nn_canvas(self, crop):

        target_w, target_h = 1280, 800
        canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)

        crop_h, crop_w = crop.shape[:2]

        x_offset = (target_w - crop_w) // 2
        y_offset = (target_h - crop_h) // 2

        canvas[y_offset:y_offset+crop_h, x_offset:x_offset+crop_w] = crop

        return canvas
    
    def _get_hero(self):

        for p in self.table.players:
            if p.is_hero:
                return p

        return None
        
    def _update_community_cards(self, frame, comm_zone):

        crop = frame[
            comm_zone.y1:comm_zone.y1 + comm_zone.height,
            comm_zone.x1:comm_zone.x1 + comm_zone.width
        ]

        nn_result = self.nn_client.predict(crop)

        self.table.community_cards = [
            Card(rank=c["rank"], suit=c["suit"])
            for c in nn_result.get("cards", [])
        ]

    def _detect_dealer_button(self, frame):

        center = self.button_detector.detect(frame)

        if center is None:
            return

        bx, by = center

        closest_player = None
        best_dist = 999999

        for player in self.table.players:

            if player.zone is None:
                continue

            px = (player.zone.x1 + player.zone.x2) // 2
            py = (player.zone.y1 + player.zone.y2) // 2

            dist = (px - bx) ** 2 + (py - by) ** 2

            if dist < best_dist:
                best_dist = dist
                closest_player = player

        if closest_player:
            closest_player.is_button = True

    def _assign_positions(self):
        btn_index = None

        for i, p in enumerate(self.table.players):
            if p.is_button:
                btn_index = i
                break

        if btn_index is None:
            return

        for i, p in enumerate(self.table.players):

            pos_index = (i - btn_index) % len(self.table.players)

            p.position = POSITIONS_6MAX[pos_index]