import cv2
from app.pipeline import PokerVisionPipeline
from debug.visualize import DebugVisualizer

frame = cv2.imread("images/table.png")

pipeline = PokerVisionPipeline(seats=6)

result = pipeline.process(frame)

vis = frame.copy()

DebugVisualizer.draw_table_center(vis, result["table_center"])
DebugVisualizer.draw_rect(vis, result["community_zone"], color=(0, 0, 255), thickness=2)
DebugVisualizer.draw_player_positions(vis, result["player_positions"])

cv2.imshow("Poker Vision Debug", vis)
cv2.waitKey(0)
cv2.destroyAllWindows()
