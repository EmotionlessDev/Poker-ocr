class PositionAssigner:

    def __init__(self):

        # позиции для 6max
        self.positions_map = {
            0: "BTN",
            1: "SB",
            2: "BB",
            3: "UTG",
            4: "MP",
            5: "CO"
        }

    def assign(self, players):

        # только активные игроки
        active = [p for p in players if p.is_active]

        if not active:
            return

        btn_index = None

        for i, p in enumerate(active):
            if p.is_button:
                btn_index = i
                break

        if btn_index is None:
            return

        n = len(active)

        for i, p in enumerate(active):

            pos_index = (i - btn_index) % n

            # если игроков меньше чем 6 — просто берём первые позиции
            if pos_index in self.positions_map:
                p.position = self.positions_map[pos_index]
            else:
                p.position = ""