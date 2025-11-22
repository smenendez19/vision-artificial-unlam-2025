"""
Script de prueba rápida del sistema
Verifica que todo esté instalado y configurado correctamente
"""
import sys
import os

print("="*70)
print("🧪 TEST DEL SISTEMA DE RECONOCIMIENTO FACIAL")
print("="*70)
print()

# Test 1: Verificar Python
print("1️⃣ Verificando versión de Python...")
python_version = sys.version_info
if python_version.major >= 3 and python_version.minor >= 8:
    print(f"   ✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
else:
    print(f"   ❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} - Se requiere 3.8+")
    sys.exit(1)

# Test 2: Verificar módulos
print("\n2️⃣ Verificando módulos instalados...")
modulos = {
    'cv2': 'opencv-python',
    'deepface': 'deepface',
    'flask': 'flask',
    'numpy': 'numpy',
    'pandas': 'pandas'
}

faltantes = []
for modulo, nombre_pip in modulos.items():
    try:
        __import__(modulo)
        print(f"   ✅ {modulo}")
    except ImportError:
        print(f"   ❌ {modulo} - Instalar con: pip install {nombre_pip}")
        faltantes.append(nombre_pip)

if faltantes:
    print(f"\n❌ Faltan módulos. Instala con:")
    print(f"   pip install {' '.join(faltantes)}")
    sys.exit(1)

# Test 3: Verificar estructura de carpetas
print("\n3️⃣ Verificando estructura de carpetas...")
carpetas_necesarias = [
    'backend/database',
    'backend/database/empleados',
    'backend/database/vip',
    'backend/database/visitantes',
    'backend/logs',
    'backend/temp'
]

for carpeta in carpetas_necesarias:
    if os.path.exists(carpeta):
        print(f"   ✅ {carpeta}")
    else:
        print(f"   ⚠️  {carpeta} - Será creada automáticamente")

# Test 4: Verificar personas registradas
print("\n4️⃣ Verificando personas registradas...")
total_personas = 0
for rol in ['empleados', 'vip', 'visitantes']:
    carpeta = f'backend/database/{rol}'
    if os.path.exists(carpeta):
        archivos = [f for f in os.listdir(carpeta) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if archivos:
            print(f"   ✅ {rol}: {len(archivos)} personas")
            total_personas += len(archivos)
        else:
            print(f"   ⚠️  {rol}: 0 personas (vacío)")

if total_personas == 0:
    print("\n⚠️  No hay personas registradas.")
    print("   Registra personas con: python scripts/capturar_rostros.py")
else:
    print(f"\n✅ Total: {total_personas} personas registradas")

# Test 5: Verificar cámara
print("\n5️⃣ Verificando cámara...")
try:
    import cv2
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            altura, ancho = frame.shape[:2]
            print(f"   ✅ Cámara detectada ({ancho}x{altura})")
        else:
            print("   ❌ No se pudo capturar frame de la cámara")
        cap.release()
    else:
        print("   ❌ No se pudo abrir la cámara")
        print("   Verifica que:")
        print("     • La cámara esté conectada")
        print("     • No esté siendo usada por otra aplicación")
        print("     • Tienes permisos para acceder a la cámara")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Test rápido de DeepFace
print("\n6️⃣ Probando DeepFace...")
try:
    from deepface import DeepFace
    print("   ✅ DeepFace importado correctamente")
    
    # Test de modelos disponibles
    modelos = ['VGG-Face', 'Facenet', 'ArcFace', 'Dlib', 'OpenFace']
    print("   ℹ️  Modelos disponibles:", ", ".join(modelos))
    
except Exception as e:
    print(f"   ❌ Error con DeepFace: {e}")

# Test 7: Verificar archivos del proyecto
print("\n7️⃣ Verificando archivos del proyecto...")
archivos_principales = [
    'backend/app.py',
    'backend/app_simple.py',
    'backend/reconocimiento.py',
    'backend/config.py',
    'backend/utils.py',
    'scripts/capturar_rostros.py'
]

for archivo in archivos_principales:
    if os.path.exists(archivo):
        print(f"   ✅ {archivo}")
    else:
        print(f"   ❌ {archivo} - ¡Falta este archivo!")

# Resumen final
print("\n" + "="*70)
print("📋 RESUMEN")
print("="*70)

if faltantes:
    print("\n❌ Sistema NO está listo")
    print(f"   Instala módulos faltantes: pip install {' '.join(faltantes)}")
elif total_personas == 0:
    print("\n⚠️  Sistema casi listo")
    print("   Falta registrar personas:")
    print("   → python scripts/capturar_rostros.py")
else:
    print("\n✅ Sistema listo para usar!")
    print("\nOpciones para ejecutar:")
    print("   1. Versión simple (solo OpenCV):")
    print("      → python backend/app_simple.py")
    print()
    print("   2. Versión completa (con WebSockets):")
    print("      → python backend/app.py")

print("\n" + "="*70)
print()