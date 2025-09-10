import cv2
import numpy as np
from joblib import load
import os

def nothing(x): pass

def main():
    print("=== CLASIFICADOR CON MACHINE LEARNING ===")
    
    modelo_filename = 'clasificador_formas.joblib'
    if not os.path.exists(modelo_filename):
        print(f"ERROR: No se encuentra el archivo '{modelo_filename}'")
        print("Ejecuta primero 'entrenador.py' para generar el modelo")
        return
    
    try:
        clasificador = load(modelo_filename)
        print(f"✓ Modelo cargado desde '{modelo_filename}'")
    except Exception as e:
        print(f"ERROR al cargar el modelo: {e}")
        return
    
    etiquetas = {1: "llave", 2: "moneda", 3: "tijera"}
    print("Etiquetas reconocidas:", etiquetas)
    print()
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Thresh", "Controls", 100, 255, nothing)
    cv2.createTrackbar("Morph kernel", "Controls", 3, 30, nothing)
    cv2.createTrackbar("Min area", "Controls", 1000, 20000, nothing)
    cv2.createTrackbar("Confidence thresh", "Controls", 50, 100, nothing) 
    
    cv2.createTrackbar("ROI X", "Controls", 100, 640, nothing)
    cv2.createTrackbar("ROI Y", "Controls", 100, 480, nothing)
    cv2.createTrackbar("ROI Width", "Controls", 400, 640, nothing)
    cv2.createTrackbar("ROI Height", "Controls", 300, 480, nothing)

    print("Controles:")
    print("- Ajusta parámetros con las barras deslizantes")
    print("- 'Confidence thresh': umbral de confianza (0-100%)")
    print("- ESC para salir")
    print()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        roi_x = cv2.getTrackbarPos("ROI X", "Controls")
        roi_y = cv2.getTrackbarPos("ROI Y", "Controls")
        roi_w = cv2.getTrackbarPos("ROI Width", "Controls")
        roi_h = cv2.getTrackbarPos("ROI Height", "Controls")
        
        h, w = frame.shape[:2]
        roi_x = min(roi_x, w-50)
        roi_y = min(roi_y, h-50)
        roi_w = min(roi_w, w-roi_x)
        roi_h = min(roi_h, h-roi_y)
        
        roi = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        t = cv2.getTrackbarPos("Thresh", "Controls")
        _, bw = cv2.threshold(gray, max(1,t), 255, cv2.THRESH_BINARY_INV)

        k = cv2.getTrackbarPos("Morph kernel", "Controls")
        k = max(1, k)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k,k))
        bw_m = cv2.morphologyEx(bw, cv2.MORPH_OPEN, kernel)

        cnts, _ = cv2.findContours(bw_m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = cv2.getTrackbarPos("Min area", "Controls")
        confidence_thresh = cv2.getTrackbarPos("Confidence thresh", "Controls") / 100.0

        annotated = frame.copy()
        
        cv2.rectangle(annotated, (roi_x, roi_y), (roi_x+roi_w, roi_y+roi_h), (255, 255, 0), 2)
        cv2.putText(annotated, "ROI - ML Classifier", (roi_x, roi_y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        roi_annotated = roi.copy()

        detecciones = {"llave": 0, "moneda": 0, "tijera": 0, "desconocido": 0}
        
        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            
            try:
                moments = cv2.moments(cnt)
                hu_moments = cv2.HuMoments(moments).flatten()
                
                if np.any(np.isnan(hu_moments)) or np.any(np.isinf(hu_moments)):
                    continue
                
                hu_moments = hu_moments.reshape(1, -1) 
                prediccion = clasificador.predict(hu_moments)[0]
                probabilidades = clasificador.predict_proba(hu_moments)[0]

                max_confidence = np.max(probabilidades)

                if max_confidence >= confidence_thresh:
                    label_text = etiquetas.get(prediccion, f"Clase_{prediccion}")
                    color = (0, 255, 0) 
                    detecciones[label_text] += 1
                    label = f"{label_text} {max_confidence:.2f}"
                else:
                    label_text = "Desconocido"
                    color = (0, 0, 255)  
                    detecciones["desconocido"] += 1
                    label = f"{label_text} {max_confidence:.2f}"
                
                x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
                cv2.rectangle(roi_annotated, (x, y), (x+w_cnt, y+h_cnt), color, 2)
                cv2.drawContours(roi_annotated, [cnt], -1, color, 2)
                cv2.putText(roi_annotated, label, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                cv2.rectangle(annotated, (roi_x+x, roi_y+y), (roi_x+x+w_cnt, roi_y+y+h_cnt), color, 2)
                cv2.putText(annotated, label, (roi_x+x, roi_y+y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                if max_confidence >= confidence_thresh:
                    prob_text = []
                    for i, prob in enumerate(probabilidades):
                        etiq = etiquetas.get(i+1, f"C{i+1}")
                        prob_text.append(f"{etiq}:{prob:.2f}")
                    prob_str = " ".join(prob_text)
                    cv2.putText(roi_annotated, prob_str, (x, y+h_cnt+15), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
                
            except Exception as e:
                print(f"Error procesando contorno: {e}")
                continue

        stats_text = f"Detectados: L:{detecciones['llave']} M:{detecciones['moneda']} V:{detecciones['tijera']} ?:{detecciones['desconocido']}"
        cv2.putText(annotated, stats_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        conf_text = f"Confianza min: {confidence_thresh:.0%}"
        cv2.putText(annotated, conf_text, (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("ML Classifier", annotated)
        cv2.imshow("ROI Only", roi_annotated)
        cv2.imshow("Binary", bw)
        cv2.imshow("Morph", bw_m)

        key = cv2.waitKey(1) & 0xFF
        if key == 27: 
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Clasificador terminado.")

if __name__ == "__main__":
    main()