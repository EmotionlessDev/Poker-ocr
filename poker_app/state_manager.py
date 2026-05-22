import sys
import time
import numpy as np
import logging
from rooms.factory import get_room
from rooms.base_room import BaseRoom
from services.preflop_analyzer import analyze_preflop
from services.analyzer.preflop_advisor import PreflopAdvisor
from ui.overlay_controller import OverlayController, OverlayData


logger = logging.getLogger(__name__)

class PokerStateManager:
    """
    Чистый оркестратор: делегирует ВСЮ логику в Room.
    """
    
    def __init__(self, room_name: str, seats: int, hero_nickname: str, hwnd: int, enable_overlay: bool = True):
        self.hwnd = hwnd
        self.last_blinds_check = 0.0
        
        # ✅ Room владеет всем: table, geometry, extractors
        self._room: BaseRoom = get_room(room_name, seats, hero_nickname)
        self.preflop_advisor = PreflopAdvisor()

        self.enable_overlay = enable_overlay
        self.overlay_controller = OverlayController() if enable_overlay else None

        if enable_overlay:
            self._init_overlay()
    
    @property
    def table(self):
        """Прокси к table внутри room"""
        return self._room.table
    
    def update_from_frame(self, frame: np.ndarray) -> None:
        current_time = time.time()
        
        # 1) Обновляем блайнды
        if current_time - self.last_blinds_check > 5.0:
            self._update_blinds()
            self.last_blinds_check = current_time
        
        # 2) Делегируем обработку в Room
        self._room.process_frame(frame)
        
        # 3) Проверяем очередь героя
        is_hero_turn = self._room.is_hero_turn(frame)
        self.table.is_hero_turn = is_hero_turn
        
        # 4) Проверяем стадию игры (префлоп или постфлоп)
        has_community_cards = len(self.table.community_cards) > 0
        is_preflop = not has_community_cards
        
        # Обновляем street на основе карт стола
        if is_preflop:
            self.table.street = "preflop"
        elif len(self.table.community_cards) == 3:
            self.table.street = "flop"
        elif len(self.table.community_cards) == 4:
            self.table.street = "turn"
        elif len(self.table.community_cards) >= 5:
            self.table.street = "river"
        
        if is_hero_turn and is_preflop:
            self._room.on_hero_turn()
            self._log_hero_turn_state()
            
            # Анализируем префлоп ситуацию
            advice = self.preflop_advisor.get_advice(self.table)
            if advice:
                logger.info(f"💡 Advice: {advice}")
        else:
            self._clear_stale_bets(current_time)

        # 5) Обновляем оверлей
        if self.enable_overlay and self.overlay_controller:
            overlay_data = self.overlay_controller.create_overlay_data(self)
            
            # Показываем советы ТОЛЬКО на префлопе
            if is_hero_turn and is_preflop:
                advice = self.preflop_advisor.get_advice(self.table)
                if advice:
                    overlay_data.advice_action = advice.action.name
                    overlay_data.advice_confidence = advice.confidence.value
                    overlay_data.advice_reason = advice.reason
                    logger.debug(f"  [Overlay] Setting advice: {advice.action.name}")
            else:
                # На постфлопе скрываем советы
                overlay_data.advice_action = None
                overlay_data.advice_confidence = None
                overlay_data.advice_reason = None
            
            self.overlay_controller.update(overlay_data)

        # 6) Process Qt events + репаинт
        if self.enable_overlay and hasattr(self, 'qt_app') and self.qt_app:
            self.qt_app.processEvents()
            
            if hasattr(self, 'overlay_window'):
                self.overlay_window.update()

    def _init_overlay(self):
        """Инициализирует PyQt6 оверлей"""
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.overlay_window import OverlayWindow
            
            # Создаём QApplication (если ещё нет)
            self.qt_app = QApplication.instance()
            if not self.qt_app:
                self.qt_app = QApplication(sys.argv)
            
            # Создаём окно оверлея
            self.overlay_window = OverlayWindow()
            
            # Регистрируем callback
            self.overlay_controller.set_update_callback(self.overlay_window.update_data)
            
            # Показываем
            self.overlay_window.show_overlay()
            
            logger.info("✅ Overlay initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to init overlay: {e}")
            self.enable_overlay = False
    
    def _update_blinds(self) -> None:
        info = self._room.get_table_info(self.hwnd)
        if info.get("valid"):
            sb, bb = info["small_blind"], info["big_blind"]
            if self.table.small_blind != sb or self.table.big_blind != bb:
                print(f"🪙 Blinds updated: {self.table.blinds_str} → {int(sb)}/{int(bb)}")
                self.table.set_blinds(sb, bb)
                self._room.on_new_hand()
        elif self.table.big_blind == 0:
            print("⚠️ Could not parse blinds, using default 100/200")
            self.table.set_blinds(100, 200)
    
    def _clear_stale_bets(self, current_time: float) -> None:
        BET_TIMEOUT = 3.0
        for p in self.table.players:
            if hasattr(p, 'last_bet_seen_time'):
                if current_time - p.last_bet_seen_time > BET_TIMEOUT:
                    if p.last_bet > 0:
                        p.last_bet = 0.0

    def _log_hero_turn_state(self) -> None:
            """Вывод отладочной информации когда очередь героя"""
            logger.info("🟢 HERO TURN")
            
            # Игроки
            for p in self.table.players:
                if p.is_active:
                    mark = "🦸" if p.is_hero else ""
                    logger.info(f"  {mark} Seat {p.seat}: {p.nickname} "
                            f"(Pos: {p.position}, Bet: {p.last_bet})")
            
            # Карты
            logger.info(f"  Community: {[c.rank+c.suit for c in self.table.community_cards]}")
            hero = next((p for p in self.table.players if p.is_hero), None)
            if hero and hero.cards:
                logger.info(f"  Hero cards: {[c.rank+c.suit for c in hero.cards]}")
            
            logger.info("=" * 50)