# app/state_manager.py
import time
import numpy as np
import logging
from rooms.factory import get_room
from rooms.base_room import BaseRoom
from services.preflop_analyzer import analyze_preflop

logger = logging.getLogger(__name__)

class PokerStateManager:
    """
    Чистый оркестратор: делегирует ВСЮ логику в Room.
    """
    
    def __init__(self, room_name: str, seats: int, hero_nickname: str, hwnd: int):
        self.hwnd = hwnd
        self.last_blinds_check = 0.0
        
        # ✅ Room владеет всем: table, geometry, extractors
        self._room: BaseRoom = get_room(room_name, seats, hero_nickname)
    
    @property
    def table(self):
        """Прокси к table внутри room"""
        return self._room.table
    
    def update_from_frame(self, frame: np.ndarray) -> None:
        """Оркестрация: только координация, без бизнес-логики"""
        current_time = time.time()
        
        # 1) Обновляем блайнды
        if current_time - self.last_blinds_check > 5.0:
            self._update_blinds()
            self.last_blinds_check = current_time
        
        # 2) Делегируем обработку в Room
        self._room.process_frame(frame)
        
        # 3) Проверяем очередь героя
        if self._room.is_hero_turn(frame):
            self._room.on_hero_turn()
            self._log_hero_turn_state()
            
            # Префлоп-анализ
            if self.table.street == "preflop" and not self.table.community_cards:
                analyze_preflop(self.table)
        else:
            self._clear_stale_bets(current_time)
    
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