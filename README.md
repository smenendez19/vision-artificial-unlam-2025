# Trabajos Practicos para Vision Artificial

## Grupo 1

## Bibliotecas utilizadas

Se uso un entorno virtual de Python 3.12 para los trabajos

- OpenCV
- Mediapipe
- YOLOv8

## Proyecto 0

Presentacion inicial con mediapipe para iniciar la materia.
Se realizo un contador de manos con OpenCV y el entrenamiento de manos de mediapipe para probar las bibliotecas.

## Proyecto 1

Reconocimiento de formas por plantillas y preprocesamiento.

- `preprocesamiento.py`: toma imágenes de `images/` y genera plantillas binarias en `templates/` aplicando umbralización (inversa) y morfología para limpiar ruido.
- `main.py`: abre la cámara y permite seleccionar una ROI y ajustar parámetros (umbral, tamaño de kernel morfológico, área mínima). Extrae contornos y compara contra las plantillas mediante `cv2.matchShapes` para rotular la forma más similar. Muestra un panel con: imagen completa anotada, ROI, binaria y binaria tras morfología.

## Proyecto 2

Clasificación de objetos con aprendizaje automático usando descriptores de Hu.

- `generadorDescriptores.py`: captura desde cámara, segmenta la ROI y calcula los 7 invariantes de Hu del contorno principal, imprimiéndolos listos para construir el dataset.
- `entrenar.py`: entrena un `DecisionTreeClassifier` (scikit-learn) sobre un dataset de Hu moments y guarda el modelo en `clasificador_formas.joblib`. Exporta además una visualización del árbol.
- `clasificador.py`: carga el modelo entrenado y clasifica en tiempo real objetos en la ROI (clases ejemplo: llave, moneda, tijera). Permite ajustar umbral, kernel, área mínima y un umbral de confianza para mostrar la predicción y sus probabilidades.

## Proyecto 3

Corrección de perspectiva con homografía y visualización de grilla.

- `main.py`: herramienta interactiva con dos modos para calcular la homografía de un plano:
  - Modo QR: detecta automáticamente las 4 esquinas de un código QR (`cv2.QRCodeDetector`) y calcula la homografía.
  - Modo Clics: permite seleccionar manualmente 4 puntos en la imagen.
 Una vez definida la homografía, muestra la proyección de una grilla en perspectiva sobre la imagen y un warp frontal del plano en una ventana aparte.

## Proyecto 4

Detección de piezas de ajedrez con YOLOv8 y flujo de transferencia de aprendizaje.

- `requirements.txt`: dependencias para YOLOv8, OpenCV y PyTorch (con nota para instalación CUDA desde el índice oficial de PyTorch).
- `train_model.py`: entrena un modelo base `yolov8n.pt` sobre el dataset definido en `chess_model/data.yaml`. Guarda resultados en `runs/chess_training/chess_v1`.
- `retrain_model.py`: realiza fine-tuning a partir de un modelo previo (por ejemplo `runs/chess_training/chess_v1/weights/best.pt`) usando un dataset actualizado en `chess_model_new/data.yaml`, y guarda `chess_v2`.
- `detect_chess.py`: inferencia en tiempo real desde cámara usando un checkpoint entrenado (por defecto `runs/chess_training/chess_v1/weights/best.pt`), mostrando FPS y detecciones.
- `transfer_learning.py`: captura de imágenes desde cámara para recolectar nuevos datos y guardarlos en `chess_model_new/images/` para reetiquetar y reentrenar.
- `chess_model/`: carpeta esperada con dataset en formato YOLO (images/ y labels/ para train/val/test) y archivo `data.yaml` de configuración.
- `chess_model_new/`: carpeta de trabajo para nuevos datos a etiquetar y su `data.yaml` correspondiente para reentrenamiento.
- `runs/`: resultados de entrenamiento (pesos, métricas, gráficos) organizados por experimento (`chess_training/chess_v1`, `chess_training/chess_v2`, etc.).

Notas:

- El dataset de referencia proviene de Roboflow (chess pieces). Asegurá colocar `data.yaml` y las carpetas `train/`, `valid/` y `test/` dentro de `chess_model/` siguiendo el formato YOLOv8.
- Para GPU NVIDIA en Windows, instalá PyTorch con la URL de índice CUDA indicada en `proyecto_4/README.md` antes de instalar el resto de librerías.
