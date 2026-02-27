from domain.state import PokerTable, Card
from app.pipeline import PokerVisionPipeline
from app.nn_client import NeuralNetClient

import numpy as np
import pytesseract
import re
import cv2

class PokerStateManager:
    def __init__(self, room: str, seats: int, hero_nickname: str):
        self.pipeline = PokerVisionPipeline(room, seats)
        self.nn_client = NeuralNetClient()
        self.table: PokerTable = PokerTable()
        self.hero_nickname = hero_nickname.lower()
        self.hero_zone = None  # пока не определяем

    def update_from_frame(self, frame: np.ndarray):
        """
        Обновляет состояние стола.
        Пока:
          - community_cards заполняются нейронкой
          - hero_cards и hero_position остаются пустыми
        """
        result = self.pipeline.process(frame)
        if not result:
            return
        
        # Получаем зоны игроков и пытаемся найти hero
        player_zones = result.get("player_zones", [])
        for zone in player_zones:
            # crop чуть выше для текста
            crop = frame[max(0, zone.y1-20):zone.y2, zone.x1:zone.x2]
            text = pytesseract.image_to_string(crop)
            text_clean = re.sub(r'\W+', '', text).lower()
            hero_nick_clean = re.sub(r'\W+', '', self.hero_nickname).lower()
            if hero_nick_clean in text_clean:
                self.hero_zone = zone
                print("Hero zone найден")

        if self.hero_zone:
            # crop для карт — нижняя часть зоны
            # берем зону целиком
            target_w, target_h = 1280, 800
            crop_cards = frame[self.hero_zone.y1:self.hero_zone.y2, self.hero_zone.x1:self.hero_zone.x2]
            crop_cards = cv2.resize(crop_cards, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
            cv2.imshow("Hero Crop", crop_cards)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            nn_result = self.nn_client.predict(crop_cards)
            self.table.hero_cards = [Card(rank=c["rank"], suit=c["suit"]) for c in nn_result.get("cards", [])]     
       

        comm_zone = result["community_zone"]
        crop = frame[comm_zone.y1:comm_zone.y1 + comm_zone.height,
                     comm_zone.x1:comm_zone.x1 + comm_zone.width]

        nn_result = self.nn_client.predict(crop)
        self.table.community_cards = [
            Card(rank=c["rank"], suit=c["suit"]) for c in nn_result.get("cards", [])
        ]