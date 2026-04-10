from abc import ABC, abstractmethod
from domain.geometry import Rect, Point

class BaseRoomGeometry(ABC):

    def __init__(self, seats: int):
        self.seats = seats

    @abstractmethod
    def compute_table_center(self, frame_shape) -> Point:
        pass

    @abstractmethod
    def compute_community_zone(self, table_center: Point, table_rect: Rect) -> Rect:
        pass

    @abstractmethod
    def compute_player_zones(self, table_rect: Rect) -> list[Rect]:
        pass