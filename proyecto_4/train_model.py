# Proyecto 4 - Vision Artificial
# Transfer learning con YOLOv8 para deteccion de objetos

import os

import torch
from ultralytics import YOLO


def main():
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_DIR = os.path.join(BASE_DIR, "runs", "chess_training")

    # Cargar modelo
    model = YOLO("yolov8n.pt", "v8")

    # Entrenar
    model.train(
        data="chess_model/data.yaml",
        epochs=50,
        imgsz=640,
        device=0,
        batch=8,
        workers=4,
        project=PROJECT_DIR,
        name="chess_v1",
        exist_ok=True,
        verbose=True
    )


if __name__ == "__main__":

    # Check CUDA
    print("CUDA:", torch.cuda.is_available())
    print("CUDA Device:", torch.cuda.get_device_name(0))

    # Train model
    main()
