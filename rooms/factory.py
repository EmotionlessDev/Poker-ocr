from .replaypoker import ReplayPokerGeometry

def get_room_geometry(room_name: str, seats: int):
    room_name = room_name.lower()

    if room_name == "replaypoker":
        return ReplayPokerGeometry(seats)

    raise ValueError(f"Unknown room: {room_name}")