from detectors.table_center import TableCenterEstimator
from domain.geometry import compute_community_cards_zone, Rect, Point

class PokerVisionPipeline:
    def __init__(self, panel_detector):
        self.panel_detector = panel_detector
        self.center_estimator = TableCenterEstimator()

    def process(self, frame):
        h, w = frame.shape[:2]  # размеры кадра

        panels = self.panel_detector.detect(frame)
        table_center = self.center_estimator.estimate_from_panels(panels, frame)

        # fallback: если центр стола не найден
        if table_center is None:
            table_center = Point(w // 2, h // 2)

        # Получаем рамку стола
        if panels:
            x1 = min(p.x1 for p in panels)
            y1 = min(p.y1 for p in panels)
            x2 = max(p.x2 for p in panels)
            y2 = max(p.y2 for p in panels)
            table_rect = Rect(x1, y1, x2, y2)
        else:
            # fallback: грубый прямоугольник вокруг центра
            table_rect = Rect(table_center.x - 200, table_center.y - 100,
                              table_center.x + 200, table_center.y + 100)

        community_zone = compute_community_cards_zone(table_center, table_rect)

        return {
            "panels": panels,
            "table_center": table_center,
            "community_zone": community_zone
        }
