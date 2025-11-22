"""
Configuración del sistema de reconocimiento facial
"""
import os

class Config:
    """Configuración general del sistema"""
    
    # Servidor
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    SECRET_KEY = 'faceguard-secret-key-change-in-production'
    
    # Rutas
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    LOGS_DIR = os.path.join(BASE_DIR, 'logs')
    TEMP_DIR = os.path.join(BASE_DIR, 'temp')
    
    # Cámara
    CAMERA_INDEX = 0  # 0 = cámara por defecto
    CAMERA_WIDTH = 1280
    CAMERA_HEIGHT = 720
    CAMERA_FPS = 30
    
    # Reconocimiento Facial
    MODELO_FACIAL = 'Facenet'  # Opciones: 'VGG-Face', 'Facenet', 'ArcFace', 'Dlib', 'OpenFace'
    DETECTOR_BACKEND = 'opencv'  # Opciones: 'opencv', 'ssd', 'dlib', 'mtcnn', 'retinaface'
    UMBRAL_CONFIANZA = 50  # % mínimo para considerar reconocido
    
    # Procesamiento
    PROCESAR_CADA_N_FRAMES = 10 # Procesar cada N frames para mejorar rendimiento
    MAX_DETECCIONES = 4  # Máximo de rostros a procesar simultáneamente
    
    # Categorías y Roles
    ROLES = {
        'empleados': {
            'nombre': 'Empleado',
            'nivel_acceso': 2,
            'genera_alerta': False
        },
        'vip': {
            'nombre': 'VIP',
            'nivel_acceso': 3,
            'genera_alerta': True,  # Notificar cuando ingresa un VIP
            'tipo_alerta': 'bajo'
        },
        'visitantes': {
            'nombre': 'Visitante',
            'nivel_acceso': 1,
            'genera_alerta': True,
            'tipo_alerta': 'medio'
        }
    }
    
    # Niveles de Alerta
    NIVELES_ALERTA = {
        'bajo': {
            'color': 'green',
            'prioridad': 1
        },
        'medio': {
            'color': 'yellow',
            'prioridad': 2
        },
        'alto': {
            'color': 'orange',
            'prioridad': 3
        },
        'critico': {
            'color': 'red',
            'prioridad': 4
        }
    }
    
    # Logs
    LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FILE = os.path.join(LOGS_DIR, 'sistema.log')
    LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5
    
    # CORS
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:3001']
    
    @classmethod
    def init_app(cls):
        """Inicializar directorios necesarios"""
        os.makedirs(cls.DATABASE_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        
        # Crear subdirectorios de roles
        for rol in cls.ROLES.keys():
            os.makedirs(os.path.join(cls.DATABASE_DIR, rol), exist_ok=True)


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class TestConfig(Config):
    """Configuración para tests"""
    TESTING = True
    DATABASE_DIR = os.path.join(Config.BASE_DIR, 'test_database')


# Seleccionar configuración según entorno
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
    'default': DevelopmentConfig
}