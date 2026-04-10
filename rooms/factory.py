from rooms.replaypoker_room import ReplayPokerRoom
from rooms.replaypoker_geometry import ReplayPokerGeometry

def get_room(room_name: str, seats: int, hero_nickname: str):
    """Фабрика для создания room-specific экземпляров"""
    room_name = room_name.lower()
    
    if room_name == "replaypoker":
        return ReplayPokerRoom(seats, hero_nickname)
    
    raise ValueError(f"Unknown room: {room_name}")

def get_room_geometry_class(room_name: str, seats: int):
    """Фабрика для геометрии (BaseRoomGeometry) — для Pipeline"""
    room_name = room_name.lower()
    if room_name == "replaypoker":
        return ReplayPokerGeometry(seats)
    raise ValueError(f"Unknown room: {room_name}")