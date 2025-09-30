import cv2
import numpy as np
from collections import deque

# =========================================
# Parámetros
# =========================================
DEST_SIZE = 500  # tamaño del cuadrado frontal (px)
GRID_N = 3       # grilla NxN en la visualización
WINDOW_NAME_VIEW = "Vista"
WINDOW_NAME_WARP = "Frontal (warp)"

# =========================================
# Utilidades geométricas
# =========================================
def order_corners(pts):
    """
    Ordena 4 puntos (x,y) en el orden: TL, TR, BR, BL.
    pts: array de shape (4,2).
    """
    pts = np.array(pts, dtype=np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).ravel()

    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)

def compute_homography(src_pts, size=DEST_SIZE):
    """
    src_pts: cuatro puntos de la imagen en perspectiva (TL,TR,BR,BL)
    size: tamaño del cuadrado frontal de destino (size x size)
    """
    dst_pts = np.array([
        [0, 0],
        [size - 1, 0],
        [size - 1, size - 1],
        [0, size - 1]
    ], dtype=np.float32)
    H, _ = cv2.findHomography(src_pts, dst_pts, method=cv2.RANSAC)
    return H

def draw_perspective_grid(frame, H, n=GRID_N, size=DEST_SIZE, color=(0,255,0), thickness=1):
    """
    Dibuja en 'frame' una grilla cuadrada NxN en perspectiva,
    mapeando líneas del plano frontal (destino) hacia la imagen original (fuente).
    """
    if H is None:
        return frame

    H_inv = np.linalg.inv(H)

    def warp_points(pts_2d, Hmat):
        """pts_2d: (N,2) en coords destino → devuelve (N,2) en coords imagen"""
        pts = np.hstack([pts_2d, np.ones((pts_2d.shape[0], 1))])
        p = pts @ Hmat.T
        p = p[:, :2] / p[:, 2:3]
        return p

    # Líneas verticales y horizontales en el espacio destino
    num_samples = 50
    t = np.linspace(0, size - 1, num_samples).astype(np.float32)

    # Verticales: x = k*size/n
    for k in range(1, n):  # no dibujamos el borde externo, solo divisiones internas
        x = np.full_like(t, k * size / n)
        line_dst = np.stack([x, t], axis=1)
        line_img = warp_points(line_dst, H_inv).astype(int)
        cv2.polylines(frame, [line_img], isClosed=False, color=color, thickness=thickness)

    # Horizontales: y = k*size/n
    for k in range(1, n):
        y = np.full_like(t, k * size / n)
        line_dst = np.stack([t, y], axis=1)
        line_img = warp_points(line_dst, H_inv).astype(int)
        cv2.polylines(frame, [line_img], isClosed=False, color=color, thickness=thickness)

    return frame

def put_status_text(img, lines, org=(10,30)):
    y = org[1]
    for line in lines:
        cv2.putText(img, line, (org[0], y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2, cv2.LINE_AA)
        y += 28

# =========================================
# Modo por clics: manejo de mouse
# =========================================
class ClickCollector:
    def __init__(self):
        self.points = []
        self.active = False

    def start(self):
        self.points = []
        self.active = True

    def stop(self):
        self.active = False

    def callback(self, event, x, y, flags, param):
        if not self.active:
            return
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))

# =========================================
# Modo QR: detección esquinas del QR
# =========================================
def detect_qr_corners(frame, qrdetector):
    """
    Devuelve 4 esquinas (TL,TR,BR,BL) o None si no hay QR.
    """
    # detectAndDecode devuelve: data, points, straight_qrcode
    data, points, _ = qrdetector.detectAndDecode(frame)
    if points is None or len(points) == 0:
        return None, None

    # 'points' viene como (1,4,2) o (4,1,2) según versión; normalizamos a (4,2)
    pts = points.reshape(-1, 2).astype(np.float32)
    ordered = order_corners(pts)
    return ordered, data

# =========================================
# Loop principal
# =========================================
def main():
    cap = cv2.VideoCapture(0)  # importante: sin CAP_DSHOW en Linux
    if not cap.isOpened():
        print("No se pudo abrir la cámara. ¿Montaste /dev/video0 en el contenedor?")
        return

    cv2.namedWindow(WINDOW_NAME_VIEW, cv2.WINDOW_NORMAL)
    cv2.namedWindow(WINDOW_NAME_WARP, cv2.WINDOW_NORMAL)

    # Estado
    mode = "view"          # "view" | "qr" | "click"
    H = None               # homografía actual
    last_qr_pts = None     # últimos puntos detectados en modo QR (para confirmar con cualquier tecla)
    last_qr_data = None
    qrdetector = cv2.QRCodeDetector()

    clicker = ClickCollector()
    cv2.setMouseCallback(WINDOW_NAME_VIEW, clicker.callback)

    # Buffer de mensajes breves
    msg_queue = deque(maxlen=2)

    print("Controles: q → modo QR | h → modo clics | 'q' de nuevo en view para volver a QR")
    print("Cerrar ventanas o Ctrl+C para salir.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            display = frame.copy()

            if mode == "view":
                # Visualización: si hay H, dibujar grilla y mostrar warp frontal
                if H is not None:
                    draw_perspective_grid(display, H, n=GRID_N, size=DEST_SIZE, color=(0,255,0), thickness=2)
                    warp = cv2.warpPerspective(frame, H, (DEST_SIZE, DEST_SIZE))
                    cv2.imshow(WINDOW_NAME_WARP, warp)
                    put_status_text(display, ["[VIEW] Homografía activa (g = grilla, warp en ventana aparte)",
                                              "Teclas: q=QR, h=clics, cierra para salir"])
                else:
                    # Sin homografía aún
                    blank = np.zeros((DEST_SIZE, DEST_SIZE, 3), dtype=np.uint8)
                    cv2.putText(blank, "Sin homografia", (40, DEST_SIZE//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (200,200,200), 2, cv2.LINE_AA)
                    cv2.imshow(WINDOW_NAME_WARP, blank)
                    put_status_text(display, ["[VIEW] Sin homografía",
                                              "Teclas: q=QR, h=clics, cierra para salir"])

            elif mode == "qr":
                # Detección en vivo para que el usuario encuadre el QR
                pts, data = detect_qr_corners(frame, qrdetector)
                if pts is not None:
                    last_qr_pts = pts
                    last_qr_data = data
                    # Dibujar las esquinas del QR
                    for p in pts.astype(int):
                        cv2.circle(display, tuple(p), 6, (0, 255, 255), -1)
                    cv2.polylines(display, [pts.astype(int)], True, (0, 255, 255), 2)
                    put_status_text(display, ["[QR] QR detectado. Presiona cualquier tecla para confirmar.",
                                              "q/h/otra tecla confirma con el QR actual."])
                else:
                    put_status_text(display, ["[QR] Buscando QR...", "Presiona cualquier tecla para volver."])

            elif mode == "click":
                # Mostrar puntos clickeados
                for i, p in enumerate(clicker.points):
                    cv2.circle(display, p, 6, (255, 0, 255), -1)
                    cv2.putText(display, f"{i+1}", (p[0]+8, p[1]-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,255), 2)

                put_status_text(display, [
                    "[CLICS] Hacé clic en 4 vértices de un cuadrado en perspectiva.",
                    "Cualquier tecla antes del 4º clic: aborta (mantiene homografía previa)."
                ])

                if len(clicker.points) >= 4:
                    # Tomamos los primeros 4, ordenamos y computamos H
                    pts = order_corners(np.array(clicker.points[:4], dtype=np.float32))
                    H_new = compute_homography(pts, DEST_SIZE)
                    if H_new is not None:
                        H = H_new
                        msg_queue.append("Homografía actualizada (clics).")
                    else:
                        msg_queue.append("No se pudo computar la homografía (clics).")
                    clicker.stop()
                    mode = "view"

            # Mostrar mensajes breves, si hay
            if len(msg_queue) > 0:
                put_status_text(display, list(msg_queue), org=(10, display.shape[0]-10-28*len(msg_queue)))

            cv2.imshow(WINDOW_NAME_VIEW, display)

            # Lectura de teclado (1ms para mantener fluidez)
            key = cv2.waitKey(1) & 0xFF

            if key != 255:  # alguna tecla
                if mode == "view":
                    if key == ord('q'):
                        mode = "qr"
                        msg_queue.append("Modo QR: apunte a un código. Cualquier tecla confirma.")
                    elif key == ord('h'):
                        mode = "click"
                        clicker.start()
                        msg_queue.append("Modo clics: seleccione 4 puntos o presione tecla para abortar.")
                    else:
                        # otras teclas en view no hacen nada especial
                        pass
                elif mode == "qr":
                    # Confirmar con el último QR válido si existe
                    if last_qr_pts is not None:
                        H_new = compute_homography(last_qr_pts, DEST_SIZE)
                        if H_new is not None:
                            H = H_new
                            msg_queue.append("Homografía actualizada (QR).")
                        else:
                            msg_queue.append("No se pudo computar la homografía (QR).")
                    else:
                        msg_queue.append("No se detectó QR. Manteniendo homografía previa.")
                    mode = "view"
                    last_qr_pts, last_qr_data = None, None
                elif mode == "click":
                    # Abortar selección si aún no se completaron 4 puntos
                    if len(clicker.points) < 4:
                        clicker.stop()
                        mode = "view"
                        msg_queue.append("Abortado. Homografía previa conservada.")

    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
