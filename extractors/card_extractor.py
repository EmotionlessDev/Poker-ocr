from utils.image_utils import safe_crop, prepare_nn_canvas
from domain.state import Card

class CardExtractor:
    def __init__(self, nn_client, hero_canvas_size=(1280,800)):
        self.nn = nn_client
        self.hero_canvas_size = hero_canvas_size

    def extract_board(self, frame, comm_zone):
        crop = safe_crop(frame, comm_zone)
        if crop is None:
            return []
        nn_result = self.nn.predict(crop)
        return [Card(rank=c["rank"], suit=c["suit"]) for c in nn_result.get("cards", [])]

    def extract_hero(self, frame, hero_zone):
        crop = safe_crop(frame, hero_zone)
        if crop is None:
            return []
        canvas = prepare_nn_canvas(crop, *self.hero_canvas_size)
        nn_result = self.nn.predict(canvas)
        return [Card(rank=c["rank"], suit=c["suit"]) for c in nn_result.get("cards", [])]