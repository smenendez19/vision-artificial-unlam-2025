"""
Sistema de Reconocimiento Facial usando DeepFace
"""

import logging
import os
import sys
from datetime import datetime

import cv2

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import Config
from deepface import DeepFace
from utils.file_utils import guardar_frame_temporal, limpiar_archivos_temporales
from utils.helpers import (
    debe_generar_alerta,
    extraer_nombre_archivo,
    extraer_rol_ruta,
    generar_id_deteccion,
    obtener_nivel_acceso,
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
        logger.info("Inicializando Sistema de Reconocimiento Facial...")

        self.db_path = Config.DATABASE_DIR
        self.model_name = Config.MODELO_FACIAL
        self.detector_backend = Config.DETECTOR_BACKEND
        self.umbral_confianza = Config.UMBRAL_CONFIANZA

        # Camara
        self.camera = None
        self.camera_activa = False

        # Cache de roles
        self.roles_cache = self._cargar_roles()

        # Estadisticas
        self.total_detecciones = 0
        self.detecciones_exitosas = 0
        self.alertas_generadas = 0

        logger.info(f"Modelo: {self.model_name}")
        logger.info(f"Detector: {self.detector_backend}")
        logger.info(f"Base de datos: {self.db_path}")
        logger.info(f"Personas registradas: {len(self.roles_cache)}")

    def _cargar_roles(self):
        """
        Carga informacion de roles desde la estructura de carpetas

        Returns:
            dict: Diccionario con informacion de cada persona (nombre -> info)
        """
        roles = {}

        for rol, info in Config.ROLES.items():
            carpeta_rol = os.path.join(self.db_path, rol)
            if os.path.exists(carpeta_rol):
                # Iterar sobre cada carpeta de persona dentro de la categoria
                for nombre_persona in os.listdir(carpeta_rol):
                    carpeta_persona = os.path.join(carpeta_rol, nombre_persona)
                    if os.path.isdir(carpeta_persona):
                        # Contar imagenes de esta persona
                        imagenes = [f for f in os.listdir(carpeta_persona) if f.endswith((".jpg", ".jpeg", ".png"))]
                        num_fotos = len(imagenes)

                        if num_fotos > 0:
                            # Nombre limpio de la persona
                            nombre = extraer_nombre_archivo(nombre_persona)

                            roles[nombre] = {
                                "rol": info["nombre"],
                                "nivel_acceso": info["nivel_acceso"],
                                "categoria": rol,
                                "num_fotos": num_fotos
                            }

        logger.info(f"Cargados {len(roles)} perfiles")
        for nombre, info in roles.items():
            logger.debug(f"  - {nombre}: {info['num_fotos']} foto(s)")

        return roles

    def iniciar_camara(self, camera_index=None):
        """
        Inicia la camara

        Args:
            camera_index (int): Indice de la camara

        Returns:
            bool: True si se inicio correctamente
        """
        if camera_index is None:
            camera_index = Config.CAMERA_INDEX

        try:
            self.camera = cv2.VideoCapture(0)

            if not self.camera.isOpened():
                logger.error("No se pudo abrir la camara")
                return False

            # Configurar resolucion
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)

            self.camera_activa = True
            logger.info("Camara iniciada correctamente")
            return True

        except Exception as e:
            logger.error(f"Error iniciando camara: {e}")
            return False

    def detener_camara(self):
        """Detiene la camara"""
        if self.camera:
            self.camera.release()
            self.camera_activa = False
            logger.info("Camara detenida")

    def capturar_frame(self):
        """
        Captura un frame de la camara

        Returns:
            numpy.ndarray: Frame capturado o None
        """
        if not self.camera_activa or not self.camera:
            logger.warning("Camara no activa")
            return None

        ret, frame = self.camera.read()

        if not ret:
            logger.error("Error capturando frame")
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
            temp_path = guardar_frame_temporal(frame, "deteccion")

            # Extraer rostros
            rostros = DeepFace.extract_faces(img_path=temp_path, detector_backend=self.detector_backend, enforce_detection=False, align=True)

            logger.debug(f"Detectados {len(rostros)} rostros")

            return rostros

        except Exception as e:
            logger.error(f"Error detectando rostros: {e}")
            return []

    def identificar_persona(self, rostro_img, rostro_path):
        """
        Identifica una persona comparando con la base de datos

        Args:
            rostro_img: Imagen del rostro
            rostro_path (str): Ruta temporal del rostro

        Returns:
            dict: Informacion de la persona identificada
        """
        try:
            from deepface import DeepFace

            detecciones = DeepFace.extract_faces(
                img_path=rostro_path,
                detector_backend=self.detector_backend,
                enforce_detection=False
            )

            if len(detecciones) == 0:
                # Casi nunca pasa, pero lo dejo por robustez
                cara_valida = False
            else:
                d = detecciones[0]
                area = d["facial_area"]
                conf = d.get("confidence", 0)

                # Si el detector no encontró nada, estas señales lo delatan:
                if conf == 0 or area["w"] == 0 or area["h"] == 0:
                    cara_valida = False
                else:
                    cara_valida = True

            if not cara_valida:
                logger.info("No se detectaron caras reales en la imagen — no se genera alerta.")
                return {
                    "encontrado": False,
                    "autorizado": False,
                    "genera_alerta": False,
                    "tipo_alerta": None,
                    "nombre": "no_face_detected_or_no_match"
                }

            # 2) Si hay cara, usar la imagen completa o recortada
            resultados = DeepFace.find(
                img_path=rostro_path,
                db_path=self.db_path,
                model_name=self.model_name,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                silent=True,
            )

            # Analizar resultados
            if len(resultados) > 0 and len(resultados[0]) > 0:
                mejor_match = resultados[0].iloc[0]
                identidad = mejor_match["identity"]
                distancia = mejor_match["distance"]
                confianza = round((1 - distancia) * 100, 2)

                logger.info(f"Match encontrado: {identidad} - Distancia: {distancia:.4f} - Confianza: {confianza}%")

                # Validar confianza
                if confianza >= self.umbral_confianza:
                    nombre = extraer_nombre_archivo(identidad)
                    rol = extraer_rol_ruta(identidad)
                    nivel_acceso = obtener_nivel_acceso(identidad)
                    genera_alerta, tipo_alerta = debe_generar_alerta(identidad, False)

                    self.detecciones_exitosas += 1

                    logger.info(f"Identificado: {nombre} ({confianza}%)")

                    return {
                        "encontrado": True,
                        "nombre": nombre,
                        "rol": rol,
                        "confianza": confianza,
                        "nivel_acceso": nivel_acceso,
                        "autorizado": True,
                        "genera_alerta": genera_alerta,
                        "tipo_alerta": tipo_alerta,
                    }
                else:
                    logger.warning(f"Confianza baja: {confianza}% < {self.umbral_confianza}%")
            else:
                logger.warning("No se encontraron matches en la base de datos")

            analysis = DeepFace.analyze(
                img_path = rostro_path, actions = ['age', 'gender', 'race']
            )
            analysis_str = ""
            if analysis is not None:
                age = analysis[0]["age"]
                gender = analysis[0]["dominant_gender"]
                race = analysis[0]["dominant_race"]
                analysis_str = info = f"Edad: {age}, Genero: {gender}, Etnia: {race}"

            # No se encontro o confianza baja
            return self._persona_desconocida(analysis_str)

        except Exception as e:
            logger.error(f"Error identificando persona: {e}")
            import traceback
            traceback.print_exc()
            return self._persona_desconocida()

    def _persona_desconocida(self, analysis = ""):
        """
        Retorna informacion de persona desconocida

        Returns:
            dict: Informacion por defecto
        """
        return {
            "encontrado": False,
            "nombre": "Desconocido",
            "rol": "No autorizado",
            "confianza": 0,
            "nivel_acceso": 0,
            "autorizado": False,
            "genera_alerta": True,
            "tipo_alerta": "critico",
            "analysis": analysis
        }

    def procesar_frame(self, frame):
        """
        Procesa un frame completo: detecta e identifica personas

        Args:
            frame: Frame de OpenCV

        Returns:
            dict: Detecciones encontradas
        """
        self.total_detecciones += 1

        # Detectar rostros
        rostros = self.detectar_rostros(frame)

        detecciones = []

        # Procesar cada rostro
        for i, rostro in enumerate(rostros[: Config.MAX_DETECCIONES]):
            try:
                facial_area = rostro["facial_area"]
                x, y, w, h = facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]

                # Extraer region del rostro del frame original
                rostro_img = frame[y: y + h, x: x + w]

                # Guardar temporalmente
                rostro_temp = guardar_frame_temporal(rostro_img, f"rostro_{i}")

                # Identificar persona
                info_persona = self.identificar_persona(rostro_img, rostro_temp)
                if info_persona["nombre"] == "no_face_detected_or_no_match":
                    continue

                # Agregar informacion de ubicacion
                deteccion = {
                    "id": generar_id_deteccion(),
                    "nombre": info_persona["nombre"],
                    "rol": info_persona["rol"],
                    "confianza": info_persona["confianza"],
                    "autorizado": info_persona["autorizado"],
                    "nivel_acceso": info_persona["nivel_acceso"],
                    "bbox": {"x": x, "y": y, "w": w, "h": h},
                    "timestamp": datetime.now().isoformat(),
                    "genera_alerta": info_persona["genera_alerta"],
                    "tipo_alerta": info_persona.get("tipo_alerta"),
                    "analysis": info_persona.get("analysis")
                }

                detecciones.append(deteccion)

                # Generar alerta si es necesario
                if info_persona["genera_alerta"]:
                    self.alertas_generadas += 1

            except Exception as e:
                logger.error(f"Error procesando rostro {i}: {e}")

        # Limpiar archivos temporales antiguos
        if self.total_detecciones % 100 == 0:
            limpiar_archivos_temporales()

        return {"detecciones": detecciones, "total_detectados": len(detecciones), "timestamp": datetime.now().isoformat()}

    def obtener_estadisticas(self):
        """
        Obtiene estadisticas del sistema

        Returns:
            dict: Estadisticas
        """
        return {
            "total_detecciones": self.total_detecciones,
            "detecciones_exitosas": self.detecciones_exitosas,
            "alertas_generadas": self.alertas_generadas,
            "personas_registradas": len(self.roles_cache),
            "tasa_exito": round((self.detecciones_exitosas / max(self.total_detecciones, 1)) * 100, 2),
            "modelo": self.model_name,
            "detector": self.detector_backend,
        }

    def __del__(self):
        """Destructor: liberar recursos"""
        self.detener_camara()
