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
