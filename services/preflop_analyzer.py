from typing import Optional, List
from domain.state import PokerTable, Player, PreflopActionInfo


class PreflopAnalyzer:
    """Анализирует last_bet для определения префлоп-экшена"""
    
    def __init__(self, table: PokerTable):
        self.table = table
        # Fallback если блайнды ещё не спаршены
        self.bb = table.big_blind if table.big_blind > 0 else 200.0
        self.sb = table.small_blind if table.small_blind > 0 else 100.0
    
    def _safe_bet(self, bet: Optional[float]) -> float:
        """Возвращает 0.0 если bet is None"""
        return bet if bet is not None else 0.0
    
    def analyze(self) -> PreflopActionInfo:
        """Основной метод анализа"""
        info = PreflopActionInfo()
        
        # Получаем активных игроков
        active_players = [p for p in self.table.players if p.is_active]

        # Проверяем, есть ли герой
        hero = next((p for p in active_players if p.is_hero), None)
        if hero is None:
            return info
        
        # Игнорируем блайнды для определения opener
        non_blind_players = [
            p for p in active_players 
            if p.position not in ["SB", "BB"]
        ]
        
        # Находим первого рейзера
        first_raiser = self._find_first_raiser(non_blind_players)
        
        if first_raiser is None:
            info.is_open_raise = True
            return info
        
        # Заполняем информацию о первом рейзере
        info.first_raiser_seat = first_raiser.seat
        info.first_raiser_position = first_raiser.position
        info.first_raiser_amount_bb = self._safe_bet(first_raiser.last_bet) / self.bb
        info.total_raises = 1
        
        # Ищем 3-бет
        three_bettor = self._find_3bettor(active_players, first_raiser)
        
        if three_bettor is None:
            info.callers = self._find_callers(active_players, first_raiser)
            return info
        
        # Заполняем 3-бет
        info.is_3bet_pot = True
        info.three_bettor_seat = three_bettor.seat
        info.three_bettor_position = three_bettor.position
        info.three_bet_amount_bb = self._safe_bet(three_bettor.last_bet) / self.bb
        info.total_raises = 2
        
        # Ищем 4-бет
        four_bettor = self._find_4bettor(active_players, three_bettor)
        
        if four_bettor is not None:
            info.is_4bet_pot = True
            info.four_bettor_seat = four_bettor.seat
            info.four_bet_amount_bb = self._safe_bet(four_bettor.last_bet) / self.bb
            info.total_raises = 3
        
        # Кто заколлировал
        last_raiser = four_bettor if four_bettor else three_bettor
        info.callers = self._find_callers(active_players, last_raiser)
        
        return info
    
    def _find_first_raiser(self, players: List[Player]) -> Optional[Player]:
        """Находит первого открывшегося (рейз >= 2.0BB)"""
        for player in players:
            bet = self._safe_bet(player.last_bet)
            if bet <= 0:
                continue
            bet_bb = bet / self.bb
            if bet_bb >= 2.0:
                return player
        return None
    
    def _find_3bettor(self, players: List[Player], first_raiser: Player) -> Optional[Player]:
        """Находит 3-беттора (рейз > 2.0x первого рейзера)"""
        first_bet = self._safe_bet(first_raiser.last_bet)
        if first_bet <= 0:
            return None
        
        for player in players:
            if player.seat == first_raiser.seat:
                continue
            
            bet = self._safe_bet(player.last_bet)
            if bet >= first_bet * 2.0 and bet > 0:
                return player
        
        return None
    
    def _find_4bettor(self, players: List[Player], three_bettor: Player) -> Optional[Player]:
        """Находит 4-беттора (рейз > 2.0x 3-бета)"""
        three_bet = self._safe_bet(three_bettor.last_bet)
        if three_bet <= 0:
            return None
        
        for player in players:
            if player.seat == three_bettor.seat:
                continue
            
            bet = self._safe_bet(player.last_bet)
            if bet >= three_bet * 2.0 and bet > 0:
                return player
        
        return None
    
    def _find_callers(self, players: List[Player], last_raiser: Player) -> List[int]:
        """Находит тех, кто заколлировал последнего рейзера"""
        callers = []
        target_bet = self._safe_bet(last_raiser.last_bet)
        if target_bet <= 0:
            return callers
        
        for player in players:
            if player.seat == last_raiser.seat:
                continue
            
            bet = self._safe_bet(player.last_bet)
            # Колл ≈ последнему рейзу (с допуском 0.5BB)
            if abs(bet - target_bet) < self.bb * 0.5 and bet > 0:
                callers.append(player.seat)
        
        return callers
    
    def calculate_hero_to_call(self, hero: Player) -> float:
        """Сколько герою нужно заколлить (в BB)"""
        hero_bet = self._safe_bet(hero.last_bet)
        if hero_bet > 0:
            return 0.0
        
        # Находим максимальную ставку за столом
        max_bet = max((self._safe_bet(p.last_bet) for p in self.table.players), default=0)
        
        to_call = max_bet - hero_bet
        return to_call / self.bb if self.bb > 0 else 0


def analyze_preflop(table: PokerTable) -> PreflopActionInfo:
    """Анализирует префлоп-экшен и обновляет table.preflop_action"""
    analyzer = PreflopAnalyzer(table)
    info = analyzer.analyze()
    
    table.preflop_action = info
    
    hero = next((p for p in table.players if p.is_hero), None)
    if hero:
        info.hero_to_call_bb = analyzer.calculate_hero_to_call(hero)
        
        # Определяем действие героя
        hero_bet = analyzer._safe_bet(hero.last_bet)
        if hero_bet == 0:
            info.hero_last_action = "fold" if info.hero_to_call_bb > 0 else None
        elif info.first_raiser_seat == hero.seat:
            info.hero_last_action = "open_raise"
        elif info.three_bettor_seat == hero.seat:
            info.hero_last_action = "3bet"
        elif info.four_bettor_seat == hero.seat:
            info.hero_last_action = "4bet"
        else:
            info.hero_last_action = "call"
    
    return info