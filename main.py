import cv2
from ui_profiles.replay import REPLAYPOKER_PROFILE
from detectors.panel_detector import PanelDetector
from app.pipeline import PokerVisionPipeline

frame = cv2.imread("images/table.png")

panel_detector = PanelDetector(REPLAYPOKER_PROFILE)
pipeline = PokerVisionPipeline(panel_detector)

panels = pipeline.process(frame)

for p in panels:
    cv2.rectangle(frame, (p.x1, p.y1), (p.x2, p.y2), (0,255,0), 2)

cv2.imshow("Panels", frame)
cv2.waitKey(0)
