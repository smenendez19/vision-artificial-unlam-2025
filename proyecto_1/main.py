import os
from pathlib import Path

import cv2
import numpy as np

# Carpeta de templates relativa a este archivo (proyecto_1/templates)
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


def load_template_contours(dir_path):
    dir_path = Path(dir_path)
    templates = []
    if not dir_path.is_dir():
        return templates
    for fname in os.listdir(dir_path):
        if not fname.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        name = os.path.splitext(fname)[0]
        img = cv2.imread(str(dir_path / fname), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        # No re-aplicar threshold: normalizamos cualquier valor >0 a 255.
        th = (img > 0).astype("uint8") * 255
        cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            continue
        cnt = max(cnts, key=cv2.contourArea)
        templates.append((name, cnt))
        print("Cargada plantilla:", name)
    return templates


def nothing(_):
    pass


def build_panel(full_bgr, roi_bgr, bw, bw_m):
    h, w = full_bgr.shape[:2]
    target = (w, h)

    def ensure_bgr(img):
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR) if len(img.shape) == 2 else img

    roi_bgr = cv2.resize(ensure_bgr(roi_bgr), target, interpolation=cv2.INTER_AREA)
    bw_bgr = cv2.resize(ensure_bgr(bw), target, interpolation=cv2.INTER_NEAREST)
    bw_m_bgr = cv2.resize(ensure_bgr(bw_m), target, interpolation=cv2.INTER_NEAREST)

    panel = np.zeros((h * 2, w * 2, 3), dtype=np.uint8)
    panel[0:h, 0:w] = full_bgr
    panel[0:h, w:2 * w] = roi_bgr
    panel[h:2 * h, 0:w] = bw_bgr
    panel[h:2 * h, w:2 * w] = bw_m_bgr

    cv2.putText(panel, "Full", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(panel, "ROI", (w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(panel, "Binary", (10, h + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(panel, "Morph", (w + 10, h + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    return panel


def main():
    templates = load_template_contours(TEMPLATES_DIR)
    if not templates:
        print("No hay plantillas encontradas en 'templates/'")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("No se pudo abrir la cámara.")
        return

    cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Panel", cv2.WINDOW_NORMAL)

    cv2.createTrackbar("Thresh", "Controls", 100, 255, nothing)
    cv2.createTrackbar("Morph kernel", "Controls", 3, 50, nothing)
    cv2.createTrackbar("Min area", "Controls", 1000, 50000, nothing)
    cv2.createTrackbar("Match thresh", "Controls", 30, 500, nothing)  # *1000
    cv2.createTrackbar("ROI X", "Controls", 100, 640, nothing)
    cv2.createTrackbar("ROI Y", "Controls", 100, 480, nothing)
    cv2.createTrackbar("ROI Width", "Controls", 400, 640, nothing)
    cv2.createTrackbar("ROI Height", "Controls", 300, 480, nothing)

    print("Presiona Q o ESC para salir")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            roi_x = cv2.getTrackbarPos("ROI X", "Controls")
            roi_y = cv2.getTrackbarPos("ROI Y", "Controls")
            roi_w = cv2.getTrackbarPos("ROI Width", "Controls")
            roi_h = cv2.getTrackbarPos("ROI Height", "Controls")

            h, w = frame.shape[:2]
            roi_x = min(roi_x, w - 50)
            roi_y = min(roi_y, h - 50)
            roi_w = min(roi_w, w - roi_x)
            roi_h = min(roi_h, h - roi_y)

            roi = frame[roi_y: roi_y + roi_h, roi_x: roi_x + roi_w]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            t = cv2.getTrackbarPos("Thresh", "Controls")
            _, bw = cv2.threshold(gray, max(1, t), 255, cv2.THRESH_BINARY_INV)

            k = cv2.getTrackbarPos("Morph kernel", "Controls")
            k = max(1, k | 1)  # asegurar impar
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
            bw_m = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)

            cnts, _ = cv2.findContours(bw_m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            min_area = cv2.getTrackbarPos("Min area", "Controls")
            match_thresh_val = cv2.getTrackbarPos("Match thresh", "Controls") / 1000.0

            annotated = frame.copy()
            cv2.rectangle(annotated, (roi_x, roi_y), (roi_x + roi_w, roi_y + roi_h), (255, 255, 0), 2)

            roi_annotated = roi.copy()
            for cnt in cnts:
                area = cv2.contourArea(cnt)
                if area < min_area:
                    continue
                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.01 * peri, True)
                best_name = None
                best_score = float("inf")
                for name, tpl in templates:
                    score = cv2.matchShapes(cnt, tpl, cv2.CONTOURS_MATCH_I1, 0.0)
                    if score < best_score:
                        best_score = score
                        best_name = name
                x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
                if best_score < match_thresh_val:
                    color = (0, 255, 0)
                    label = f"{best_name} {best_score:.3f}"
                else:
                    color = (0, 0, 255)
                    label = f"? {best_score:.3f}"
                cv2.rectangle(roi_annotated, (x, y), (x + w_cnt, y + h_cnt), color, 2)
                cv2.drawContours(roi_annotated, [approx], -1, color, 1)
                cv2.rectangle(annotated, (roi_x + x, roi_y + y), (roi_x + x + w_cnt, roi_y + y + h_cnt), color, 2)
                cv2.putText(annotated, label, (roi_x + x, roi_y + y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                cv2.putText(roi_annotated, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            panel = build_panel(annotated, roi_annotated, bw, bw_m)
            cv2.imshow("Panel", panel)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), 27):  # q o ESC
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
