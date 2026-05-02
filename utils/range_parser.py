from typing import List


class RangeParser:
    """Парсит строку ренджа в формате Flopzilla в список рук"""
    
    @staticmethod
    def parse(range_str: str) -> List[str]:
        """
        "AA-55,AKs-A2s,KQo" → ["AA", "KK", ..., "AKs", "AQs", ..., "KQo"]
        
        Возвращает список нормализованных строк рук: ["AA", "AKs", "KQo", ...]
        """
        if not range_str:
            return []
        
        hands = []
        tokens = [t.strip() for t in range_str.split(",")]
        
        for token in tokens:
            hands.extend(RangeParser._expand_token(token))
        
        return hands
    
    @staticmethod
    def _expand_token(token: str) -> List[str]:
        """Раскрывает один токен в список конкретных рук"""
        result = []
        token = token.strip()
        
        if not token:
            return result
        
        RANKS = "23456789TJQKA"
        
        # === 1. Диапазон пар: "AA-44", "KK-88", "55-22" ===
        # ✅ Проверяем что обе части — пары (AA, KK, 55 и т.д.)
        if "-" in token and len(token) == 5 and token[0] == token[1] and token[3] == token[4]:
            start_rank = token[0]  # A из AA
            end_rank = token[3]    # 4 из 44
            for r in RANKS:
                if RANKS.index(end_rank) <= RANKS.index(r) <= RANKS.index(start_rank):
                    result.append(f"{r}{r}")
        
        # === 2. Suited Ace range: "AKs-A2s" ===
        elif "-" in token and token.startswith("A") and token.endswith("s"):
            parts = token.split("-")
            high = parts[0][1]  # K
            low = parts[1][1]   # 2
            for r in RANKS:
                if RANKS.index(low) <= RANKS.index(r) <= RANKS.index(high):
                    result.append(f"A{r}s")
        
        # === 3. Suited broadway range: "KQs-K9s" ===
        elif "-" in token and token.endswith("s") and len(token) == 7:
            parts = token.split("-")
            rank1 = parts[0][0]  # K
            rank2_high = parts[0][1]  # Q
            rank2_low = parts[1][1]   # 9
            for r in RANKS:
                if RANKS.index(rank2_low) <= RANKS.index(r) <= RANKS.index(rank2_high):
                    result.append(f"{rank1}{r}s")
        
        # === 4. Offsuit range: "KQo-K9o", "AKo-A4o" ===
        elif "-" in token and token.endswith("o") and len(token) == 7:
            parts = token.split("-")
            rank1 = parts[0][0]  # K из KQo, A из AKo
            rank2_high = parts[0][1]  # Q из KQo
            rank2_low = parts[1][1]   # 9 из K9o
            for r in RANKS:
                if RANKS.index(rank2_low) <= RANKS.index(r) <= RANKS.index(rank2_high):
                    result.append(f"{rank1}{r}o")
        
        # === 5. Одиночный offsuit: "KQo" ===
        elif token.endswith("o") and len(token) == 3:
            result.append(token)
        
        # === 6. Одиночный suited: "AKs" ===
        elif token.endswith("s") and len(token) == 3:
            result.append(token)
        
        # === 7. Пары: "AA", "KK", "88" ===
        elif len(token) == 2 and token[0] == token[1] and token[0] in RANKS:
            result.append(token)
        
        return result