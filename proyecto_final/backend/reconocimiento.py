"""
Sistema de Reconocimiento Facial usando DeepFace
"""
import cv2
import os
import logging
from datetime import datetime
from deepface import DeepFace
from config import Config
from utils import (
    extraer_nombre_archivo,
    extraer_rol_ruta,
    obtener_nivel_acceso,
    debe_generar_alerta,
    guardar_frame_temporal,
    limpiar_archivos_temporales,
    generar_id_deteccion
)

# Configurar logging
logging.basicConfig(level=Config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class SistemaReconocimiento:
    """
    Sistema de reconocimiento facial con DeepFace
    """
    
    def __init__(self):
        """Inicializar el sistema"""
        logger.info("🚀 Inicializando Sistema de Reconocimiento Facial...")
        
        self.db_path = Config.DATABASE_DIR
        self.model_name = Config.MODELO_FACIAL
        self.detector_backend = Config.DETECTOR_BACKEND
        self.umbral_confianza = Config.UMBRAL_CONFIANZA
        
        # Cámara
        self.camera = None
        self.camera_activa = False
        
        # Cache de roles
        self.roles_cache = self._cargar_roles()
        
        # Estadísticas
        self.total_detecciones = 0
        self.detecciones_exitosas = 0
        self.alertas_generadas = 0
        
        logger.info(f"✓ Modelo: {self.model_name}")
        logger.info(f"✓ Detector: {self.detector_backend}")
        logger.info(f"✓ Base de datos: {self.db_path}")
        logger.info(f"✓ Personas registradas: {len(self.roles_cache)}")
    
    def _cargar_roles(self):
        """
        Carga información de roles desde la estructura de carpetas
        
        Returns:
            dict: Diccionario con información de cada persona
        """
        roles = {}
        
        for rol, info in Config.ROLES.items():
            carpeta = os.path.join(self.db_path, rol)
            if os.path.exists(carpeta):
                for archivo in os.listdir(carpeta):
                    if archivo.endswith(('.jpg', '.jpeg', '.png')):
                        nombre = extraer_nombre_archivo(archivo)
                        ruta_completa = os.path.join(carpeta, archivo)
                        
                        roles[nombre] = {
                            'rol': info['nombre'],
                            'nivel_acceso': info['nivel_acceso'],
                            'ruta': ruta_completa,
                            'categoria': rol
                        }
        
        logger.info(f"✓ Cargados {len(roles)} perfiles")
        return roles
    
    def iniciar_camara(self, camera_index=None):
        """
        Inicia la cámara
        
        Args:
            camera_index (int): Índice de la cámara
        
        Returns:
            bool: True si se inició correctamente
        """
        if camera_index is None:
            camera_index = Config.CAMERA_INDEX
        
        try:
            self.camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            
            if not self.camera.isOpened():
                logger.error("❌ No se pudo abrir la cámara")
                return False
            
            # Configurar resolución
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
            
            self.camera_activa = True
            logger.info("✓ Cámara iniciada correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error iniciando cámara: {e}")
            return False
    
    def detener_camara(self):
        """Detiene la cámara"""
        if self.camera:
            self.camera.release()
            self.camera_activa = False
            logger.info("✓ Cámara detenida")
    
    def capturar_frame(self):
        """
        Captura un frame de la cámara
        
        Returns:
            numpy.ndarray: Frame capturado o None
        """
        if not self.camera_activa or not self.camera:
            logger.warning("⚠ Cámara no activa")
            return None
        
        ret, frame = self.camera.read()
        
        if not ret:
            logger.error("❌ Error capturando frame")
            return None
        
        return frame
    
    def detectar_rostros(self, frame):
        """
        Detecta todos los rostros en un frame
        
        Args:
            frame: Frame de OpenCV
        
        Returns:
            list: Lista de rostros detectados
        """
        try:
            # Guardar frame temporalmente
            temp_path = guardar_frame_temporal(frame, 'deteccion')
            
            # Extraer rostros
            rostros = DeepFace.extract_faces(
                img_path=temp_path,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                align=True
            )
            
            logger.debug(f"🔍 Detectados {len(rostros)} rostros")
            
            return rostros
            
        except Exception as e:
            logger.error(f"❌ Error detectando rostros: {e}")
            return []
    
    def identificar_persona(self, rostro_img, rostro_path):
        """
        Identifica una persona comparando con la base de datos
        
        Args:
            rostro_img: Imagen del rostro
            rostro_path (str): Ruta temporal del rostro
        
        Returns:
            dict: Información de la persona identificada
        """
        try:
            # Buscar en base de datos
            resultados = DeepFace.find(
                img_path=rostro_path,
                db_path=self.db_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                silent=True
            )
            
            # Analizar resultados
            if len(resultados) > 0 and len(resultados[0]) > 0:
                mejor_match = resultados[0].iloc[0]
                identidad = mejor_match['identity']
                distancia = mejor_match['distance']
                confianza = round((1 - distancia) * 100, 2)
                
                # Validar confianza
                if confianza >= self.umbral_confianza:
                    nombre = extraer_nombre_archivo(identidad)
                    rol = extraer_rol_ruta(identidad)
                    nivel_acceso = obtener_nivel_acceso(identidad)
                    genera_alerta, tipo_alerta = debe_generar_alerta(identidad, False)
                    
                    self.detecciones_exitosas += 1
                    
                    logger.info(f"✓ Identificado: {nombre} ({confianza}%)")
                    
                    return {
                        'encontrado': True,
                        'nombre': nombre,
                        'rol': rol,
                        'confianza': confianza,
                        'nivel_acceso': nivel_acceso,
                        'autorizado': True,
                        'genera_alerta': genera_alerta,
                        'tipo_alerta': tipo_alerta
                    }
                else:
                    logger.warning(f"⚠ Confianza baja: {confianza}%")
            
            # No se encontró o confianza baja
            return self._persona_desconocida()
            
        except Exception as e:
            logger.error(f"❌ Error identificando persona: {e}")
            return self._persona_desconocida()
    
    def _persona_desconocida(self):
        """
        Retorna información de persona desconocida
        
        Returns:
            dict: Información por defecto
        """
        return {
            'encontrado': False,
            'nombre': 'Desconocido',
            'rol': 'No autorizado',
            'confianza': 0,
            'nivel_acceso': 0,
            'autorizado': False,
            'genera_alerta': True,
            'tipo_alerta': 'critico'
        }
    
    def procesar_frame(self, frame):
        """
        Procesa un frame completo: detecta e identifica personas
        
        Args:
            frame: Frame de OpenCV
        
        Returns:
            dict: Frame procesado y detecciones
        """
        import base64
        
        self.total_detecciones += 1
        
        # Detectar rostros
        rostros = self.detectar_rostros(frame)
        
        detecciones = []
        
        # Procesar cada rostro
        for i, rostro in enumerate(rostros[:Config.MAX_DETECCIONES]):
            try:
                facial_area = rostro['facial_area']
                x, y, w, h = facial_area['x'], facial_area['y'], facial_area['w'], facial_area['h']
                
                # Extraer región del rostro del frame original
                rostro_img = frame[y:y+h, x:x+w]
                
                # Guardar temporalmente
                rostro_temp = guardar_frame_temporal(rostro_img, f'rostro_{i}')
                
                # Identificar persona
                info_persona = self.identificar_persona(rostro_img, rostro_temp)
                
                # Agregar información de ubicación
                deteccion = {
                    'id': generar_id_deteccion(),
                    'nombre': info_persona['nombre'],
                    'rol': info_persona['rol'],
                    'confianza': info_persona['confianza'],
                    'autorizado': info_persona['autorizado'],
                    'nivel_acceso': info_persona['nivel_acceso'],
                    'bbox': {
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h
                    },
                    'timestamp': datetime.now().isoformat(),
                    'genera_alerta': info_persona['genera_alerta'],
                    'tipo_alerta': info_persona.get('tipo_alerta')
                }
                
                detecciones.append(deteccion)
                
                # Generar alerta si es necesario
                if info_persona['genera_alerta']:
                    self.alertas_generadas += 1
                
            except Exception as e:
                logger.error(f"❌ Error procesando rostro {i}: {e}")
        
        # Convertir frame a base64 para transmisión
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Limpiar archivos temporales antiguos
        if self.total_detecciones % 100 == 0:
            limpiar_archivos_temporales()
        
        return {
            'frame': frame_base64,
            'detecciones': detecciones,
            'total_detectados': len(detecciones),
            'timestamp': datetime.now().isoformat()
        }
    
    def obtener_estadisticas(self):
        """
        Obtiene estadísticas del sistema
        
        Returns:
            dict: Estadísticas
        """
        return {
            'total_detecciones': self.total_detecciones,
            'detecciones_exitosas': self.detecciones_exitosas,
            'alertas_generadas': self.alertas_generadas,
            'personas_registradas': len(self.roles_cache),
            'tasa_exito': round((self.detecciones_exitosas / max(self.total_detecciones, 1)) * 100, 2),
            'modelo': self.model_name,
            'detector': self.detector_backend
        }
    
    def registrar_persona(self, nombre, rol, imagen_path):
        """
        Registra una nueva persona en el sistema
        
        Args:
            nombre (str): Nombre de la persona
            rol (str): Rol (empleados, vip, visitantes)
            imagen_path (str): Ruta de la imagen
        
        Returns:
            bool: True si se registró correctamente
        """
        try:
            if rol not in Config.ROLES:
                logger.error(f"❌ Rol inválido: {rol}")
                return False
            
            # Crear nombre de archivo
            nombre_archivo = nombre.lower().replace(' ', '_') + '.jpg'
            carpeta_destino = os.path.join(self.db_path, rol)
            ruta_destino = os.path.join(carpeta_destino, nombre_archivo)
            
            # Copiar imagen
            import shutil
            shutil.copy(imagen_path, ruta_destino)
            
            # Actualizar cache
            self.roles_cache = self._cargar_roles()
            
            logger.info(f"✓ Persona registrada: {nombre} como {rol}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error registrando persona: {e}")
            return False
    
    def eliminar_persona(self, nombre):
        """
        Elimina una persona del sistema
        
        Args:
            nombre (str): Nombre de la persona
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            if nombre in self.roles_cache:
                ruta = self.roles_cache[nombre]['ruta']
                os.remove(ruta)
                
                # Actualizar cache
                del self.roles_cache[nombre]
                
                logger.info(f"✓ Persona eliminada: {nombre}")
                return True
            else:
                logger.warning(f"⚠ Persona no encontrada: {nombre}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error eliminando persona: {e}")
            return False
    
    def __del__(self):
        """Destructor: liberar recursos"""
        self.detener_camara()


# ============================================
# TESTING
# ============================================

if __name__ == "__main__":
    print("🧪 Probando Sistema de Reconocimiento...\n")
    
    # Inicializar
    Config.init_app()
    sistema = SistemaReconocimiento()
    
    # Mostrar estadísticas
    print("\n📊 Estadísticas:")
    stats = sistema.obtener_estadisticas()
    for key, value in stats.items():
        print(f"  • {key}: {value}")
    
    # Test con cámara (si está disponible)
    if sistema.iniciar_camara():
        print("\n📹 Probando con cámara...")
        print("Presiona 'q' para salir\n")
        
        frame_count = 0
        
        while True:
            frame = sistema.capturar_frame()
            
            if frame is None:
                break
            
            # Procesar cada 30 frames
            if frame_count % 30 == 0:
                resultado = sistema.procesar_frame(frame)
                print(f"\nFrame {frame_count}:")
                print(f"  Detectados: {resultado['total_detectados']}")
                for det in resultado['detecciones']:
                    print(f"    • {det['nombre']} ({det['confianza']}%) - {det['rol']}")
            
            # Mostrar frame
            cv2.imshow('Sistema de Reconocimiento', frame)
            
            frame_count += 1
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        sistema.detener_camara()
        cv2.destroyAllWindows()
    else:
        print("⚠ No se pudo iniciar la cámara")
    
    print("\n✓ Tests completados")