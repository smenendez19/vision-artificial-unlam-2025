"""
Modulo para captura de dataset de rostros
"""

import os
import sys
from datetime import datetime

import cv2
from config import Config

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def evaluar_calidad_foto(frame, bbox):
    """
    Evalua la calidad de una foto de rostro

    Args:
        frame: Frame de OpenCV
        bbox: Tupla (x, y, w, h)

    Returns:
        tuple: (puntuacion, mensaje)
    """
    x, y, w, h = bbox

    # Extraer region del rostro
    rostro = frame[y: y + h, x: x + w]

    # 1. Verificar tamano
    if w < 150 or h < 150:
        return 0, "Rostro muy pequeno - acercate mas"

    if w > 500 or h > 500:
        return 0, "Rostro muy grande - alejate un poco"

    # 2. Verificar brillo
    gray = cv2.cvtColor(rostro, cv2.COLOR_BGR2GRAY)
    brillo = gray.mean()

    if brillo < 60:
        return 0, "Muy oscuro - mejora la iluminacion"
    if brillo > 200:
        return 0, "Muy brillante - reduce la luz"

    # 3. Verificar nitidez (desenfoque)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    nitidez = laplacian.var()

    if nitidez < 100:
        return 0, "Desenfocado - manten quieta la camara"

    # 4. Verificar posicion (centrado)
    frame_h, frame_w = frame.shape[:2]
    centro_x = x + w / 2
    centro_y = y + h / 2

    if abs(centro_x - frame_w / 2) > frame_w / 4:
        return 0, "No centrado horizontalmente"

    if abs(centro_y - frame_h / 2) > frame_h / 4:
        return 0, "No centrado verticalmente"

    # Calcular puntuacion (0-100)
    puntuacion_brillo = max(0, 100 - abs(brillo - 130))
    puntuacion_nitidez = min(100, (nitidez / 500) * 100)
    puntuacion_tamano = 100 if 200 <= w <= 400 else 50

    puntuacion = (puntuacion_brillo + puntuacion_nitidez + puntuacion_tamano) / 3

    mensaje = "Calidad: "
    if puntuacion >= 80:
        mensaje += "EXCELENTE"
    elif puntuacion >= 60:
        mensaje += "BUENA"
    elif puntuacion >= 40:
        mensaje += "ACEPTABLE"
    else:
        mensaje += "REGULAR"

    return puntuacion, mensaje


class CapturadorDataset:
    """
    Clase para capturar datasets de rostros de alta calidad
    """

    def __init__(self):
        """Inicializar capturador"""
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        Config.init_app()

    def capturar_dataset_persona(self, nombre, categoria, objetivo=10):
        """
        Captura multiples fotos de una persona para dataset

        Args:
            nombre: Nombre de la persona
            categoria: Categoria (empleados, vip, visitantes)
            objetivo: Cantidad de fotos a capturar

        Returns:
            bool: True si se completo exitosamente
        """
        # Crear carpeta para la persona
        carpeta_destino = os.path.join(Config.DATABASE_DIR, categoria, nombre)
        os.makedirs(carpeta_destino, exist_ok=True)

        print(f"\nCarpeta creada: {carpeta_destino}")
        print(f"\nSe capturaran {objetivo} fotos de alta calidad")
        print("\nInstrucciones:")
        print("  - Manten el rostro de frente")
        print("  - Buena iluminacion frontal")
        print("  - No muevas la cabeza bruscamente")
        print("  - Variaciones: con/sin sonrisa, ligeros angulos")
        print("\nPresiona ESPACIO cuando veas EXCELENTE")
        print("Presiona Q para cancelar\n")

        input("Presiona ENTER para comenzar...")

        # Iniciar camara
        # cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: No se pudo abrir la camara")
            return False

        fotos_capturadas = 0

        print(f"\nCamara iniciada - Capturando {objetivo} fotos...\n")

        while fotos_capturadas < objetivo:
            ret, frame = cap.read()

            if not ret:
                print("Error capturando frame")
                break

            raw_frame = frame.copy()

            # Detectar rostros
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            mensaje_calidad = "No se detecta rostro"
            color_mensaje = (0, 0, 255)
            puntuacion = 0
            bbox_valido = None

            # Evaluar calidad si hay rostro
            if len(faces) > 0:
                # Usar el rostro mas grande
                bbox = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = bbox

                puntuacion, mensaje_calidad = evaluar_calidad_foto(frame, bbox)
                bbox_valido = bbox

                # Color segun calidad
                if puntuacion >= 80:
                    color_bbox = (0, 255, 0)
                    color_mensaje = (0, 255, 0)
                elif puntuacion >= 60:
                    color_bbox = (0, 255, 255)
                    color_mensaje = (0, 255, 255)
                else:
                    color_bbox = (0, 165, 255)
                    color_mensaje = (0, 165, 255)

                # Dibujar rectangulo
                cv2.rectangle(frame, (x, y), (x + w, y + h), color_bbox, 3)

                # Indicador de calidad
                cv2.putText(frame, f"Calidad: {puntuacion:.0f}/100", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bbox, 2)

            # Informacion en pantalla
            cv2.putText(frame, f"Fotos: {fotos_capturadas}/{objetivo}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            cv2.putText(frame, mensaje_calidad, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_mensaje, 2)

            if puntuacion >= 50:
                cv2.putText(frame, "ESPACIO para capturar", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow("Captura de Dataset - FACEGUARD", frame)

            # Controles
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q") or key == ord("Q"):
                print("\nCaptura cancelada")
                break

            elif key == ord(" ") and puntuacion >= 50 and bbox_valido is not None:
                # Capturar foto de alta calidad
                x, y, w, h = bbox_valido

                # Agregar margen
                margen = 30
                x_min = max(0, x - margen)
                y_min = max(0, y - margen)
                x_max = min(frame.shape[1], x + w + margen)
                y_max = min(frame.shape[0], y + h + margen)

                rostro = raw_frame[y_min:y_max, x_min:x_max]

                # Guardar
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"{nombre}_{timestamp}.jpg"
                filepath = os.path.join(carpeta_destino, filename)

                cv2.imwrite(filepath, rostro)
                fotos_capturadas += 1

                print(f"  Foto {fotos_capturadas}/{objetivo} capturada - Calidad: {puntuacion:.0f}/100")

                # Pausa breve
                cv2.waitKey(500)

        cap.release()
        cv2.destroyAllWindows()

        if fotos_capturadas == objetivo:
            print("\nDataset completo!")
            print(f"{fotos_capturadas} fotos guardadas en: {carpeta_destino}")
            return True
        else:
            print(f"\nSolo se capturaron {fotos_capturadas}/{objetivo} fotos")
            return False
