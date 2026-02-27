import sys
import json
import cv2
import torch
import base64
import numpy as np
from pathlib import Path
from torchvision import transforms, models
from PIL import Image
from ultralytics import YOLO
import contextlib
import io

# Settings
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 128

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

rank_classes = ['10','2','3','4','5','6','7','8','9','A','J','K','Q']
suit_classes = ['clubs', 'diamonds', 'hearts', 'spades']

# Load models
yolo_model = YOLO(str(MODELS_DIR / "best.pt"))  # YOLO детекция карт

rank_model = models.resnet18()
rank_model.fc = torch.nn.Linear(rank_model.fc.in_features, len(rank_classes))
rank_model.load_state_dict(torch.load(MODELS_DIR / "rank_classifier.pth", map_location=DEVICE))
rank_model = rank_model.to(DEVICE).eval()

suit_model = models.resnet18()
suit_model.fc = torch.nn.Linear(suit_model.fc.in_features, len(suit_classes))
suit_model.load_state_dict(torch.load(MODELS_DIR / "suit_classifier.pth", map_location=DEVICE))
suit_model = suit_model.to(DEVICE).eval()

transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

def predict_rank(img_crop):
    img_tensor = transform(img_crop).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        out = rank_model(img_tensor)
        _, pred = torch.max(out, 1)
    return rank_classes[pred.item()]

def predict_suit(img_crop):
    img_tensor = transform(img_crop).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        out = suit_model(img_tensor)
        _, pred = torch.max(out, 1)
    return suit_classes[pred.item()]

def get_adaptive_imgsz(h, w, base_size=832, max_size=1280):
    scale = max(h, w) / 1280
    imgsz = int(base_size * scale)
    imgsz = round(imgsz / 32) * 32
    return max(640, min(imgsz, max_size))

def process_image(img):
    cards = []

    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        results = yolo_model(
            img,
            imgsz=get_adaptive_imgsz(img.shape[0], img.shape[1]),
            conf=0.25,
            verbose=False
        )

    for box in results[0].boxes.xyxy:
        x1, y1, x2, y2 = map(int, box.tolist())
        crop = img[y1:y2, x1:x2]
        crop_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))

        cards.append({
            "rank": predict_rank(crop_pil),
            "suit": predict_suit(crop_pil),
            "bbox": [x1, y1, x2, y2]
        })

    return {"cards": cards}

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            data = json.loads(line.strip())
            img_bytes = base64.b64decode(data["image"])
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            result = process_image(img)
            print(json.dumps(result), flush=True)

        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)

if __name__ == "__main__":
    main()