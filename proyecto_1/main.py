# guardar como detect_shape_realtime_roi.py
import cv2
import numpy as np
import os
TEMPLATES_DIR = "./templates/" 
def load_template_contours(dir_path):
    templates = []
    for fname in os.listdir(dir_path):
        if not fname.lower().endswith(('.png','.jpg','.jpeg')):
            continue
        name = os.path.splitext(fname)[0]
        img = cv2.imread(os.path.join(dir_path, fname), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        _, th = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            continue
        cnt = max(cnts, key=cv2.contourArea)
        templates.append((name, cnt))
        print("Cargada plantilla:", name)
    return templates

def nothing(x): pass

def main():
    templates = load_template_contours(TEMPLATES_DIR)
    if not templates:
        print("No templates found. Put reference images into 'templates/'")
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Thresh", "Controls", 100, 255, nothing)
    cv2.createTrackbar("Morph kernel", "Controls", 3, 30, nothing)
    cv2.createTrackbar("Min area", "Controls", 1000, 20000, nothing)
    cv2.createTrackbar("Match thresh (lower better)", "Controls", 30, 500, nothing)
    
    # ✅ NUEVAS BARRAS PARA ROI
    cv2.createTrackbar("ROI X", "Controls", 100, 640, nothing)
    cv2.createTrackbar("ROI Y", "Controls", 100, 480, nothing)
    cv2.createTrackbar("ROI Width", "Controls", 400, 640, nothing)
    cv2.createTrackbar("ROI Height", "Controls", 300, 480, nothing)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # ✅ AQUÍ SE DEFINE LA ROI
        roi_x = cv2.getTrackbarPos("ROI X", "Controls")
        roi_y = cv2.getTrackbarPos("ROI Y", "Controls")
        roi_w = cv2.getTrackbarPos("ROI Width", "Controls")
        roi_h = cv2.getTrackbarPos("ROI Height", "Controls")
        
        # Asegurar que ROI esté dentro de los límites
        h, w = frame.shape[:2]
        roi_x = min(roi_x, w-50)
        roi_y = min(roi_y, h-50)
        roi_w = min(roi_w, w-roi_x)
        roi_h = min(roi_h, h-roi_y)
        
        # ✅ RECORTAR LA REGIÓN DE INTERÉS
        roi = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        
        # ✅ PROCESAR SOLO LA ROI (no todo el frame)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        t = cv2.getTrackbarPos("Thresh", "Controls")
        _, bw = cv2.threshold(gray, max(1,t), 255, cv2.THRESH_BINARY_INV)

        k = cv2.getTrackbarPos("Morph kernel", "Controls")
        k = max(1, k)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k,k))
        bw_m = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)

        cnts, _ = cv2.findContours(bw_m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = cv2.getTrackbarPos("Min area", "Controls")
        match_thresh_val = cv2.getTrackbarPos("Match thresh (lower better)", "Controls") / 1000.0

        # ✅ CREAR IMAGEN COMPLETA PARA MOSTRAR
        annotated = frame.copy()
        
        # ✅ DIBUJAR RECTÁNGULO DE LA ROI
        cv2.rectangle(annotated, (roi_x, roi_y), (roi_x+roi_w, roi_y+roi_h), (255, 255, 0), 2)
        cv2.putText(annotated, "ROI", (roi_x, roi_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # Procesar contornos dentro de la ROI
        roi_annotated = roi.copy()
        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.01 * peri, True)

            best_name = None
            best_score = float('inf')
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
                label = f"Desconocido {best_score:.3f}"
            
            # Dibujar en la ROI
            cv2.rectangle(roi_annotated, (x, y), (x+w_cnt, y+h_cnt), color, 2)
            cv2.drawContours(roi_annotated, [approx], -1, color, 1)
            cv2.putText(roi_annotated, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # ✅ TAMBIÉN DIBUJAR EN LA IMAGEN COMPLETA (ajustando coordenadas)
            cv2.rectangle(annotated, (roi_x+x, roi_y+y), (roi_x+x+w_cnt, roi_y+y+h_cnt), color, 2)
            cv2.putText(annotated, label, (roi_x+x, roi_y+y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Mostrar ventanas
        cv2.imshow("Full Frame", annotated)
        cv2.imshow("ROI Only", roi_annotated)
        cv2.imshow("Binary", bw)
        cv2.imshow("Morph", bw_m)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()