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
def dibujar_bbox(frame, bbox, nombre, rol, confianza, autorizado):
    """
    Dibuja un bounding box con información de la persona
    
    Args:
        frame: Frame de OpenCV
        bbox: Diccionario con {x, y, w, h}
        nombre: Nombre de la persona
        rol: Rol de la persona
        confianza: Confianza del reconocimiento (0-100)
        autorizado: Boolean si está autorizado
    
    Returns:
        frame: Frame con el bbox dibujado
    """
    x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
    
    # Color según autorización
    if autorizado:
        color = (0, 255, 0)  # Verde
        color_fondo = (0, 200, 0)
    else:
        color = (0, 0, 255)  # Rojo
        color_fondo = (0, 0, 200)
    
    # Dibujar rectángulo principal
    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
    
    # Esquinas decorativas
    longitud_esquina = 20
    grosor_esquina = 4
    # Esquina superior izquierda
    cv2.line(frame, (x, y), (x + longitud_esquina, y), color, grosor_esquina)
    cv2.line(frame, (x, y), (x, y + longitud_esquina), color, grosor_esquina)
    # Esquina superior derecha
    cv2.line(frame, (x+w, y), (x+w - longitud_esquina, y), color, grosor_esquina)
    cv2.line(frame, (x+w, y), (x+w, y + longitud_esquina), color, grosor_esquina)
    # Esquina inferior izquierda
    cv2.line(frame, (x, y+h), (x + longitud_esquina, y+h), color, grosor_esquina)
    cv2.line(frame, (x, y+h), (x, y+h - longitud_esquina), color, grosor_esquina)
    # Esquina inferior derecha
    cv2.line(frame, (x+w, y+h), (x+w - longitud_esquina, y+h), color, grosor_esquina)
    cv2.line(frame, (x+w, y+h), (x+w, y+h - longitud_esquina), color, grosor_esquina)
    
    # Panel de información
    texto_nombre = f"{nombre}"
    texto_rol = f"{rol}"
    texto_confianza = f"{confianza:.0f}%" if confianza > 0 else "N/A"
    
    # Calcular tamaño del panel
    (w_texto, h_texto), _ = cv2.getTextSize(
        texto_nombre, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
    )
    
    # Fondo del panel
    y_panel = y - 80
    if y_panel < 0:
        y_panel = y + h + 10
    
    cv2.rectangle(frame, 
                 (x, y_panel), 
                 (x + max(w_texto + 20, 200), y_panel + 75), 
                 color_fondo, -1)
    
    # Borde del panel
    cv2.rectangle(frame, 
                 (x, y_panel), 
                 (x + max(w_texto + 20, 200), y_panel + 75), 
                 color, 2)
    
    # Textos del panel
    cv2.putText(frame, texto_nombre, 
               (x + 10, y_panel + 25),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    cv2.putText(frame, texto_rol, 
               (x + 10, y_panel + 50),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1)
    
    cv2.putText(frame, texto_confianza, 
               (x + 10, y_panel + 70),
               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1)
    
    # Icono de estado
    centro_icono = (x + w - 30, y + 30)
    if autorizado:
        # Check verde
        cv2.circle(frame, centro_icono, 20, (0, 255, 0), -1)
        cv2.putText(frame, "✓", 
                   (centro_icono[0] - 10, centro_icono[1] + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    else:
        # X roja
        cv2.circle(frame, centro_icono, 20, (0, 0, 255), -1)
        cv2.line(frame, 
                (centro_icono[0] - 10, centro_icono[1] - 10),
                (centro_icono[0] + 10, centro_icono[1] + 10),
                (255, 255, 255), 3)
        cv2.line(frame, 
                (centro_icono[0] + 10, centro_icono[1] - 10),
                (centro_icono[0] - 10, centro_icono[1] + 10),
                (255, 255, 255), 3)
    
    return frame


# ============================================
# TESTING
# ============================================
# ... (el resto del código de testing que ya tienes)

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