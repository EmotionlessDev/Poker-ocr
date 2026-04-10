import time
from typing import Optional
import numpy as np
from domain.state import PokerTable, PreflopActionInfo
from app.pipeline import PokerVisionPipeline
from rooms.factory import get_room
from rooms.base_room import BaseRoom
from services.preflop_analyzer import analyze_preflop


class PokerStateManager:
    """
    Оркестратор: управляет потоком обработки, делегируя room-specific логику.
    """
    
    def __init__(self, room_name: str, seats: int, hero_nickname: str, hwnd: int):
        self.hwnd = hwnd
        self.last_blinds_check = 0.0
        
        # ✅ Room-specific логика вынесена в BaseRoom
        self.room: BaseRoom = get_room(room_name, seats, hero_nickname)
        
        # ✅ Pipeline пока оставляем для вычисления зон (можно перенести в room позже)
        self.pipeline = PokerVisionPipeline(room_name, seats)
        
        # ✅ Синхронизируем ссылку на table
        self.table: PokerTable = self.room.table
        
        # Получаем блайнды при инициализации
        self._update_blinds_from_hwnd()

    def update_from_frame(self, frame: np.ndarray) -> None:
        """Основной цикл обработки кадра"""
        current_time = time.time()
        
        # 1) Обновляем блайнды периодически
        if current_time - self.last_blinds_check > 5.0:
            self._update_blinds_from_hwnd()
            self.last_blinds_check = current_time
        
        # 2) Получаем зоны через pipeline (пока общий для всех румов)
        pipeline_result = self.pipeline.process(frame)
        if not pipeline_result:
            return
        
        # 3) Делегируем обработку руму
        self.room.process_frame(frame, pipeline_result)
        
        # 4) Проверяем очередь героя
        self.table.is_hero_turn = self.room.is_hero_turn(frame)
        
        # 5) Если очередь героя — анализ
        if self.table.is_hero_turn:
            self.room.on_hero_turn()
            
            # Префлоп-анализ (если нужно)
            if self.table.street == "preflop" and not self.table.community_cards:
                pass
                # analyze_preflop(self.table)
        else:
            # Сбрасываем устаревшие ставки
            self._clear_stale_bets(current_time)
        
        # 6) Синхронизируем table (на случай если room обновил свой)
        self.table = self.room.table

    def _update_blinds_from_hwnd(self) -> None:
        """Обновляет блайнды из заголовка окна"""
        info = self.room.get_table_info(self.hwnd)
        
        if info.get("valid"):
            sb, bb = info["small_blind"], info["big_blind"]
            
            if self.table.small_blind != sb or self.table.big_blind != bb:
                print(f"🪙 Blinds updated: {self.table.blinds_str} → {int(sb)}/{int(bb)}")
                self.table.set_blinds(sb, bb)
                # Сброс при смене блайндов (новая раздача)
                self.room.on_new_hand()
        else:
            if self.table.big_blind == 0:
                print("⚠️ Could not parse blinds, using default 100/200")
                self.table.set_blinds(100, 200)

    def _clear_stale_bets(self, current_time: float) -> None:
        """Сбрасывает устаревшие ставки"""
        BET_TIMEOUT = 3.0
        for p in self.table.players:
            if hasattr(p, 'last_bet_seen_time'):
                if current_time - p.last_bet_seen_time > BET_TIMEOUT:
                    if p.last_bet > 0:
                        p.last_bet = 0.0