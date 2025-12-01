"""
Funciones auxiliares para el sistema
"""

import os
import sys
import uuid

from config import Config

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


def extraer_nombre_archivo(ruta_archivo):
    """
    Extrae el nombre limpio de una persona desde el nombre del archivo

    Args:
        ruta_archivo (str): Ruta completa del archivo

    Returns:
        str: Nombre de la persona sin numeros/timestamps
    """
    nombre_archivo = os.path.splitext(os.path.basename(ruta_archivo))[0]
    partes = nombre_archivo.split("_")

    nombre_limpio = []
    for parte in partes:
        if parte.isdigit():
            continue
        nombre_limpio.append(parte)

    if nombre_limpio:
        nombre = " ".join(nombre_limpio).title()
    else:
        nombre = partes[0].title()

    return nombre


def extraer_rol_ruta(ruta_archivo):
    """
    Extrae el rol desde la ruta del archivo
    Estructura esperada: .../database/categoria/persona/foto.jpg

    Args:
        ruta_archivo (str): Ruta completa

    Returns:
        str: Nombre del rol
    """
    partes = ruta_archivo.split(os.sep)

    # La categoria esta 3 niveles arriba del archivo (database/categoria/persona/foto.jpg)
    if len(partes) >= 3:
        categoria = partes[-3]

        if categoria in Config.ROLES:
            return Config.ROLES[categoria]["nombre"]

    return "Desconocido"


def obtener_nivel_acceso(ruta_archivo):
    """
    Obtiene el nivel de acceso desde la ruta del archivo
    Estructura esperada: .../database/categoria/persona/foto.jpg

    Args:
        ruta_archivo (str): Ruta completa

    Returns:
        int: Nivel de acceso
    """
    partes = ruta_archivo.split(os.sep)

    # La categoria esta 3 niveles arriba del archivo (database/categoria/persona/foto.jpg)
    if len(partes) >= 3:
        categoria = partes[-3]

        if categoria in Config.ROLES:
            return Config.ROLES[categoria]["nivel_acceso"]

    return 0


def debe_generar_alerta(ruta_archivo, es_desconocido):
    """
    Determina si debe generar alerta para esta deteccion
    Estructura esperada: .../database/categoria/persona/foto.jpg

    Args:
        ruta_archivo (str): Ruta del archivo
        es_desconocido (bool): Si la persona es desconocida

    Returns:
        tuple: (debe_generar, tipo_alerta)
    """
    if es_desconocido:
        return True, "critico"

    partes = ruta_archivo.split(os.sep)

    # La categoria esta 3 niveles arriba del archivo (database/categoria/persona/foto.jpg)
    if len(partes) >= 3:
        categoria = partes[-3]

        if categoria in Config.ROLES:
            rol_info = Config.ROLES[categoria]
            genera = rol_info.get("genera_alerta", False)
            tipo = rol_info.get("tipo_alerta", "bajo")
            return genera, tipo

    return False, None


def generar_id_deteccion():
    """
    Genera un ID unico para una deteccion

    Returns:
        str: ID unico corto
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
    nombre = nombre.lower().replace(" ", "_")
    caracteres_validos = "abcdefghijklmnopqrstuvwxyz0123456789_"
    nombre = "".join(c for c in nombre if c in caracteres_validos)

    return nombre
