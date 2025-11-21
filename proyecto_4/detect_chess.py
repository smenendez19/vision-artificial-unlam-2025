import time

import cv2
from ultralytics import YOLO

# MODEL_PATH = "runs/chess_training/chess_v1/weights/best.pt"
MODEL_PATH = "runs/chess_training/chess_v2/weights/best.pt"

CONF_THRESHOLD = 0.25

model = YOLO(MODEL_PATH)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara.")

print("Para salir presione Q")

prev_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error al leer frame de la cámara.")
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = model.predict(source=frame_rgb, conf=CONF_THRESHOLD, device=0, verbose=False)

    for r in results:
        annotated_frame = r.plot()
        boxes = r.boxes

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time else 0
        prev_time = curr_time

        cv2.putText(
            annotated_frame,
            f"FPS: {fps:.1f}",
            (8, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2,
        )

        # Mostrar por consola las detecciones
        for box in boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            name = model.names[cls]
            print(f"{name}: {conf:.2f}")

        cv2.imshow("Deteccion de piezas de ajedrez", annotated_frame)

    # Salir con 'Q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Cámara cerrada correctamente.")
