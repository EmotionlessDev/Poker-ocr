import subprocess
import json
import base64
import cv2
import numpy as np
from pathlib import Path

class NeuralNetClient:

    def __init__(self):
        project_root = Path(__file__).resolve().parent.parent

        runner_path = project_root / "nn_service" / "nn_runner.py"

        python_path = project_root / "nn_service" / "venv" / "Scripts" / "python.exe"

        self.process = subprocess.Popen(
            [str(python_path), str(runner_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )

    def predict(self, img):
        _, buffer = cv2.imencode(".jpg", img)
        img_base64 = base64.b64encode(buffer).decode()

        request = json.dumps({"image": img_base64})
        self.process.stdin.write(request + "\n")
        self.process.stdin.flush()

        response = self.process.stdout.readline()
        return json.loads(response)

    def close(self):
        self.process.terminate()