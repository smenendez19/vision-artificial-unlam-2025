"""
FACEGUARD - Sistema de Reconocimiento Facial
Aplicacion principal con menu interactivo

Mejoras implementadas:
- Menu principal con navegacion por flechas arriba/abajo
- Menu visual en OpenCV para seleccion de categoria (sin input de terminal)
- Reconocimiento mejorado: multiples fotos de la misma persona se identifican correctamente
- Carpeta backend limpiada: solo contiene database/, logs/ y temp/
- Config.py movido a raiz del proyecto
- Deteccion robusta de teclas con codigos completos (sin mascara 0xFF en flechas)
"""

import os
import sys
from datetime import datetime

import cv2
import numpy as np
from config import Config
from datasets.capturador import CapturadorDataset
from modules.reconocimiento import SistemaReconocimiento
from utils.draw_utils import (
    dibujar_bbox,
    dibujar_menu_seleccion,
    mostrar_mensaje_centro,
)

# Agregar paths necesarios
sys.path.append(os.path.dirname(__file__))


class AplicacionFaceGuard:
    """
    Aplicacion principal con menu interactivo
    """

    def __init__(self):
        """Inicializar aplicacion"""
        print("\n" + "=" * 70)
        print("FACEGUARD - Sistema de Reconocimiento Facial")
        print("=" * 70 + "\n")

        # Inicializar configuracion
        Config.init_app()

        # Estadisticas de sesion
        self.frame_count = 0
        self.detecciones_sesion = []
        self.alertas_sesion = []

    def mostrar_menu_principal(self):
        """
        Muestra el menu principal y retorna la seleccion

        Returns:
            int: Opcion seleccionada (1-3) o 0 para salir
        """
        # Crear frame negro para el menu
        frame = np.ones((720, 1280, 3), dtype="uint8") * 255

        opciones = [
            "Capturar nuevo dataset de persona",
            "Entrenar modelo de reconocimiento",
            "Reconocimiento facial en tiempo real",
            "Salir"
        ]

        seleccion = 0

        while True:
            # Dibujar menu
            frame_menu = frame.copy()
            frame_menu = dibujar_menu_seleccion(frame_menu, opciones, seleccion, "FACEGUARD - MENU PRINCIPAL")

            cv2.imshow("FaceGuard", frame_menu)

            key = cv2.waitKeyEx(10)

            # Tecla arriba: flecha arriba o W
            if key == 2490368 or key == ord("w") or key == ord("W"):
                seleccion = (seleccion - 1) % len(opciones)

            # Tecla abajo: flecha abajo o S
            elif key == 2621440 or key == ord("s") or key == ord("S"):
                seleccion = (seleccion + 1) % len(opciones)

            # Teclas numericas directas
            elif key == ord("1"):
                cv2.destroyAllWindows()
                return 1
            elif key == ord("2"):
                cv2.destroyAllWindows()
                return 2
            elif key == ord("3"):
                cv2.destroyAllWindows()
                return 3
            elif key == ord("4"):
                cv2.destroyAllWindows()
                return 4

            # Enter para seleccionar
            elif key == 13 or key == ord("\r") or key == ord("\n"):
                cv2.destroyAllWindows()
                return seleccion + 1

            # Q para salir
            elif key == ord("q") or key == ord("Q"):
                cv2.destroyAllWindows()
                return 0

    def menu_captura_dataset(self):
        """
        Menu para capturar dataset de una persona
        """
        # Menu visual para seleccionar categoria
        frame = np.ones((720, 1280, 3), dtype="uint8") * 255

        categorias_opciones = ["Empleado", "VIP", "Visitante"]
        categorias_map = {0: "empleados", 1: "vip", 2: "visitantes"}

        seleccion = 0

        # Seleccionar categoria
        while True:
            frame_menu = frame.copy()
            frame_menu = dibujar_menu_seleccion(frame_menu, categorias_opciones, seleccion, "SELECCIONAR CATEGORIA")

            cv2.imshow("FaceGuard - Captura Dataset", frame_menu)

            key = cv2.waitKeyEx(10)

            # Flechas arriba/abajo o W/S
            if key == 2490368 or key == ord("w") or key == ord("W"):
                seleccion = (seleccion - 1) % len(categorias_opciones)
            elif key == 2621440 or key == ord("s") or key == ord("S"):
                seleccion = (seleccion + 1) % len(categorias_opciones)
            elif key == ord("1"):
                seleccion = 0
                break
            elif key == ord("2"):
                seleccion = 1
                break
            elif key == ord("3"):
                seleccion = 2
                break
            elif key == 13 or key == ord("\r") or key == ord("\n"):
                break
            elif key == ord("q") or key == ord("Q"):
                cv2.destroyAllWindows()
                return

        categoria = categorias_map[seleccion]
        cv2.destroyAllWindows()

        # Pedir nombre por consola (necesario para texto libre)
        print(f"\nCategoria seleccionada: {categorias_opciones[seleccion]}")
        while True:
            nombre = input("Nombre completo (sin numeros): ").strip()
            if nombre and not any(c.isdigit() for c in nombre):
                break
            print("Nombre invalido (no uses numeros)")

        # Capturar dataset
        capturador = CapturadorDataset()
        exito = capturador.capturar_dataset_persona(nombre, categoria, objetivo=10)

        if exito:
            print("\nDataset capturado exitosamente!")
        else:
            print("\nCaptura incompleta o cancelada")

    def mostrar_info_pantalla(self, frame, sistema):
        """
        Dibuja informacion en la pantalla

        Args:
            frame: Frame de OpenCV
            sistema: Instancia del sistema de reconocimiento

        Returns:
            frame: Frame con informacion dibujada
        """
        altura, ancho = frame.shape[:2]

        # Fondo semi-transparente para el panel de info
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (ancho, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Titulo
        cv2.putText(frame, "FACEGUARD - Sistema de Reconocimiento", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # Informacion
        info_textos = [
            f"Frame: {self.frame_count}",
            f"Personas registradas: {len(sistema.roles_cache)}",
            f"Detecciones sesion: {len(self.detecciones_sesion)}",
            f"Alertas generadas: {len(self.alertas_sesion)}",
        ]

        y_pos = 65
        for texto in info_textos:
            cv2.putText(frame, texto, (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_pos += 25

        # Controles
        cv2.putText(
            frame,
            "Q - Salir | ESPACIO - Pausar | R - Reiniciar | S - Screenshot",
            (20, altura - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (200, 200, 200),
            1,
        )

        return frame

    def dibujar_detecciones(self, frame, detecciones):
        """
        Dibuja las detecciones en el frame

        Args:
            frame: Frame de OpenCV
            detecciones: Lista de detecciones

        Returns:
            frame: Frame con detecciones dibujadas
        """
        for deteccion in detecciones:
            frame = dibujar_bbox(frame, deteccion["bbox"], deteccion["nombre"], deteccion["rol"], deteccion["confianza"], deteccion["autorizado"])

        return frame

    def mostrar_alerta(self, frame, alerta):
        """
        Muestra una alerta en pantalla

        Args:
            frame: Frame de OpenCV
            alerta: Informacion de la alerta
        """
        altura, ancho = frame.shape[:2]

        # Panel de alerta en la parte superior
        if alerta["tipo_alerta"] == "critico":
            color_alerta = (0, 0, 255)
            texto_nivel = "ALERTA CRITICA"
        elif alerta["tipo_alerta"] == "alto":
            color_alerta = (0, 165, 255)
            texto_nivel = "ALERTA ALTA"
        elif alerta["tipo_alerta"] == "medio":
            color_alerta = (0, 255, 255)
            texto_nivel = "ALERTA MEDIA"
        else:
            color_alerta = (0, 255, 0)
            texto_nivel = "NOTIFICACION"

        # Parpadeo para alertas criticas
        if alerta["tipo_alerta"] == "critico" and self.frame_count % 10 < 5:
            # Fondo de alerta
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 150), (ancho, 250), color_alerta, -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

        # Panel de alerta
        cv2.rectangle(frame, (50, 150), (ancho - 50, 250), color_alerta, 3)
        cv2.rectangle(frame, (50, 150), (ancho - 50, 190), color_alerta, -1)

        # Texto de alerta
        cv2.putText(frame, texto_nivel, (70, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

        cv2.putText(frame, f"Persona: {alerta['nombre']} {alerta["analysis"] if alerta["tipo_alerta"] == "critico" else ''}", (70, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(frame, f"Rol: {alerta['rol']}", (70, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    def guardar_screenshot(self, frame):
        """Guarda un screenshot del frame actual"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"Screenshot guardado: {filename}")

    def mostrar_estadisticas_finales(self, sistema):
        """Muestra estadisticas al finalizar"""
        print("\n" + "=" * 70)
        print("ESTADISTICAS DE LA SESION")
        print("=" * 70)

        stats = sistema.obtener_estadisticas()

        print(f"\nFrames procesados: {self.frame_count}")
        print(f"Total detecciones: {stats['total_detecciones']}")
        print(f"Detecciones exitosas: {stats['detecciones_exitosas']}")
        print(f"Alertas generadas: {stats['alertas_generadas']}")
        print(f"Tasa de exito: {stats['tasa_exito']}%")

        if self.detecciones_sesion:
            print("\nPersonas detectadas en esta sesion:")
            personas_unicas = set([d["nombre"] for d in self.detecciones_sesion])
            for persona in personas_unicas:
                cantidad = sum(1 for d in self.detecciones_sesion if d["nombre"] == persona)
                print(f"  - {persona}: {cantidad} veces")

        if self.alertas_sesion:
            print("\nAlertas generadas:")
            for alerta in self.alertas_sesion[-5:]:
                print(f"  - {alerta['timestamp']}: {alerta['nombre']} ({alerta['tipo_alerta']})")

        print("\n" + "=" * 70)

    def reconocimiento_tiempo_real(self):
        """
        Ejecuta el reconocimiento facial en tiempo real
        """
        print("\n" + "=" * 70)
        print("RECONOCIMIENTO FACIAL EN TIEMPO REAL")
        print("=" * 70 + "\n")

        # Inicializar sistema
        sistema = SistemaReconocimiento()

        print("Sistema inicializado correctamente")
        print(f"Personas registradas: {len(sistema.roles_cache)}")
        print(f"Modelo: {sistema.model_name}")
        print(f"Detector: {sistema.detector_backend}\n")

        # Iniciar camara
        if not sistema.iniciar_camara():
            print("Error: No se pudo iniciar la camara")
            input("\nPresiona ENTER para volver al menu principal...")
            return

        print("Camara iniciada")
        print("\nCONTROLES:")
        print("  - Q: Salir")
        print("  - ESPACIO: Pausar/Reanudar")
        print("  - R: Reiniciar estadisticas")
        print("  - S: Capturar screenshot")
        print("\nIniciando deteccion...\n")

        # Reiniciar contadores
        self.frame_count = 0
        self.detecciones_sesion = []
        self.alertas_sesion = []

        pausado = False
        ultima_alerta = None
        frames_desde_alerta = 0

        try:
            while True:
                if not pausado:
                    # Capturar frame
                    frame = sistema.capturar_frame()

                    if frame is None:
                        print("Error capturando frame")
                        break

                    # Procesar cada N frames
                    if self.frame_count % Config.PROCESAR_CADA_N_FRAMES == 0:
                        resultado = sistema.procesar_frame(frame)

                        # Guardar detecciones
                        if resultado["detecciones"]:
                            self.detecciones_sesion.extend(resultado["detecciones"])

                            # Log en consola
                            print(f"\nFrame {self.frame_count}:")
                            for det in resultado["detecciones"]:
                                icono = "OK" if det["autorizado"] else "ALERTA"
                                print(f"  [{icono}] {det['nombre']} - {det['rol']} ({det['confianza']}%)")

                            # Generar alertas
                            for det in resultado["detecciones"]:
                                if det["genera_alerta"]:
                                    ultima_alerta = det
                                    frames_desde_alerta = 0
                                    self.alertas_sesion.append(
                                        {
                                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                                            "nombre": det["nombre"],
                                            "rol": det["rol"],
                                            "tipo_alerta": det["tipo_alerta"],
                                        }
                                    )
                                    print(f"\n  ALERTA: {det['nombre']} - {det['tipo_alerta']}")

                        # Dibujar detecciones
                        frame = self.dibujar_detecciones(frame, resultado["detecciones"])

                    # Mostrar alerta si hay una reciente
                    if ultima_alerta and frames_desde_alerta < 20:
                        self.mostrar_alerta(frame, ultima_alerta)
                        frames_desde_alerta += 1

                    # Informacion en pantalla
                    frame = self.mostrar_info_pantalla(frame, sistema)

                    self.frame_count += 1

                else:
                    # Mensaje de pausa
                    frame = mostrar_mensaje_centro(frame, "PAUSADO - Presiona ESPACIO para continuar", (255, 255, 0))

                # Mostrar frame
                cv2.imshow("FaceGuard - Reconocimiento Facial", frame)

                # Controles de teclado
                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == ord("Q"):
                    print("\nDeteniendo sistema...")
                    break
                elif key == ord(" "):
                    pausado = not pausado
                    estado = "PAUSADO" if pausado else "REANUDADO"
                    print(f"\n{estado}")
                elif key == ord("r") or key == ord("R"):
                    self.detecciones_sesion = []
                    self.alertas_sesion = []
                    self.frame_count = 0
                    print("\nEstadisticas reiniciadas")
                elif key == ord("s") or key == ord("S"):
                    self.guardar_screenshot(frame)

        except KeyboardInterrupt:
            print("\n\nPrograma interrumpido por el usuario")

        finally:
            # Limpiar
            sistema.detener_camara()
            cv2.destroyAllWindows()

            # Mostrar estadisticas finales
            self.mostrar_estadisticas_finales(sistema)

            print("\nSistema detenido correctamente")
            input("\nPresiona ENTER para volver al menu principal...")

    def menu_entrenar_modelo(self):
        """
        Entrena el modelo de reconocimiento facial procesando todas las imagenes
        de la base de datos sin abrir ventanas de OpenCV
        """
        print("\n" + "=" * 70)
        print("ENTRENAMIENTO DEL MODELO DE RECONOCIMIENTO")
        print("=" * 70)

        print("\nAnalizando base de datos...")

        # Contar imagenes totales
        total_imagenes = 0
        categorias = {}

        for categoria in ["empleados", "vip", "visitantes"]:
            ruta_categoria = os.path.join(Config.DATABASE_DIR, categoria)
            if os.path.exists(ruta_categoria):
                personas = os.listdir(ruta_categoria)
                num_imagenes = sum(
                    len([f for f in os.listdir(os.path.join(ruta_categoria, p)) if f.endswith((".jpg", ".png"))])
                    for p in personas
                    if os.path.isdir(os.path.join(ruta_categoria, p))
                )
                categorias[categoria] = num_imagenes
                total_imagenes += num_imagenes

        print("\nImagenes encontradas:")
        for cat, num in categorias.items():
            print(f"  - {cat.capitalize()}: {num} imagenes")
        print(f"\nTotal: {total_imagenes} imagenes\n")

        if total_imagenes == 0:
            print("ERROR: No hay imagenes en la base de datos")
            print("Primero captura algunas personas usando la opcion 1 del menu")
            input("\nPresiona ENTER para continuar...")
            return

        # Confirmar entrenamiento
        print("El entrenamiento procesara todas las imagenes y puede tardar varios minutos.")
        confirmacion = input("\nDeseas continuar? (s/n): ")

        if confirmacion.lower() != "s":
            print("\nEntrenamiento cancelado")
            input("\nPresiona ENTER para continuar...")
            return

        print("\n" + "-" * 70)
        print("INICIANDO ENTRENAMIENTO...")
        print("-" * 70 + "\n")

        try:
            from deepface import DeepFace

            # Procesar cada categoria
            imagenes_procesadas = 0
            errores = 0

            for categoria in ["empleados", "vip", "visitantes"]:
                ruta_categoria = os.path.join(Config.DATABASE_DIR, categoria)
                if not os.path.exists(ruta_categoria):
                    continue

                print(f"\nProcesando categoria: {categoria.upper()}")
                personas = [
                    p
                    for p in os.listdir(ruta_categoria)
                    if os.path.isdir(os.path.join(ruta_categoria, p))
                ]

                for persona in personas:
                    ruta_persona = os.path.join(ruta_categoria, persona)
                    imagenes = [f for f in os.listdir(ruta_persona) if f.endswith((".jpg", ".png"))]

                    print(f"  - {persona}: {len(imagenes)} imagenes", end=" ")

                    for imagen in imagenes:
                        ruta_imagen = os.path.join(ruta_persona, imagen)
                        try:
                            # DeepFace generara y cacheara las representaciones
                            DeepFace.represent(
                                img_path=ruta_imagen,
                                model_name=Config.MODELO_FACIAL,
                                detector_backend=Config.DETECTOR_BACKEND,
                                enforce_detection=False,
                            )
                            imagenes_procesadas += 1
                        except Exception:
                            errores += 1

                    print("[OK]")

            print("\n" + "-" * 70)
            print("ENTRENAMIENTO COMPLETADO")
            print("-" * 70)
            print(f"\nImagenes procesadas exitosamente: {imagenes_procesadas}")
            print(f"Errores: {errores}")

            if imagenes_procesadas > 0:
                print("\nEl modelo esta listo para usar en reconocimiento en tiempo real")
            else:
                print("\nADVERTENCIA: No se pudo procesar ninguna imagen")

        except Exception as e:
            print(f"\n\nERROR durante el entrenamiento: {e}")
            import traceback

            traceback.print_exc()

        input("\nPresiona ENTER para volver al menu principal...")

    def ejecutar(self):
        """
        Ejecuta el bucle principal de la aplicacion
        """
        while True:
            opcion = self.mostrar_menu_principal()

            if opcion == 1:
                # Capturar dataset
                self.menu_captura_dataset()

            elif opcion == 2:
                # Entrenar modelo
                self.menu_entrenar_modelo()

            elif opcion == 3:
                # Reconocimiento facial
                self.reconocimiento_tiempo_real()

            elif opcion == 4 or opcion == 0:
                # Salir
                print("\nCerrando aplicacion...")
                print("Hasta luego!\n")
                break


def main():
    """
    Funcion principal
    """
    try:
        app = AplicacionFaceGuard()
        app.ejecutar()
    except Exception as e:
        print(f"\nError fatal: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
