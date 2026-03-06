POSITIONS_6MAX = [
    "BTN",
    "SB",
    "BB",
    "UTG",
    "MP",
    "CO"
]

class PositionAssigner:
    def __init__(self, positions_map=None):
        self.positions_map = positions_map or POSITIONS_6MAX

    def assign(self, players):
        btn_index = None
        for i, p in enumerate(players):
            if getattr(p, "is_button", False):
                btn_index = i
                break
        if btn_index is None:
            return

        n = len(players)
        for i, p in enumerate(players):
            pos_index = (i - btn_index) % n
            p.position = self.positions_map[pos_index]