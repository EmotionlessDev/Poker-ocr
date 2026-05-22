"""
Префлоп ренджи для RFI (Raise First In) в формате Flopzilla.
Формат: "AA-55,AKs-A2s,KQs-K9s,..."
"""

RFI_RANGES = {
    "UTG": "AA-55,AKs-A2s,KQs-K9s,QJs-QTs,JTs,AKo-AJo,KQo",
    "UTG+1": "AA-55,AKs-A2s,KQs-K9s,QJs-QTs,JTs,AKo-AJo,KQo",
    "MP": "AA-55,AKs-A2s,KQs-K8s,QJs-Q9s,JTs-J9s,T9s,AKo-ATo,KQo-KJo",
    "CO": "AA-44,AKs-A2s,KQs-K3s,QJs-Q8s,JTs-J8s,T9s-T8s,98s,AKo-A9o,KQo-KTo,QJo-QTo,JTo",
    "BU": "AA-22,AKs-A2s,KQs-K2s,QJs-Q3s,JTs-J5s,T9s-T6s,98s-96s,87s-86s,76s-75s,65s-64s,54s,AKo-A4o,KQo-K9o,QJo-Q9o,JTo-J9o,T9o",
    "SB": "AA-22,AKs-A2s,KQs-K2s,QJs-Q3s,JTs-J5s,T9s-T6s,98s-96s,87s-86s,76s-75s,65s-64s,54s,AKo-A4o,KQo-K9o,QJo-Q9o,JTo-J9o,T9o",
    "BB": "AA-22,AKs-A2s,KQs-K2s,QJs-Q3s,JTs-J5s,T9s-T6s,98s-96s,87s-86s,76s-75s,65s-64s,54s,AKo-A4o,KQo-K9o,QJo-Q9o,JTo-J9o,T9o",
}

# 3-бет ренджи для разных позиций героя против позиций опенера
RANGES_3BET = {
    # Герой не в блайндах (общие ренджи для EP/MP)
    "3BET_VS_EP": "AA-99,AKs-ATs,KQs-KJs,AKo-AQo,A9s,A5s-A4s,KTs,KQo",
    "3BET_VS_MP": "AA-99,AKs-ATs,KQs-KJs,AKo-AQo,A9s,A5s-A4s,KTs,KQo",
    
    # Герой на BTN против CO
    "3BET_BTN_VS_CO": "AA-88,AKs-A9s,A5s-A4s,KQs-KTs,QJs-QTs,JTs,AKo-AJo,KQo,77-55,A8s-A6s,A3s,K9s,Q9s,J9s,T9s,ATo,KJo,QJo",
    
    # Герой в SB
    "3BET_SB_VS_EP": "AA-TT,AKs-ATs,A5s,KQs-KTs,QJs,AKo-AQo,99,A4s,KQo",
    "3BET_SB_VS_MP": "AA-TT,AKs-ATs,A5s,KQs-KTs,QJs,AKo-AQo,99,A4s,KQo",
    "3BET_SB_VS_CO": "AA-88,AKs-A9s,A5s-A4s,KQs-KTs,QJs-QTs,AKo-AJo,KQo,A3s,JTs,KJo",
    "3BET_SB_VS_BTN": "AA-55,AKs-A8s,A5s-A4s,KQs-K9s,QJs-QTs,JTs,AKo-ATo,KQo-KJo",
    
    # Герой в BB
    "3BET_BB_VS_EP": "AA-JJ,AKs-AQs,A5s-A2s,AKo,AJs-ATs,KQs-KTs,QJs-QTs,JTs,AQo",
    "3BET_BB_VS_MP": "AA-JJ,AKs-AQs,A5s-A2s,AKo,AJs-ATs,KQs-KTs,QJs-QTs,JTs,AQo",
    "3BET_BB_VS_CO": "AA-TT,AKs-ATs,A5s-A2s,KQs-KTs,QJs-QTs,JTs,AKo-AQo,K5s-K2s,ATo,KJo-KTo,QJo",
    "3BET_BB_VS_BU": "AA-TT,AKs-ATs,A5s-A2s,KQs-KTs,K5s-K2s,QJs-QTs,Q5s-Q2s,JTs,AKo-AQo,J9s-J5s,T9s-T6s,ATo,KJo-KTo,QJo-QTo,JTo",
    "3BET_BB_VS_SB": "AA-TT,AKs-ATs,A5s-A2s,KQs-KTs,K5s-K2s,QJs-QTs,Q5s-Q2s,JTs,AKo-AQo,A5o-A2o,J6s-J2s,T6s-T2s,A7o-A6o,K8o-K6o",
}

# Маппинг: (позиция героя, позиция опенера) → ключ ренджа
RANGES_3BET_KEYS = {
    # Герой не в блайндах (упрощённо)
    ("UTG", "MP"): "3BET_VS_MP",
    ("UTG", "CO"): "3BET_VS_EP",  # редкая ситуация
    ("MP", "CO"): "3BET_VS_MP",
    ("CO", "BTN"): "3BET_BTN_VS_CO",
    
    # Герой в SB
    ("SB", "UTG"): "3BET_SB_VS_EP",
    ("SB", "UTG+1"): "3BET_SB_VS_EP",
    ("SB", "MP"): "3BET_SB_VS_MP",
    ("SB", "CO"): "3BET_SB_VS_CO",
    ("SB", "BTN"): "3BET_SB_VS_BTN",
    
    # Герой в BB
    ("BB", "UTG"): "3BET_BB_VS_EP",
    ("BB", "UTG+1"): "3BET_BB_VS_EP",
    ("BB", "MP"): "3BET_BB_VS_MP",
    ("BB", "CO"): "3BET_BB_VS_CO",
    ("BB", "BTN"): "3BET_BB_VS_BU",
    ("BB", "SB"): "3BET_BB_VS_SB",
}