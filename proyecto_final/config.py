"""
Configuracion del sistema de reconocimiento facial
"""

import os


class Config:
    """Configuracion general del sistema"""

    # Rutas
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_DIR = os.path.join(BASE_DIR, "backend", "database")
    LOGS_DIR = os.path.join(BASE_DIR, "backend", "logs")
    TEMP_DIR = os.path.join(BASE_DIR, "backend", "temp")

    # Camara
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 1280
    CAMERA_HEIGHT = 720
    CAMERA_FPS = 30

    # Reconocimiento Facial
    MODELO_FACIAL = "Facenet"
    DETECTOR_BACKEND = "opencv"
    UMBRAL_CONFIANZA = 50

    # Procesamiento
    PROCESAR_CADA_N_FRAMES = 10
    MAX_DETECCIONES = 1

    # Categorias y Roles
    ROLES = {
        "empleados": {"nombre": "Empleado", "nivel_acceso": 2, "genera_alerta": False},
        "vip": {"nombre": "VIP", "nivel_acceso": 3, "genera_alerta": True, "tipo_alerta": "bajo"},
        "visitantes": {"nombre": "Visitante", "nivel_acceso": 1, "genera_alerta": True, "tipo_alerta": "medio"},
    }

    # Niveles de Alerta
    NIVELES_ALERTA = {
        "bajo": {"color": "green", "prioridad": 1},
        "medio": {"color": "yellow", "prioridad": 2},
        "alto": {"color": "orange", "prioridad": 3},
        "critico": {"color": "red", "prioridad": 4},
    }

    # Logs
    LOG_LEVEL = "DEBUG"
    LOG_FILE = os.path.join(LOGS_DIR, "sistema.log")
    LOG_MAX_SIZE = 10 * 1024 * 1024
    LOG_BACKUP_COUNT = 5

    @classmethod
    def init_app(cls):
        """Inicializar directorios necesarios"""
        os.makedirs(cls.DATABASE_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
        os.makedirs(cls.TEMP_DIR, exist_ok=True)

        # Crear subdirectorios de roles
        for rol in cls.ROLES.keys():
            os.makedirs(os.path.join(cls.DATABASE_DIR, rol), exist_ok=True)
