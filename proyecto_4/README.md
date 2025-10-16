# Transfer learning con YOLOv8

Dataset: <https://public.roboflow.com/object-detection/chess-full/24>

## Instalacion Pytorch

    pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126

## Instalacion resto de librerias

## Pasos para usar el proyecto

### 1 - Instalacion de librerias en venv

Crear un entorno virtual

    python -m venv venv

Instalar Pytorch

    pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126

Instalar el resto de librerias de requirements.txt

    pip3 install -r requirements.txt

## 2 - Descargar dataset modelo chess de Roboflow

Link: <https://public.roboflow.com/object-detection/chess-full>

Agregar las carpetas test, train, model y el archivo data.yaml dentro de una carpeta chess_model en la raiz del proyecto.

## 3 - Entrenamiento del modelo

Ejecutar check_cuda para detectar placa de video

    python check_cuda.py

Entrenar el modelo

    python train_model.py

## 4 - Prueba de deteccion de objetos

Ejecutar el siguiente programa:

    python detect_chess.py

## 5 - Toma de imagenes para reentrenar el modelo

Ejecutar el programa e ir sacando nuevos frames con la camara pulsando s

    python transfer_learning.py

## 6 - Etiquetar (label) las imagenes

Utilizando Roboflow etiquetamos las imagenes que vamos a importar y luego exportamos en formato YOLOv8

## 7 Reentrenar el modelo con el existente

Ejecutar el siguiente codigo:

    python retrain_model.py
