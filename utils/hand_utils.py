from typing import List, Tuple
from domain.state import Card


# Маппинг рангов для сортировки
RANK_ORDER = "23456789TJQKA"
SUIT_SYMBOLS = {"hearts": "h", "diamonds": "d", "clubs": "c", "spades": "s"}


def card_to_string(card: Card) -> str:
    """Card(rank='A', suit='spades') → 'As'"""
    rank = card.rank if card.rank != '10' else 'T'
    suit = SUIT_SYMBOLS.get(card.suit, card.suit[0].lower())
    return f"{rank}{suit}"


def cards_to_sorted_string(cards: List[Card]) -> str:
    """Сортирует две карты: старшая первая, suited суффикс"""
    if len(cards) != 2:
        return ""
    
    c1, c2 = cards
    r1, r2 = c1.rank if c1.rank != '10' else 'T', c2.rank if c2.rank != '10' else 'T'
    
    # Сортируем по старшинству
    if RANK_ORDER.index(r1) < RANK_ORDER.index(r2):
        r1, r2 = r2, r1
        c1, c2 = c2, c1
    
    # Для пар (одинаковых рангов) всегда возвращаем без суффикса s/o
    if r1 == r2:
        return f"{r1}{r2}"
    
    suited = "s" if c1.suit == c2.suit else "o"
    return f"{r1}{r2}{suited}"


def parse_hand_range_token(token: str) -> List[Tuple[str, str]]:
    """
    Парсит один токен ренджа в список рук.
    
    Примеры:
    - "AA" → [("A", "A")]
    - "AKs" → [("A", "K", "s")]
    - "55-22" → [("5","5"), ("4","4"), ("3","3"), ("2","2")]
    - "AKs-A2s" → все suited AK, AQ, AJ, ..., A2
    """
    hands = []
    
    # Пары: "55-22"
    if "-" in token and token[0].isdigit() and token[1].isdigit():
        start_rank = token[0]
        end_rank = token[3]
        for r in RANK_ORDER[RANK_ORDER.index(end_rank):RANK_ORDER.index(start_rank)+1]:
            hands.append((r, r))
    
    # Suited broadways: "AKs-A2s"
    elif "-" in token and token.endswith("s"):
        high = token[1]  # K из AKs
        low = token.split("-")[1][1]  # 2 из A2s
        for r in RANK_ORDER[RANK_ORDER.index(low):RANK_ORDER.index(high)+1]:
            hands.append(("A", r, "s"))
    
    # Offsuit: "AKo"
    elif token.endswith("o"):
        hands.append((token[0], token[1], "o"))
    
    # Suited: "AKs"
    elif token.endswith("s"):
        hands.append((token[0], token[1], "s"))
    
    # Pocket pair: "AA"
    elif len(token) == 2 and token[0] == token[1]:
        hands.append((token[0], token[0]))
    
    return hands


def hand_matches_range(hand_str: str, range_tokens: List[str]) -> bool:
    """
    Проверяет, входит ли рука в список токенов ренджа.
    
    hand_str: "AKs", "77", "QJo"
    range_tokens: ["AA-55", "AKs-A2s", "KQo"]
    """
    if not hand_str or len(hand_str) < 2:
        return False
    
    # Нормализуем руку
    rank1, rank2 = hand_str[0], hand_str[1]
    suited = hand_str[2] if len(hand_str) > 2 else None
    
    RANK_ORDER = "23456789TJQKA"
    
    for token in range_tokens:
        token = token.strip()
        if not token:
            continue
        
        # Пары: "AA-55" или "55-22"
        if "-" in token and len(token) == 5:
            # Проверяем что это диапазон пар (оба символа одинаковые)
            start_part = token.split("-")[0]
            end_part = token.split("-")[1]
            
            if len(start_part) == 2 and len(end_part) == 2 and start_part[0] == start_part[1] and end_part[0] == end_part[1]:
                # Диапазон пар типа "AA-55" или "55-22"
                if rank1 == rank2:  # pocket pair
                    start_rank = start_part[0]
                    end_rank = end_part[0]
                    low_idx = min(RANK_ORDER.index(start_rank), RANK_ORDER.index(end_rank))
                    high_idx = max(RANK_ORDER.index(start_rank), RANK_ORDER.index(end_rank))
                    curr_idx = RANK_ORDER.index(rank1)
                    if low_idx <= curr_idx <= high_idx:
                        return True
        
        # Suited range: "AKs-A2s"
        elif "-" in token and token.endswith("s") and len(token) == 7:
            if suited == "s" and rank1 == "A":
                high = token[1]
                low = token.split("-")[1][1]
                if RANK_ORDER.index(low) <= RANK_ORDER.index(rank2) <= RANK_ORDER.index(high):
                    return True
        
        # Offsuit range: "KQo-K9o"
        elif "-" in token and token.endswith("o") and len(token) == 7:
            parts = token.split("-")
            r1 = parts[0][0]
            r2_high = parts[0][1]
            r2_low = parts[1][1]
            if suited == "o" and rank1 == r1:
                if RANK_ORDER.index(r2_low) <= RANK_ORDER.index(rank2) <= RANK_ORDER.index(r2_high):
                    return True
        
        # Конкретная рука
        elif token == hand_str:
            return True
        
        # Pocket pair exact
        elif len(token) == 2 and token[0] == token[1] and hand_str == token:
            return True
    
    return False