
import cv2
import numpy as np
import os


def nothing(x): pass

def main():

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) 
    cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)
    cv2.createTrackbar("Thresh", "Controls", 100, 255, nothing)
    cv2.createTrackbar("Morph kernel", "Controls", 3, 30, nothing)
    cv2.createTrackbar("Min area", "Controls", 1000, 20000, nothing)
    
    cv2.createTrackbar("ROI X", "Controls", 100, 640, nothing)
    cv2.createTrackbar("ROI Y", "Controls", 100, 480, nothing)
    cv2.createTrackbar("ROI Width", "Controls", 400, 640, nothing)
    cv2.createTrackbar("ROI Height", "Controls", 300, 480, nothing)

    samples_count = {1: 0, 2: 0, 3: 0}

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

        annotated = frame.copy()

        cv2.rectangle(annotated, (roi_x, roi_y), (roi_x+roi_w, roi_y+roi_h), (255, 255, 0), 2)
        cv2.putText(annotated, "ROI - Presiona ESPACIO", (roi_x, roi_y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        roi_annotated = roi.copy()

        largest_contour = None
        largest_area = 0

        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue

            if area > largest_area:
                largest_area = area
                largest_contour = cnt

            x, y, w_cnt, h_cnt = cv2.boundingRect(cnt)
            cv2.rectangle(roi_annotated, (x, y), (x+w_cnt, y+h_cnt), (0, 255, 255), 1)
            cv2.putText(roi_annotated, f"Area: {int(area)}", (x, y-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        if largest_contour is not None:
            x, y, w_cnt, h_cnt = cv2.boundingRect(largest_contour)
            cv2.rectangle(roi_annotated, (x, y), (x+w_cnt, y+h_cnt), (0, 255, 0), 3)
            cv2.drawContours(roi_annotated, [largest_contour], -1, (0, 255, 0), 2)
            cv2.putText(roi_annotated, "PRINCIPAL", (x, y-30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.rectangle(annotated, (roi_x+x, roi_y+y), (roi_x+x+w_cnt, roi_y+y+h_cnt), (0, 255, 0), 2)

        info_text = f"Muestras: Llave({samples_count[1]}) Moneda({samples_count[2]}) Tijera({samples_count[3]})"
        cv2.putText(annotated, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imshow("Full Frame", annotated)
        cv2.imshow("ROI Only", roi_annotated)
        cv2.imshow("Binary", bw)
        cv2.imshow("Morph", bw_m)

        key = cv2.waitKey(1) & 0xFF

        if key == ord(' ') and largest_contour is not None:  
            moments = cv2.moments(largest_contour)
            hu_moments = cv2.HuMoments(moments).flatten()
            
            print("=" * 60)
            print("INVARIANTES DE HU CAPTURADOS:")
            print("Contorno de área:", int(largest_area))
            print()
            print("Para copiar en dataset (formato Python list):")
            hu_str = "[" + ", ".join([f"{val:.8e}" for val in hu_moments]) + "]"
            print(hu_str)
            print()
            print("Para Excel/CSV (separado por comas):")
            csv_str = ", ".join([f"{val:.8e}" for val in hu_moments])
            print(csv_str)
            print()
            print("Recuerda agregar la etiqueta correspondiente:")
            print("1=llave, 2=moneda, 3=tijera")
            print("=" * 60)
            
        elif key == ord('1'):
            samples_count[1] += 1
            print(f"Contador llave: {samples_count[1]}")
        elif key == ord('2'):
            samples_count[2] += 1
            print(f"Contador moneda: {samples_count[2]}")
        elif key == ord('3'):
            samples_count[3] += 1
            print(f"Contador tijera: {samples_count[3]}")
        elif key == 27: 
            break 

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()