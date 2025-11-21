import os

import cv2

cap = cv2.VideoCapture(0)

if os.path.exists("dataset/images") is False:
    os.makedirs("dataset/images")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Captura", frame)
    key = cv2.waitKey(1)

    if key == ord('s'):
        unique_id = cv2.getTickCount()
        filename = f"dataset/images/frame_{unique_id}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Guardada: {filename}")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
