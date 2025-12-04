"""
Sistema de logging para alertas de reconocimiento facial
"""

import json
import logging
import os
from datetime import datetime

from config import Config


class AlertLogger:
    """
    Gestor de logs de alertas del sistema de reconocimiento facial
    """

    def __init__(self, log_dir=None, filter_level="all"):
        """
        Inicializa el sistema de logging de alertas

        Args:
            log_dir (str): Directorio donde se guardarán los logs
            filter_level (str): Nivel de filtrado de alertas.
                Opciones: 'all' (todas), 'critico' (solo críticas),
                'alto' (alto y crítico), 'medio' (medio, alto y crítico)
                Por defecto: 'all'
        """
        self.log_dir = log_dir or Config.LOGS_DIR
        self.filter_level = filter_level.lower()
        os.makedirs(self.log_dir, exist_ok=True)

        # Archivo de log principal de alertas
        self.alerts_log_file = os.path.join(self.log_dir, f"alertas_{datetime.now().strftime('%Y%m%d')}.log")

        # Archivo JSON para alertas estructuradas
        self.alerts_json_file = os.path.join(self.log_dir, f"alertas_{datetime.now().strftime('%Y%m%d')}.json")

        # Configurar logger
        self.logger = logging.getLogger("AlertLogger")
        self.logger.setLevel(logging.INFO)

        # Handler para archivo de texto
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.alerts_log_file, mode="a", encoding="utf-8")
            file_handler.setLevel(logging.INFO)

            # Formato detallado para logs
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _debe_guardar_alerta(self, tipo_alerta):
        """
        Determina si una alerta debe guardarse según el filtro configurado

        Args:
            tipo_alerta (str): Tipo de alerta (critico, alto, medio, bajo)

        Returns:
            bool: True si debe guardarse, False si no
        """
        if self.filter_level == "all":
            return True
        elif self.filter_level == "critico":
            return tipo_alerta == "critico"
        elif self.filter_level == "alto":
            return tipo_alerta in ["critico", "alto"]
        elif self.filter_level == "medio":
            return tipo_alerta in ["critico", "alto", "medio"]
        return True

    def log_alerta(self, deteccion):
        """
        Registra una alerta en los archivos de log (si pasa el filtro)

        Args:
            deteccion (dict): Información de la detección que generó la alerta
        """
        tipo_alerta = deteccion.get("tipo_alerta", "bajo")

        # Verificar si debe guardarse según el filtro
        if not self._debe_guardar_alerta(tipo_alerta):
            return

        # Crear mensaje de log
        mensaje = (
            f"ALERTA [{tipo_alerta.upper()}] | "
            f"Persona: {deteccion['nombre']} | "
            f"Rol: {deteccion['rol']} | "
            f"Confianza: {deteccion['confianza']}% | "
            f"Ubicación: ({deteccion['bbox']['x']}, {deteccion['bbox']['y']})"
        )

        # Log en archivo de texto
        if tipo_alerta == "critico":
            self.logger.critical(mensaje)
        elif tipo_alerta == "alto":
            self.logger.error(mensaje)
        elif tipo_alerta == "medio":
            self.logger.warning(mensaje)
        else:
            self.logger.info(mensaje)

        # Log en JSON
        self._log_json(deteccion)

    def _log_json(self, deteccion):
        """
        Registra la alerta en formato JSON

        Args:
            deteccion (dict): Información de la detección
        """
        # Preparar datos para JSON
        alerta_data = {
            "timestamp": datetime.now().isoformat(),
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "nombre": deteccion["nombre"],
            "rol": deteccion["rol"],
            "nivel_acceso": deteccion.get("nivel_acceso", 0),
            "confianza": deteccion["confianza"],
            "tipo_alerta": deteccion["tipo_alerta"],
            "bbox": deteccion["bbox"],
            "analysis": deteccion.get("analysis", ""),
        }

        # Leer alertas existentes
        alertas = []
        if os.path.exists(self.alerts_json_file):
            try:
                with open(self.alerts_json_file, "r", encoding="utf-8") as f:
                    alertas = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                alertas = []

        # Agregar nueva alerta
        alertas.append(alerta_data)

        # Guardar en archivo
        with open(self.alerts_json_file, "w", encoding="utf-8") as f:
            json.dump(alertas, f, indent=2, ensure_ascii=False)

    def log_deteccion(self, deteccion):
        """
        Registra una detección normal (sin alerta)

        Args:
            deteccion (dict): Información de la detección
        """
        mensaje = f"DETECCIÓN | " f"Persona: {deteccion['nombre']} | " f"Rol: {deteccion['rol']} | " f"Confianza: {deteccion['confianza']}%"
        self.logger.info(mensaje)

    def log_sesion_inicio(self):
        """Registra el inicio de una sesión de reconocimiento"""
        self.logger.info("=" * 80)
        self.logger.info("NUEVA SESIÓN DE RECONOCIMIENTO INICIADA")
        self.logger.info("=" * 80)

    def log_sesion_fin(self, estadisticas):
        """
        Registra el fin de una sesión con estadísticas

        Args:
            estadisticas (dict): Estadísticas de la sesión
        """
        self.logger.info("-" * 80)
        self.logger.info("SESIÓN DE RECONOCIMIENTO FINALIZADA")
        self.logger.info(f"Frames procesados: {estadisticas.get('frames_procesados', 0)}")
        self.logger.info(f"Detecciones totales: {estadisticas.get('total_detecciones', 0)}")
        self.logger.info(f"Alertas generadas: {estadisticas.get('alertas_generadas', 0)}")
        self.logger.info("=" * 80)

    def obtener_alertas_del_dia(self):
        """
        Obtiene todas las alertas del día actual

        Returns:
            list: Lista de alertas
        """
        if os.path.exists(self.alerts_json_file):
            try:
                with open(self.alerts_json_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return []
        return []

    def obtener_estadisticas_alertas(self):
        """
        Obtiene estadísticas de las alertas del día

        Returns:
            dict: Estadísticas de alertas
        """
        alertas = self.obtener_alertas_del_dia()

        if not alertas:
            return {"total": 0, "por_tipo": {}, "por_persona": {}}

        # Contar por tipo
        por_tipo = {}
        for alerta in alertas:
            tipo = alerta.get("tipo_alerta", "desconocido")
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

        # Contar por persona
        por_persona = {}
        for alerta in alertas:
            nombre = alerta.get("nombre", "Desconocido")
            por_persona[nombre] = por_persona.get(nombre, 0) + 1

        return {"total": len(alertas), "por_tipo": por_tipo, "por_persona": por_persona, "alertas_recientes": alertas[-10:]}  # Últimas 10 alertas
