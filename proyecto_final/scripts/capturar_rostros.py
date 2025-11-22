"""
Script para capturar rostros y registrar personas en el sistema
"""
import cv2
import os
import sys

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config import Config


def capturar_rostros(nombre, rol, num_fotos=3):
    """
    Captura fotos de una persona para registrarla en el sistema
    
    Args:
        nombre (str): Nombre completo de la persona
        rol (str): Rol (empleados, vip, visitantes)
        num_fotos (int): Cantidad de fotos a capturar
    """
    
    # Validar rol
    if rol not in Config.ROLES:
        print(f"❌ Rol inválido. Debe ser uno de: {', '.join(Config.ROLES.keys())}")
        return False
    
    # Crear carpeta si no existe
    carpeta_destino = os.path.join(Config.DATABASE_DIR, rol)
    os.makedirs(carpeta_destino, exist_ok=True)
    
    # Nombre de archivo base
    nombre_archivo = nombre.lower().replace(' ', '_')
    
    # Abrir cámara
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara")
        return False
    
    print("\n" + "="*60)
    print(f"📸 CAPTURA DE ROSTROS - {nombre}")
    print("="*60)
    print(f"\n👤 Persona: {nombre}")
    print(f"🏷️  Rol: {Config.ROLES[rol]['nombre']}")
    print(f"📁 Destino: {carpeta_destino}")
    print(f"📷 Fotos a capturar: {num_fotos}")
    print("\n📌 INSTRUCCIONES:")
    print("  • Mira a la cámara de frente")
    print("  • Asegúrate de tener buena iluminación")
    print("  • Presiona ESPACIO para capturar cada foto")
    print("  • Presiona ESC para cancelar")
    print("\n" + "="*60 + "\n")
    
    fotos_capturadas = 0
    
    # Cargar detector de rostros para ayuda visual
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    while fotos_capturadas < num_fotos:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Error capturando frame")
            break
        
        # Detectar rostros para guía visual
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Dibujar rectángulos alrededor de los rostros
        for (x, y, w, h) in faces:
            color = (0, 255, 0) if len(faces) == 1 else (0, 165, 255)
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
            
            # Texto de guía
            if len(faces) == 1:
                cv2.putText(frame, "Perfecto! Presiona ESPACIO", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "Debe haber solo 1 persona", (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        
        # Información en pantalla
        info_text = f"Fotos: {fotos_capturadas}/{num_fotos}"
        cv2.putText(frame, info_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        cv2.putText(frame, "ESPACIO: Capturar | ESC: Salir", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Indicador de rostros detectados
        rostros_text = f"Rostros detectados: {len(faces)}"
        color_texto = (0, 255, 0) if len(faces) == 1 else (0, 0, 255)
        cv2.putText(frame, rostros_text, (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color_texto, 2)
        
        # Mostrar frame
        cv2.imshow(f'Capturando: {nombre}', frame)
        
        # Controles
        tecla = cv2.waitKey(1) & 0xFF
        
        if tecla == ord(' '):  # Espacio
            if len(faces) == 1:
                # Guardar foto
                nombre_completo = f"{nombre_archivo}_{fotos_capturadas + 1}.jpg"
                ruta_completa = os.path.join(carpeta_destino, nombre_completo)
                
                cv2.imwrite(ruta_completa, frame)
                print(f"✓ Foto {fotos_capturadas + 1}/{num_fotos} guardada: {nombre_completo}")
                
                fotos_capturadas += 1
                
                # Feedback visual
                frame_feedback = frame.copy()
                cv2.putText(frame_feedback, "CAPTURADO!", 
                           (frame.shape[1]//2 - 100, frame.shape[0]//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                cv2.imshow(f'Capturando: {nombre}', frame_feedback)
                cv2.waitKey(500)  # Mostrar por 500ms
            else:
                print("⚠️  Debe haber exactamente 1 rostro visible")
        
        elif tecla == 27:  # ESC
            print("\n❌ Captura cancelada")
            cap.release()
            cv2.destroyAllWindows()
            return False
    
    # Finalizar
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "="*60)
    print(f"✅ Registro completado!")
    print(f"   • Persona: {nombre}")
    print(f"   • Rol: {Config.ROLES[rol]['nombre']}")
    print(f"   • Fotos capturadas: {fotos_capturadas}")
    print(f"   • Ubicación: {carpeta_destino}")
    print("="*60 + "\n")
    
    return True


def menu_principal():
    """Menú interactivo para registrar personas"""
    
    Config.init_app()
    
    print("\n" + "="*60)
    print("🔐 FACEGUARD - Registro de Personas")
    print("="*60)
    
    while True:
        print("\n📋 MENÚ:")
        print("  1. Registrar nuevo Empleado")
        print("  2. Registrar nuevo VIP")
        print("  3. Registrar nuevo Visitante")
        print("  4. Ver personas registradas")
        print("  5. Salir")
        print()
        
        opcion = input("Selecciona una opción (1-5): ").strip()
        
        if opcion == '1':
            registrar_persona('empleados')
        elif opcion == '2':
            registrar_persona('vip')
        elif opcion == '3':
            registrar_persona('visitantes')
        elif opcion == '4':
            mostrar_personas_registradas()
        elif opcion == '5':
            print("\n👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida")


def registrar_persona(rol):
    """Proceso de registro de una persona"""
    print(f"\n📝 Registrando {Config.ROLES[rol]['nombre']}")
    print("-" * 40)
    
    nombre = input("Nombre completo: ").strip()
    
    if not nombre:
        print("❌ Nombre no puede estar vacío")
        return
    
    print(f"\n¿Capturar fotos de {nombre}?")
    confirmar = input("(s/n): ").strip().lower()
    
    if confirmar == 's':
        num_fotos = input("¿Cuántas fotos capturar? (recomendado: 3): ").strip()
        try:
            num_fotos = int(num_fotos) if num_fotos else 3
            num_fotos = max(1, min(num_fotos, 10))  # Entre 1 y 10
        except:
            num_fotos = 3
        
        capturar_rostros(nombre, rol, num_fotos)
    else:
        print("❌ Registro cancelado")


def mostrar_personas_registradas():
    """Muestra todas las personas registradas"""
    print("\n" + "="*60)
    print("👥 PERSONAS REGISTRADAS")
    print("="*60)
    
    total = 0
    
    for rol, info in Config.ROLES.items():
        carpeta = os.path.join(Config.DATABASE_DIR, rol)
        
        if os.path.exists(carpeta):
            archivos = [f for f in os.listdir(carpeta) if f.endswith(('.jpg', '.jpeg', '.png'))]
            
            if archivos:
                print(f"\n📁 {info['nombre']} ({len(archivos)}):")
                for archivo in sorted(archivos):
                    nombre = archivo.split('.')[0].replace('_', ' ').title()
                    print(f"  • {nombre}")
                total += len(archivos)
    
    print("\n" + "="*60)
    print(f"Total de personas: {total}")
    print("="*60)


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrumpido. ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error: {e}")