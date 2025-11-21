# Proyecto 4 - Vision Artificial
# Transfer learning con YOLOv8 para deteccion de objetos

import os

import torch
from ultralytics import YOLO


def train_model(model, data, name):
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    PROJECT_DIR = os.path.join(BASE_DIR, "runs", "chess_training")

    # Cargar modelo
    model = YOLO(model)

    # Entrenar
    model.train(
        data=data,
        epochs=50,
        imgsz=640,
        device=0,
        batch=8,
        workers=4,
        project=PROJECT_DIR,
        name=name,
        exist_ok=True,
        verbose=True
    )


if __name__ == "__main__":

    # Check CUDA
    print("CUDA:", torch.cuda.is_available())
    print("CUDA Device:", torch.cuda.get_device_name(0))

    # Train model
    # train_model("yolov8n.pt", "chess_model/data.yaml", "chess_v1")

    # Train model with best weights
    train_model("runs/chess_training/chess_v1/weights/best.pt", "chess_model_new/data.yaml", "chess_v2")
