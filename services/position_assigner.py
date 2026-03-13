POSITIONS = {
    6: ["BU", "SB", "BB", "UTG", "MP", "CO"],
    5: ["BU", "SB", "BB", "MP", "CO"],
    4: ["BU", "SB", "BB", "CO"],
    3: ["BU", "SB", "BB"],
    2: ["SB", "BB"],
}


class PositionAssigner:

    def assign(self, players):

        # очистить старые позиции
        for p in players:
            p.position = ""

        button = next((p for p in players if p.is_button), None)

        if button is None:
            return

        seats = len(players)

        # порядок игроков начиная с BU
        order = []

        for i in range(seats):

            seat = (button.seat - i) % seats
            player = players[seat]

            if player.is_active:
                order.append(player)

        active_count = len(order)

        if active_count < 2:
            return

        positions = POSITIONS.get(active_count)

        if not positions:
            return

        for i, player in enumerate(order):

            if i < len(positions):
                player.position = positions[i]