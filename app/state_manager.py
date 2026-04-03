import time
from domain.state import Player, PokerTable, PreflopActionInfo
from app.pipeline import PokerVisionPipeline
from app.nn_client import NeuralNetClient
from detectors.button_detector import DealerButtonDetector
from extractors.player_extractor import PlayerExtractor
from extractors.card_extractor import CardExtractor
from services.position_assigner import PositionAssigner
from detectors.seat_state_detector import SeatStateDetector
from extractors.nickname_extractor import NicknameExtractor
from extractors.bet_extractor import BetExtractor
from services.preflop_analyzer import analyze_preflop

import numpy as np

class PokerStateManager:
    def __init__(self, room: str, seats: int, hero_nickname: str, hwnd: int, button_template="./assets/dealer_button.png"):
        self.pipeline = PokerVisionPipeline(room, seats)
        self.nn_client = NeuralNetClient()
        self.hwnd = hwnd

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
        self.last_blinds_check = 0.0
        
        # ➕ Сразу получаем блайнды при инициализации
        self._update_blinds_from_hwnd()

    def update_from_frame(self, frame: np.ndarray):
        result = self.pipeline.process(frame)
        if not result:
            return

        player_zones = result.get("player_zones", [])
        comm_zone = result.get("community_zone")
        bet_zones = result.get("bet_zones", [])

        # ➕ Проверяем блайнды (раз в 5 секунд)
        current_time = time.time()
        if current_time - self.last_blinds_check > 5.0:
            self._update_blinds_from_hwnd()
            self.last_blinds_check = current_time

        # 1) update players
        self.player_extractor.extract(frame, player_zones, self.table.players)

        # 2) detect dealer button
        center = self.button_detector.detect(frame)
        if center:
            self._assign_button_to_closest_player(center)

        # 3) assign positions
        self.position_assigner.assign(self.table.players)

        # 4) hero cards
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

        # 7) Анализируем префлоп-экшен (НЕТУ КАРТ НА СТОЛЕ)
        if self.table.street == "preflop" and self.table.community_cards == []:
            analyze_preflop(self.table)
            self._debug_preflop_action()

    def _update_blinds_from_hwnd(self):
        """Обновляет блайнды из заголовка окна через pipeline"""
        info = self.pipeline.get_table_info(self.hwnd)
        
        if info.get("valid"):
            sb = info["small_blind"]
            bb = info["big_blind"]
            
            # Проверяем, изменились ли блайнды
            if self.table.small_blind != sb or self.table.big_blind != bb:
                print(f"🪙 Blinds updated: {self.table.blinds_str} → {int(sb)}/{int(bb)}")
                self.table.set_blinds(sb, bb)
                # Сброс префлоп-инфо при смене блайндов (новая раздача)
                self.table.preflop_action = PreflopActionInfo()
        else:
            # Fallback: стандартные блайнды если не удалось спарсить
            if self.table.big_blind == 0:
                print("⚠️ Could not parse blinds from window title, using default 100/200")
                self.table.set_blinds(100, 200)

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
            for p in self.table.players:
                p.is_button = False
            best.is_button = True

    def _debug_preflop_action(self):
        """Вывод информации о префлопе (для отладки)"""
        info = self.table.preflop_action
        
        print(f"\n📊 Preflop Analysis (Blinds: {self.table.blinds_str})")
        
        if info.is_open_raise:
            print("   Status: Hero opens first")
        elif info.is_4bet_pot:
            print(f"   Status: 4-bet pot!")
            print(f"   Opener: seat {info.first_raiser_seat} ({info.first_raiser_position}) - {info.first_raiser_amount_bb:.1f}BB")
            print(f"   3-bet: seat {info.three_bettor_seat} ({info.three_bettor_position}) - {info.three_bet_amount_bb:.1f}BB")
            print(f"   4-bet: seat {info.four_bettor_seat} - {info.four_bet_amount_bb:.1f}BB")
        elif info.is_3bet_pot:
            print(f"   Status: 3-bet pot")
            print(f"   Opener: seat {info.first_raiser_seat} ({info.first_raiser_position}) - {info.first_raiser_amount_bb:.1f}BB")
            print(f"   3-bet: seat {info.three_bettor_seat} ({info.three_bettor_position}) - {info.three_bet_amount_bb:.1f}BB")
        else:
            print(f"   Status: Raised by seat {info.first_raiser_seat} ({info.first_raiser_position})")
            if info.callers:
                print(f"   Callers: {info.callers}")
        
        if info.hero_to_call_bb > 0:
            print(f"   Hero needs to call: {info.hero_to_call_bb:.1f}BB")
        
        print("-" * 50)