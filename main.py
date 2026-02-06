import cv2
from ui_profiles.replay import REPLAYPOKER_PROFILE
from detectors.panel_detector import PanelDetector
from app.pipeline import PokerVisionPipeline
from debug.visualize import DebugVisualizer

frame = cv2.imread("images/table.png")

panel_detector = PanelDetector(REPLAYPOKER_PROFILE)
pipeline = PokerVisionPipeline(panel_detector)

result = pipeline.process(frame)

panels = result["panels"]
table_center = result["table_center"]

vis = frame.copy()

DebugVisualizer.draw_panels(vis, panels)
DebugVisualizer.draw_table_center(vis, table_center)
DebugVisualizer.draw_rect(vis, result["community_zone"], color=(0, 0, 255), thickness=2)

cv2.imshow("Poker Vision Debug", vis)
cv2.waitKey(0)


result = pipeline.process(frame)

