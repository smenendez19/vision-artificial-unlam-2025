# Proyecto 4 - Vision Artificial
# Transfer learning con YOLOv8 para deteccion de objetos

import os

from ultralytics import YOLO


def main():
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_DIR = os.path.join(BASE_DIR, "runs", "chess_training")

    # Cargar modelo
    model = YOLO("runs/chess_training/chess_v1/weights/best.pt")

    # Entrenar
    model.train(
        data="chess_model_new/data.yaml",
        epochs=50,
        imgsz=640,
        device=0,
        batch=8,
        workers=4,
        project=PROJECT_DIR,
        name="chess_v2",
        exist_ok=True,
        verbose=True
    )


if __name__ == "__main__":
    main()
