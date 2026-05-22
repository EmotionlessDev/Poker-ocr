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
        # Рейз = ставка >= 2.0 BB (исключаем блайнды и коллы)
        raise_threshold = bb * 2.0
        
        raises_count = 0
        for p in table.players:
            if not p.is_active or p.last_bet <= 0:
                continue
            bet_bb = p.last_bet / bb
            # Исключаем блайнды если они просто доложили (SB < 1.5BB, BB = 1.0BB)
            if p.position in ["SB", "BB"] and bet_bb < 1.5:
                continue
            if bet_bb >= raise_threshold:
                raises_count += 1
        
        # === 2. Классифицируем ===
        if raises_count == 0:
            # Никто не рейзил → RFI
            return "RFI"
        
        elif raises_count == 1:
            # Один рейзер → VS_OPEN
            return "VS_OPEN"
        
        else:
            # Два и более рейза → 3BET_POT
            return "3BET_POT"
    
    def _advise_rfi(self, table: PokerTable, hero: Player) -> Advice:
        """Рекомендация для RFI спота"""
        hand_str = cards_to_sorted_string(hero.cards)
        position = self._normalize_position(hero.position)
        
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
        """
        Рекомендация против открывашки (VS_OPEN).
        Стратегия: 3-бет или фолд, колл почти не используем.
        """
        hand_str = cards_to_sorted_string(hero.cards)
        hero_position = self._normalize_position(hero.position)
        
        # === 1. Определяем кто открылся ===
        opener = self._find_opener(table)
        if not opener or not opener.position:
            # Не смогли определить опенера — фолд по умолчанию
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.LOW,
                reason="Could not identify opener"
            )
        
        opener_position = self._normalize_position(opener.position)
        
        # === 2. Находим ключ ренджа ===
        range_key = self._get_3bet_range_key(hero_position, opener_position)
        if not range_key:
            # Нет ренджа для этой комбинации позиций — фолд
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.MEDIUM,
                reason=f"No 3-bet range for {hero_position} vs {opener_position}"
            )
        
        # === 3. Получаем и парсим рендж ===
        range_str = ranges.RANGES_3BET.get(range_key, "")
        if not range_str:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.LOW,
                reason=f"Empty range for key {range_key}"
            )
        
        # Парсим с кэшированием
        if range_key not in self._parsed_ranges:
            self._parsed_ranges[range_key] = self.range_parser.parse(range_str)
        
        # === 4. Проверяем руку ===
        in_range = hand_matches_range(hand_str, self._parsed_ranges[range_key])
        
        if in_range:
            # Учитываем размер рейза опенера для размера 3-бета
            opener_bet_bb = opener.last_bet / (table.big_blind or 200)
            sizing = "3x" if opener_bet_bb <= 2.5 else "4x"
            
            return Advice(
                action=ActionRecommendation.RAISE,
                confidence=Confidence.HIGH,
                reason=f"{hand_str} is in 3-bet range vs {opener_position} ({sizing})",
                hand_strength=0.85,
                range_coverage=1.0
            )
        else:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.MEDIUM,
                reason=f"{hand_str} not in 3-bet range vs {opener_position}",
                hand_strength=0.35,
                range_coverage=0.0
            )
    
    def _advise_vs_3bet(self, table: PokerTable, hero: Player) -> Advice:
        """
        Рекомендация для 3-бет спотов (4-бет или фолд).
        Стратегия: 4-бет с сильными руками, фолд со слабыми.
        """
        hand_str = cards_to_sorted_string(hero.cards)
        hero_position = self._normalize_position(hero.position)
        
        # === 1. Определяем кто сделал 3-бет ===
        threebettor = self._find_threebettor(table)
        if not threebettor or not threebettor.position:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.LOW,
                reason="Could not identify 3-bettor"
            )
        
        threebettor_position = self._normalize_position(threebettor.position)
        
        # === 2. Находим ключ ренджа для 4-бета ===
        range_key = self._get_4bet_range_key(hero_position, threebettor_position)
        if not range_key:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.MEDIUM,
                reason=f"No 4-bet range for {hero_position} vs 3bet from {threebettor_position}"
            )
        
        # === 3. Получаем и парсим рендж ===
        range_str = ranges.RANGES_4BET.get(range_key, "")
        if not range_str:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.LOW,
                reason=f"Empty 4-bet range for key {range_key}"
            )
        
        # Парсим с кэшированием
        if range_key not in self._parsed_ranges:
            self._parsed_ranges[range_key] = self.range_parser.parse(range_str)
        
        # === 4. Проверяем руку ===
        in_range = hand_matches_range(hand_str, self._parsed_ranges[range_key])
        
        if in_range:
            threebet_bet_bb = threebettor.last_bet / (table.big_blind or 200)
            sizing = "2.5x" if threebet_bet_bb <= 6 else "3x"
            
            return Advice(
                action=ActionRecommendation.RAISE,
                confidence=Confidence.HIGH,
                reason=f"{hand_str} is in 4-bet range vs {threebettor_position} ({sizing})",
                hand_strength=0.9,
                range_coverage=1.0
            )
        else:
            return Advice(
                action=ActionRecommendation.FOLD,
                confidence=Confidence.MEDIUM,
                reason=f"{hand_str} not in 4-bet range vs {threebettor_position}",
                hand_strength=0.3,
                range_coverage=0.0
            )
    
    def _find_threebettor(self, table: PokerTable) -> Optional[Player]:
        """Находит игрока сделавшего 3-бет (второй рейз)"""
        bb = table.big_blind if table.big_blind > 0 else 200.0
        raise_threshold = bb * 3.5  # 3-бет обычно >= 3.5BB
        
        for p in table.players:
            if p.is_active and p.last_bet >= raise_threshold:
                if p.position not in ["SB", "BB"] or p.last_bet > bb * 2.5:
                    return p
        return None
    
    def _get_4bet_range_key(self, hero_pos: str, threebettor_pos: str) -> Optional[str]:
        """Возвращает ключ ренджа для 4-бета"""
        # Упрощённая логика
        if hero_pos in ["SB", "BB"]:
            if threebettor_pos in ["UTG", "UTG+1", "MP"]:
                return "4BET_BB_VS_EP"
            elif threebettor_pos == "CO":
                return "4BET_BB_VS_CO"
            elif threebettor_pos == "BTN":
                return "4BET_BB_VS_BTN"
        elif hero_pos == "BTN":
            if threebettor_pos == "CO":
                return "4BET_BTN_VS_CO"
            elif threebettor_pos in ["MP", "UTG"]:
                return "4BET_VS_EP"
        elif hero_pos == "CO":
            if threebettor_pos in ["MP", "UTG"]:
                return "4BET_VS_EP"
        
        # Fallback
        if threebettor_pos in ["UTG", "UTG+1", "MP"]:
            return "4BET_VS_EP"
        elif threebettor_pos == "CO":
            return "4BET_VS_CO"
        elif threebettor_pos == "BTN":
            return "4BET_VS_BTN"
        
        return None
    
    def _normalize_position(self, pos: str) -> str:
        """Нормализует название позиции к стандартному виду"""
        if not pos:
            return ""
        # Маппинг возможных вариаций
        pos_map = {
            "UTG": "UTG",
            "UTG+1": "UTG+1",
            "UTG+2": "UTG+1",
            "MP": "MP",
            "MP+1": "MP",
            "CO": "CO",
            "HJ": "CO",
            "LJ": "MP",
            "BTN": "BU",
            "BU": "BU",
            "DEALER": "BU",
            "SB": "SB",
            "BB": "BB",
        }
        return pos_map.get(pos.upper(), pos)
    
    def _find_opener(self, table: PokerTable) -> Optional[Player]:
        """
        Находит игрока, который открылся первым (сделал рейз > 2.0 BB).
        """
        bb = table.big_blind if table.big_blind > 0 else 200.0
        raise_threshold = bb * 2.0
        
        # Ищем первого игрока с рейзом (не блайнды)
        for p in table.players:
            if p.is_active and p.last_bet >= raise_threshold:
                # Исключаем блайнды если они просто доложили
                if p.position not in ["SB", "BB"] or p.last_bet > bb * 1.5:
                    return p
        return None

    def _get_3bet_range_key(self, hero_pos: str, opener_pos: str) -> Optional[str]:
        """
        Возвращает ключ ренджа для комбинации позиций.
        """
        # Прямой маппинг
        key = ranges.RANGES_3BET_KEYS.get((hero_pos, opener_pos))
        if key:
            return key
        
        # Fallback: группируем позиции опенера в категории
        opener_category = self._categorize_position(opener_pos)
        
        # Герой в блайндах — используем общие ренджи
        if hero_pos == "BB":
            if opener_category == "EP":
                return "3BET_BB_VS_EP"
            elif opener_category == "MP":
                return "3BET_BB_VS_MP"
            elif opener_category == "CO":
                return "3BET_BB_VS_CO"
            elif opener_category == "BTN":
                return "3BET_BB_VS_BU"
        elif hero_pos == "SB":
            if opener_category in ["EP", "MP"]:
                return "3BET_SB_VS_MP"  # используем общий
            elif opener_category == "CO":
                return "3BET_SB_VS_CO"
            elif opener_category == "BTN":
                return "3BET_SB_VS_BTN"
        
        # Герой не в блайндах — упрощённая логика
        if hero_pos in ["UTG", "MP", "CO", "BTN"]:
            if opener_category in ["EP", "MP"]:
                return "3BET_VS_MP"
            elif opener_category == "CO" and hero_pos == "BTN":
                return "3BET_BTN_VS_CO"
        
        return None

    def _categorize_position(self, pos: str) -> str:
        """
        Группирует позицию в категорию: EP, MP, CO, BTN, SB, BB.
        """
        if pos in ["UTG", "UTG+1"]:
            return "EP"
        elif pos == "MP":
            return "MP"
        elif pos == "CO":
            return "CO"
        elif pos == "BTN":
            return "BTN"
        elif pos == "SB":
            return "SB"
        elif pos == "BB":
            return "BB"
        return "UNKNOWN"