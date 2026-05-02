import logging
from typing import Optional
from domain.state import PokerTable, Player
from domain.advice import Advice, ActionRecommendation, Confidence
from utils.range_parser import RangeParser
from utils.hand_utils import cards_to_sorted_string, hand_matches_range
from .config import ranges

logger = logging.getLogger(__name__)


class PreflopAdvisor:
    """
    Советник для префлоп-решений.
    Пока поддерживает только RFI (Raise First In) споты.
    """
    
    def __init__(self):
        self.range_parser = RangeParser()
        # Кэшируем распарсенные ренджи
        self._parsed_ranges = {}
    
    def get_advice(self, table: PokerTable) -> Optional[Advice]:
        """
        Главная точка входа: анализирует состояние стола и возвращает рекомендацию.
        """
        hero = next((p for p in table.players if p.is_hero), None)
        if not hero or not hero.cards or not hero.position:
            return None
        
        # Определяем тип ситуации
        situation = self._classify_situation(table, hero)
        
        if situation == "RFI":
            return self._advise_rfi(table, hero)
        elif situation == "VS_OPEN":
            return self._advise_vs_open(table, hero)
        elif situation == "3BET_POT":
            return self._advise_vs_3bet(table, hero)
        else:
            # Пока не поддерживаем
            return None
    
    def _classify_situation(self, table: PokerTable, hero: Player) -> str:
        """
        Определяет тип префлоп-ситуации на основе количества рейзов.
        
        RFI: 0 рейзов (никто не повышал, только блайнды или коллы)
        VS_OPEN: 1 рейз (кто-то открылся, другие фолд/колл)
        3BET_POT: 2+ рейза (рейз + рейз рейза)
        """
        
        # Fallback если блайнды ещё не спаршены
        bb = table.big_blind if table.big_blind > 0 else 200.0
        
        # === 1. Считаем количество рейзов ===
        # Рейз = ставка > 2.0 BB
        raise_threshold = bb * 2.0
        
        raises_count = 0
        for p in table.players:
            if p.is_active and p.last_bet >= raise_threshold:
                raises_count += 1
        
        # === 2. Классифицируем ===
        if raises_count == 0:
            # Никто не рейзил → RFI
            # (в блайндах можно открыть/комплитить, в других позициях — рейз/фолд)
            return "RFI"
        
        elif raises_count == 1:
            # Один рейзер → VS_OPEN
            return "VS_OPEN"
        
        else:
            # Два и более рейза → 3BET_POT требует доработки
            return "3BET_POT"
    
    def _advise_rfi(self, table: PokerTable, hero: Player) -> Advice:
        """Рекомендация для RFI спота"""
        hand_str = cards_to_sorted_string(hero.cards)
        position = hero.position
        
        # Получаем рендж для позиции
        range_str = ranges.RFI_RANGES.get(position, "")
        if not range_str:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.LOW,
                reason=f"No range defined for position {position}"
            )
        
        # Парсим рендж (с кэшированием)
        if position not in self._parsed_ranges:
            self._parsed_ranges[position] = self.range_parser.parse(range_str)
        
        in_range = hand_matches_range(hand_str, self._parsed_ranges[position])
        
        if in_range:
            return Advice(
                action=ActionRecommendation.RAISE,
                confidence=Confidence.HIGH,
                reason=f"{hand_str} is in RFI range for {position}",
                hand_strength=0.8,  # заглушка
                range_coverage=1.0
            )
        else:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.MEDIUM,
                reason=f"{hand_str} is not in RFI range for {position}",
                hand_strength=0.3,
                range_coverage=0.0
            )
    
    def _advise_vs_open(self, table: PokerTable, hero: Player) -> Advice:
        """Заглушка для ответа на открывашку"""
        return Advice(
            action=ActionRecommendation.FOLD,
            confidence=Confidence.LOW,
            reason="VS_OPEN logic not implemented yet"
        )
    
    def _advise_vs_3bet(self, table: PokerTable, hero: Player) -> Advice:
        """Заглушка для 3-бет спотов"""
        return Advice(
            action=ActionRecommendation.FOLD,
            confidence=Confidence.LOW,
            reason="3BET_POT logic not implemented yet"
        )