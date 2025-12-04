"""
Utilidades para manejo de archivos
"""

import os
import sys
import time
from datetime import datetime

import cv2
from config import Config

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def guardar_frame_temporal(frame, prefijo="frame"):
    """
    Guarda un frame temporalmente

    Args:
        frame: Frame de OpenCV
        prefijo (str): Prefijo del nombre

    Returns:
        str: Ruta del archivo temporal
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{prefijo}_{timestamp}.jpg"
    filepath = os.path.join(Config.TEMP_DIR, filename)

    cv2.imwrite(filepath, frame)

    return filepath


def limpiar_archivos_temporales(max_edad_minutos=10):
    """
    Limpia archivos temporales antiguos

    Args:
        max_edad_minutos (int): Edad maxima en minutos
    """
    ahora = time.time()
    max_edad_segundos = max_edad_minutos * 60

    archivos_eliminados = 0

    for archivo in os.listdir(Config.TEMP_DIR):
        ruta = os.path.join(Config.TEMP_DIR, archivo)

        if os.path.isfile(ruta):
            edad = ahora - os.path.getmtime(ruta)

            if edad > max_edad_segundos:
                try:
                    os.remove(ruta)
                    archivos_eliminados += 1
                except Exception:
                    pass

    if archivos_eliminados > 0:
        print(f"Limpiados {archivos_eliminados} archivos temporales")
