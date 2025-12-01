"""
Utilidades para dibujar en frames de OpenCV
"""

import cv2


def dibujar_bbox(frame, bbox, nombre, rol, confianza, autorizado):
    """
    Dibuja un bounding box con informacion de la persona

    Args:
        frame: Frame de OpenCV
        bbox: Diccionario con {x, y, w, h}
        nombre: Nombre de la persona
        rol: Rol de la persona
        confianza: Confianza del reconocimiento (0-100)
        autorizado: Boolean si esta autorizado

    Returns:
        frame: Frame con el bbox dibujado
    """
    x, y, w, h = bbox["x"], bbox["y"], bbox["w"], bbox["h"]

    # Color segun autorizacion
    if autorizado:
        color = (0, 255, 0)
        color_fondo = (0, 200, 0)
    else:
        color = (0, 0, 255)
        color_fondo = (0, 0, 200)

    # Dibujar rectangulo principal
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)

    # Esquinas decorativas
    longitud_esquina = 20
    grosor_esquina = 4
    cv2.line(frame, (x, y), (x + longitud_esquina, y), color, grosor_esquina)
    cv2.line(frame, (x, y), (x, y + longitud_esquina), color, grosor_esquina)
    cv2.line(frame, (x + w, y), (x + w - longitud_esquina, y), color, grosor_esquina)
    cv2.line(frame, (x + w, y), (x + w, y + longitud_esquina), color, grosor_esquina)
    cv2.line(frame, (x, y + h), (x + longitud_esquina, y + h), color, grosor_esquina)
    cv2.line(frame, (x, y + h), (x, y + h - longitud_esquina), color, grosor_esquina)
    cv2.line(frame, (x + w, y + h), (x + w - longitud_esquina, y + h), color, grosor_esquina)
    cv2.line(frame, (x + w, y + h), (x + w, y + h - longitud_esquina), color, grosor_esquina)

    # Panel de informacion
    texto_nombre = f"{nombre}"
    texto_rol = f"{rol}"
    texto_confianza = f"{confianza:.0f}%" if confianza > 0 else "N/A"

    # Calcular tamano del panel
    (w_texto, h_texto), _ = cv2.getTextSize(texto_nombre, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)

    # Fondo del panel
    y_panel = y - 80
    if y_panel < 0:
        y_panel = y + h + 10

    cv2.rectangle(frame, (x, y_panel), (x + max(w_texto + 20, 200), y_panel + 75), color_fondo, -1)

    cv2.rectangle(frame, (x, y_panel), (x + max(w_texto + 20, 200), y_panel + 75), color, 2)

    # Textos del panel
    cv2.putText(frame, texto_nombre, (x + 10, y_panel + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, texto_rol, (x + 10, y_panel + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1)

    cv2.putText(frame, texto_confianza, (x + 10, y_panel + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1)

    # Icono de estado
    centro_icono = (x + w - 30, y + 30)
    if autorizado:
        cv2.circle(frame, centro_icono, 20, (0, 255, 0), -1)
        cv2.putText(frame, "OK", (centro_icono[0] - 15, centro_icono[1] + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    else:
        cv2.circle(frame, centro_icono, 20, (0, 0, 255), -1)
        cv2.line(frame, (centro_icono[0] - 10, centro_icono[1] - 10), (centro_icono[0] + 10, centro_icono[1] + 10), (255, 255, 255), 3)
        cv2.line(frame, (centro_icono[0] + 10, centro_icono[1] - 10), (centro_icono[0] - 10, centro_icono[1] + 10), (255, 255, 255), 3)

    return frame


def dibujar_menu_seleccion(frame, opciones, seleccion, titulo="MENU"):
    """
    Dibuja un menu de seleccion en el frame

    Args:
        frame: Frame de OpenCV
        opciones: Lista de strings con las opciones
        seleccion: Indice de la opcion seleccionada
        titulo: Titulo del menu

    Returns:
        frame: Frame con el menu dibujado
    """
    altura, ancho = frame.shape[:2]

    # Fondo semi-transparente
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (ancho, altura), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Titulo
    cv2.putText(frame, titulo, (ancho // 2 - 150, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)

    # Opciones
    y_pos = 200
    for i, opcion in enumerate(opciones):
        if i == seleccion:
            # Opcion seleccionada
            color_texto = (0, 255, 0)
            prefijo = ">> "
            grosor = 2
        else:
            # Opcion no seleccionada
            color_texto = (200, 200, 200)
            prefijo = "   "
            grosor = 1

        texto = f"{prefijo}{i + 1}. {opcion}"
        cv2.putText(frame, texto, (100, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color_texto, grosor)
        y_pos += 80

    # Instrucciones
    cv2.putText(
        frame, "Usar flechas o W/S - Numeros 1-3 - ENTER seleccionar - Q salir", (50, altura - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1
    )

    return frame


def mostrar_mensaje_centro(frame, mensaje, color=(255, 255, 255)):
    """
    Muestra un mensaje en el centro del frame

    Args:
        frame: Frame de OpenCV
        mensaje: Texto a mostrar
        color: Color del texto (BGR)

    Returns:
        frame: Frame con el mensaje
    """
    altura, ancho = frame.shape[:2]

    # Fondo semi-transparente
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, altura // 2 - 60), (ancho, altura // 2 + 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Texto
    (w_texto, h_texto), _ = cv2.getTextSize(mensaje, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2)
    x_texto = (ancho - w_texto) // 2
    y_texto = altura // 2

    cv2.putText(frame, mensaje, (x_texto, y_texto), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

    return frame
