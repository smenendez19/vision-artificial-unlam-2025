"""
FACEGUARD - Sistema de Reconocimiento Facial
"""

import os
import sys
import threading
from datetime import datetime

import cv2
import numpy as np
from config import Config
from datasets.capturador import CapturadorDataset
from modules.reconocimiento import SistemaReconocimiento
from utils.alert_logger import AlertLogger
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
        print("\n" + "=" * 70)
        print("FACEGUARD - Sistema de Reconocimiento Facial")
        print("=" * 70 + "\n")

        Config.init_app()

        self.frame_count = 0
        self.detecciones_sesion = []
        self.alertas_sesion = []
        self.alert_logger = AlertLogger()
        self.desconocidos_guardados = set()

        self.processing_thread = None
        self.thread_activo = False
        self.frame_a_procesar = None
        self.resultado_listo = None
        self.lock = threading.Lock()

    def mostrar_menu_principal(self):
        """
        Muestra el menu principal y retorna la seleccion

        Returns:
            int: Opcion seleccionada (1-3) o 0 para salir
        """
        # Crear frame negro para el menu
        frame = np.ones((720, 1280, 3), dtype="uint8") * 255

        opciones = ["Capturar nuevo dataset de persona", "Entrenar modelo de reconocimiento", "Reconocimiento facial en tiempo real", "Salir"]

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
        cv2.putText(frame, "FACEGUARD - Sistema de Reconocimiento - SECTOR A", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

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

        analysis_text = alerta["analysis"] if alerta["tipo_alerta"] == "critico" else ""
        persona_text = f"Persona: {alerta['nombre']} {analysis_text}"
        cv2.putText(frame, persona_text, (70, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(frame, f"Rol: {alerta['rol']}", (70, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    def guardar_screenshot(self, deteccion):
        if deteccion.get("nombre") == "Desconocido":
            det_id = f"{deteccion['bbox']['x']}_{deteccion['bbox']['y']}_{self.frame_count}"

            if det_id not in self.desconocidos_guardados:
                self.desconocidos_guardados.add(det_id)

                rostro_img = deteccion.get("rostro_img")
                if rostro_img is not None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = os.path.join(Config.TEMP_DIR, f"desconocido_{timestamp}.jpg")
                    cv2.imwrite(filename, rostro_img)
                    print(f"Rostro desconocido guardado: {filename}")

    def guardar_screenshot_manual(self, frame):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(Config.TEMP_DIR, f"screenshot_{timestamp}.jpg")
        cv2.imwrite(filename, frame)
        print(f"\nScreenshot guardado: {filename}")
        return filename

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

    def procesamiento_thread_worker(self, sistema):
        while self.thread_activo:
            with self.lock:
                frame_data = self.frame_a_procesar
                self.frame_a_procesar = None

            if frame_data is not None:
                frame_num, frame = frame_data
                resultado = sistema.procesar_frame(frame)

                with self.lock:
                    self.resultado_listo = (frame_num, resultado)
            else:
                threading.Event().wait(0.01)

    def reconocimiento_tiempo_real(self):
        print("\n" + "=" * 70)
        print("RECONOCIMIENTO FACIAL EN TIEMPO REAL")
        print("=" * 70 + "\n")

        if self.thread_activo:
            print("Ya hay una sesión de reconocimiento activa")
            input("\nPresiona ENTER para volver al menu principal...")
            return

        sistema = SistemaReconocimiento()

        print("Sistema inicializado correctamente")
        print(f"Personas registradas: {len(sistema.roles_cache)}")
        print(f"Modelo: {sistema.model_name}")
        print(f"Detector: {sistema.detector_backend}\n")

        if not sistema.iniciar_camara():
            print("Error: No se pudo iniciar la camara")
            input("\nPresiona ENTER para volver al menu principal...")
            return

        print("Camara iniciada")
        print("\nCONTROLES:")
        print("  - Q: Salir")
        print("  - ESPACIO: Pausar/Reanudar")
        print("  - R: Reiniciar estadisticas")
        print("\nIniciando deteccion...\n")

        self.frame_count = 0
        self.detecciones_sesion = []
        self.alertas_sesion = []
        self.desconocidos_guardados.clear()

        self.thread_activo = True
        self.frame_a_procesar = None
        self.resultado_listo = None

        self.processing_thread = threading.Thread(target=self.procesamiento_thread_worker, args=(sistema,), daemon=True)
        self.processing_thread.start()

        self.alert_logger.log_sesion_inicio()

        pausado = False
        ultima_alerta = None
        frames_desde_alerta = 0
        ultimo_frame_procesado = -1
        detecciones_actuales = []

        try:
            while True:
                if not pausado:
                    frame = sistema.capturar_frame()

                    if frame is None:
                        print("Error capturando frame")
                        break

                    if self.frame_count % Config.PROCESAR_CADA_N_FRAMES == 0:
                        with self.lock:
                            if self.frame_a_procesar is None:
                                self.frame_a_procesar = (self.frame_count, frame.copy())

                    with self.lock:
                        if self.resultado_listo is not None:
                            frame_num, resultado = self.resultado_listo
                            self.resultado_listo = None

                            if frame_num > ultimo_frame_procesado:
                                ultimo_frame_procesado = frame_num
                                detecciones_actuales = resultado["detecciones"]

                                if detecciones_actuales:
                                    self.detecciones_sesion.extend(detecciones_actuales)

                                    print(f"\nFrame {frame_num}:")
                                    for det in detecciones_actuales:
                                        icono = "OK" if det["autorizado"] else "ALERTA"
                                        print(f"  [{icono}] {det['nombre']} - {det['rol']} ({det['confianza']}%)")

                                        if det["autorizado"]:
                                            self.alert_logger.log_deteccion(det)
                                        elif det["nombre"] == "Desconocido":
                                            self.guardar_screenshot(det)

                                    for det in detecciones_actuales:
                                        if det["genera_alerta"]:
                                            ultima_alerta = det
                                            frames_desde_alerta = 0

                                            alerta_info = {
                                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                                "nombre": det["nombre"],
                                                "rol": det["rol"],
                                                "tipo_alerta": det["tipo_alerta"],
                                            }
                                            self.alertas_sesion.append(alerta_info)
                                            self.alert_logger.log_alerta(det)
                                            print(f"\n  ALERTA: {det['nombre']} - {det['tipo_alerta']}")

                    frame = self.dibujar_detecciones(frame, detecciones_actuales)

                    if ultima_alerta and frames_desde_alerta < 60:
                        self.mostrar_alerta(frame, ultima_alerta)
                        frames_desde_alerta += 1

                    frame = self.mostrar_info_pantalla(frame, sistema)
                    self.frame_count += 1

                else:
                    frame = mostrar_mensaje_centro(frame, "PAUSADO - Presiona ESPACIO para continuar", (255, 255, 0))

                cv2.imshow("FaceGuard - Reconocimiento Facial", frame)

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == ord("Q"):
                    print("\nDeteniendo sistema...")
                    break
                elif key == ord(" "):
                    pausado = not pausado
                    estado = "PAUSADO" if pausado else "REANUDADO"
                    print(f"\n{estado}")
                elif key == ord("s") or key == ord("S"):
                    self.guardar_screenshot_manual(frame)
                elif key == ord("r") or key == ord("R"):
                    self.detecciones_sesion = []
                    self.alertas_sesion = []
                    self.frame_count = 0
                    detecciones_actuales = []
                    ultima_alerta = None
                    frames_desde_alerta = 0
                    ultimo_frame_procesado = -1
                    self.desconocidos_guardados.clear()
                    print("\nEstadisticas reiniciadas")

        except KeyboardInterrupt:
            print("\n\nPrograma interrumpido por el usuario")

        finally:
            self.thread_activo = False

            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)

            self.alert_logger.log_sesion_fin(
                {
                    "frames_procesados": self.frame_count,
                    "total_detecciones": len(self.detecciones_sesion),
                    "alertas_generadas": len(self.alertas_sesion),
                }
            )

            sistema.detener_camara()
            cv2.destroyAllWindows()
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
                personas = [p for p in os.listdir(ruta_categoria) if os.path.isdir(os.path.join(ruta_categoria, p))]

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
