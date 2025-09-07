import cv2
import numpy as np

# Cargar imagen
img = cv2.imread('vaso.jpg', cv2.IMREAD_GRAYSCALE)

# Threshold más agresivo para limpiar fondo
_, clean = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# Operaciones morfológicas para limpiar
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel)

# Guardar template limpia
cv2.imwrite('templates/vaso.png', clean)