import os
from datetime import datetime

import cv2


def evaluar_calidad_foto(frame, bbox):
    """
    Evalúa la calidad de una foto de rostro

    Returns:
        tuple: (puntuacion, mensaje)
    """
    x, y, w, h = bbox

    # Extraer región del rostro
    rostro = frame[y: y + h, x: x + w]

    # 1. Verificar tamaño (mínimo 150x150)
    if w < 150 or h < 150:
        return 0, "Rostro muy pequeño - acércate más"

    if w > 500 or h > 500:
        return 0, "Rostro muy grande - aléjate un poco"

    # 2. Verificar brillo
    gray = cv2.cvtColor(rostro, cv2.COLOR_BGR2GRAY)
    brillo = gray.mean()

    if brillo < 60:
        return 0, "Muy oscuro - mejora la iluminación"
    if brillo > 200:
        return 0, "Muy brillante - reduce la luz"

    # 3. Verificar nitidez (desenfoque)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    nitidez = laplacian.var()

    if nitidez < 100:
        return 0, "Desenfocado - mantén quieta la cámara"

    # 4. Verificar posición (centrado)
    frame_h, frame_w = frame.shape[:2]
    centro_x = x + w / 2
    centro_y = y + h / 2

    if abs(centro_x - frame_w / 2) > frame_w / 4:
        return 0, "No centrado horizontalmente"

    if abs(centro_y - frame_h / 2) > frame_h / 4:
        return 0, "No centrado verticalmente"

    # Calcular puntuación (0-100)
    puntuacion_brillo = max(0, 100 - abs(brillo - 130))
    puntuacion_nitidez = min(100, (nitidez / 500) * 100)
    puntuacion_tamano = 100 if 200 <= w <= 400 else 50

    puntuacion = (puntuacion_brillo + puntuacion_nitidez + puntuacion_tamano) / 3

    mensaje = "Calidad: "
    if puntuacion >= 80:
        mensaje += "EXCELENTE ✓✓✓"
    elif puntuacion >= 60:
        mensaje += "BUENA ✓✓"
    elif puntuacion >= 40:
        mensaje += "ACEPTABLE ✓"
    else:
        mensaje += "REGULAR"

    return puntuacion, mensaje


def capturar_dataset_persona():
    """Captura multiples fotos de una persona para dataset"""

    print("\n" + "=" * 70)
    print("📸 CAPTURA DE DATASET DE ALTA CALIDAD")
    print("=" * 70 + "\n")

    # Elegir categoría
    print("Categorías:")
    print("  1. Empleado")
    print("  2. VIP")
    print("  3. Visitante")

    while True:
        try:
            opcion = int(input("\nElegir categoría (1-3): "))
            if 1 <= opcion <= 3:
                break
        except ValueError:
            pass
        print("❌ Opción inválida")

    categorias = {1: "empleados", 2: "vip", 3: "visitantes"}
    categoria = categorias[opcion]

    # Pedir nombre
    while True:
        nombre = input("\nNombre completo (sin números): ").strip()
        if nombre and not any(c.isdigit() for c in nombre):
            break
        print("❌ Nombre inválido (no uses números)")

    # Crear carpeta para la persona
    carpeta_destino = os.path.join("..", "backend", "database", categoria, nombre)
    os.makedirs(carpeta_destino, exist_ok=True)

    print(f"\n✓ Carpeta creada: {carpeta_destino}")
    print("\n📷 Se capturarán 10 fotos de alta calidad")
    print("\nInstrucciones:")
    print("  • Manten el rostro de frente")
    print("  • Buena iluminacion frontal")
    print("  • No muevas la cabeza bruscamente")
    print("  • Variaciones: con/sin sonrisa, ligeros angulos")
    print("\nPresiona ESPACIO cuando veas ✓✓✓ (calidad EXCELENTE)")
    print("Presiona Q para cancelar\n")

    input("Presiona ENTER para comenzar...")

    # Iniciar cámara
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return

    # Cargar detector de rostros
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    fotos_capturadas = 0
    objetivo = 10

    print(f"\n🎬 Cámara iniciada - Capturando {objetivo} fotos...\n")

    while fotos_capturadas < objetivo:
        ret, frame = cap.read()

        if not ret:
            print("❌ Error capturando frame")
            break

        # Detectar rostros
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        mensaje_calidad = "No se detecta rostro"
        color_mensaje = (0, 0, 255)
        puntuacion = 0
        bbox_valido = None

        # Evaluar calidad si hay rostro
        if len(faces) > 0:
            # Usar el rostro más grande
            bbox = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = bbox

            puntuacion, mensaje_calidad = evaluar_calidad_foto(frame, bbox)
            bbox_valido = bbox

            # Color según calidad
            if puntuacion >= 80:
                color_bbox = (0, 255, 0)  # Verde
                color_mensaje = (0, 255, 0)
            elif puntuacion >= 60:
                color_bbox = (0, 255, 255)  # Amarillo
                color_mensaje = (0, 255, 255)
            else:
                color_bbox = (0, 165, 255)  # Naranja
                color_mensaje = (0, 165, 255)

            # Dibujar rectángulo
            cv2.rectangle(frame, (x, y), (x + w, y + h), color_bbox, 3)

            # Indicador de calidad
            cv2.putText(frame, f"Calidad: {puntuacion:.0f}/100", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bbox, 2)

        # Información en pantalla
        cv2.putText(frame, f"Fotos: {fotos_capturadas}/{objetivo}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        cv2.putText(frame, mensaje_calidad, (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color_mensaje, 2)

        if puntuacion >= 50:
            cv2.putText(frame, "ESPACIO para capturar", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Captura de Dataset - FACEGUARD", frame)

        # Controles
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q") or key == ord("Q"):
            print("\n  Captura cancelada")
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

            rostro = frame[y_min:y_max, x_min:x_max]

            # Guardar
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{nombre}_{timestamp}.jpg"
            filepath = os.path.join(carpeta_destino, filename)

            cv2.imwrite(filepath, rostro)
            fotos_capturadas += 1

            print(f"  ✓ Foto {fotos_capturadas}/{objetivo} capturada - Calidad: {puntuacion:.0f}/100")

            # Pausa breve
            cv2.waitKey(500)

    cap.release()
    cv2.destroyAllWindows()

    if fotos_capturadas == objetivo:
        print("\n✅ Dataset completo!")
        print(f"📁 {fotos_capturadas} fotos guardadas en: {carpeta_destino}")
        print("\n💡 Ahora ejecuta el sistema de reconocimiento")
    else:
        print(f"\n  Solo se capturaron {fotos_capturadas}/{objetivo} fotos")


if __name__ == "__main__":
    try:
        capturar_dataset_persona()
    except KeyboardInterrupt:
        print("\n\n  Interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
