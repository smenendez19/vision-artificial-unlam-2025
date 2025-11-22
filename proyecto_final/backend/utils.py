"""
Utilidades para el sistema de reconocimiento facial
"""
import os
import cv2
import uuid
from datetime import datetime
from config import Config


def extraer_nombre_archivo(ruta_archivo):
    """
    Extrae el nombre limpio de una persona desde el nombre del archivo
    Maneja casos con timestamps: Carlos_20251121_205414 -> Carlos
    
    Args:
        ruta_archivo (str): Ruta completa del archivo
    
    Returns:
        str: Nombre de la persona sin timestamp
    """
    # Obtener solo el nombre del archivo sin extensión
    nombre_archivo = os.path.splitext(os.path.basename(ruta_archivo))[0]
    
    # NUEVO: Si el nombre contiene fechas/timestamps, extraer solo el nombre
    partes = nombre_archivo.split('_')
    
    # Buscar la primera parte que NO sea un número (timestamp)
    nombre_limpio = []
    for parte in partes:
        # Si es un número de 8 dígitos o más, probablemente es un timestamp
        if parte.isdigit() and len(parte) >= 8:
            break  # Detener aquí, lo que sigue es timestamp
        nombre_limpio.append(parte)
    
    # Unir las partes del nombre
    if nombre_limpio:
        nombre = ' '.join(nombre_limpio).title()
    else:
        # Fallback: usar solo la primera parte
        nombre = partes[0].title()
    
    return nombre


def extraer_rol_ruta(ruta_archivo):
    """
    Extrae el rol desde la ruta del archivo
    
    Args:
        ruta_archivo (str): Ruta completa (ej: 'database/vip/carlos.jpg')
    
    Returns:
        str: Nombre del rol
    """
    partes = ruta_archivo.split(os.sep)
    
    # El rol está en el penúltimo segmento
    if len(partes) >= 2:
        categoria = partes[-2]
        
        # Mapear a nombre legible
        if categoria in Config.ROLES:
            return Config.ROLES[categoria]['nombre']
    
    return 'Desconocido'


def obtener_nivel_acceso(ruta_archivo):
    """
    Obtiene el nivel de acceso desde la ruta del archivo
    
    Args:
        ruta_archivo (str): Ruta completa
    
    Returns:
        int: Nivel de acceso
    """
    partes = ruta_archivo.split(os.sep)
    
    if len(partes) >= 2:
        categoria = partes[-2]
        
        if categoria in Config.ROLES:
            return Config.ROLES[categoria]['nivel_acceso']
    
    return 0


def debe_generar_alerta(ruta_archivo, es_desconocido):
    """
    Determina si debe generar alerta para esta detección
    
    Args:
        ruta_archivo (str): Ruta del archivo
        es_desconocido (bool): Si la persona es desconocida
    
    Returns:
        tuple: (debe_generar, tipo_alerta)
    """
    if es_desconocido:
        return True, 'critico'
    
    partes = ruta_archivo.split(os.sep)
    
    if len(partes) >= 2:
        categoria = partes[-2]
        
        if categoria in Config.ROLES:
            rol_info = Config.ROLES[categoria]
            genera = rol_info.get('genera_alerta', False)
            tipo = rol_info.get('tipo_alerta', 'bajo')
            return genera, tipo
    
    return False, None


def guardar_frame_temporal(frame, prefijo='frame'):
    """
    Guarda un frame temporalmente
    
    Args:
        frame: Frame de OpenCV
        prefijo (str): Prefijo del nombre
    
    Returns:
        str: Ruta del archivo temporal
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{prefijo}_{timestamp}.jpg"
    filepath = os.path.join(Config.TEMP_DIR, filename)
    
    cv2.imwrite(filepath, frame)
    
    return filepath


def limpiar_archivos_temporales(max_edad_minutos=10):
    """
    Limpia archivos temporales antiguos
    
    Args:
        max_edad_minutos (int): Edad máxima en minutos
    """
    import time
    
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
        print(f"🧹 Limpiados {archivos_eliminados} archivos temporales")


def generar_id_deteccion():
    """
    Genera un ID único para una detección
    Este ID es solo para tracking interno
    
    Returns:
        str: ID único corto
    """
    return str(uuid.uuid4())[:8]


def normalizar_nombre_archivo(nombre):
    """
    Normaliza un nombre para usar como nombre de archivo
    
    Args:
        nombre (str): Nombre original
    
    Returns:
        str: Nombre normalizado
    """
    # Convertir a minúsculas y reemplazar espacios
    nombre = nombre.lower().replace(' ', '_')
    
    # Remover caracteres especiales
    caracteres_validos = 'abcdefghijklmnopqrstuvwxyz0123456789_'
    nombre = ''.join(c for c in nombre if c in caracteres_validos)
    
    return nombre


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("🧪 Probando utilidades...\n")
    
    # Test 1: Extraer nombre con timestamp
    rutas_test = [
        'database/vip/Carlos_20251121_205414_531753.jpg',
        'database/empleados/Maria_Lopez_20251121_120000.jpg',
        'database/visitantes/Juan_20251121_153045.jpg',
        'database/vip/carlos.jpg'
    ]
    
    print("📝 Test: Extraer nombres")
    for ruta in rutas_test:
        nombre = extraer_nombre_archivo(ruta)
        print(f"  {os.path.basename(ruta)} → {nombre}")
    
    print("\n✓ Tests completados")