import os

import cv2

# Preprocesamiento de imagenes

image_path = "images"

for img_file in os.listdir(image_path):

    # Monocromatica
    img = cv2.imread(os.path.join(image_path, img_file), cv2.IMREAD_GRAYSCALE)

    # Threshold
    _, clean = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

    # Morfologia (Ruido)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel)

    img_template_file = img_file.split(".")[0] + ".png"
    cv2.imwrite(f"templates/{img_template_file}", clean)
