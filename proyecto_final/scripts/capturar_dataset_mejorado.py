"""
Sistema de Reconocimiento Facial - Versión Simple (Sin WebSockets)
Solo OpenCV + DeepFace para pruebas locales
"""
import cv2
import os
import sys
from datetime import datetime

# Agregar directorio parent al path para imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar módulos del sistema
from config import Config
from reconocimiento import SistemaReconocimiento


class AplicacionSimple:
    """
    Aplicación de escritorio simple para probar el sistema
    sin necesidad de WebSockets ni servidor
    """
    
    def __init__(self):
        """Inicializar aplicación"""
        print("\n" + "="*70)
        print("🔐 FACEGUARD - Sistema de Reconocimiento Facial (Versión Simple)")
        print("="*70 + "\n")
        
        # Inicializar sistema
        Config.init_app()
        self.sistema = SistemaReconocimiento()
        
        # Estadísticas de sesión
        self.frame_count = 0
        self.detecciones_sesion = []
        self.alertas_sesion = []
        
        # Tracking persistente de detecciones
        self.detecciones_actuales = []  # Detecciones que se muestran en pantalla
        self.frames_sin_actualizacion = 0  # Contador de frames sin procesar
        self.max_frames_persistencia = 30  # Mantener detección por ~3 segundos
        
        # Colores por rol
        self.colores_roles = {
            'Empleado': (0, 255, 0),      # Verde
            'VIP': (255, 215, 0),          # Dorado
            'Visitante': (0, 165, 255),    # Naranja
            'Desconocido': (0, 0, 255)     # Rojo
        }
        
        print("✓ Sistema inicializado correctamente")
        print(f"✓ Personas registradas: {len(self.sistema.roles_cache)}")
        print(f"✓ Modelo: {self.sistema.model_name}")
        print(f"✓ Detector: {self.sistema.detector_backend}\n")
    
    def mostrar_info_pantalla(self, frame):
        """
        Dibuja información en la pantalla
        
        Args:
            frame: Frame de OpenCV
        
        Returns:
            frame: Frame con información dibujada
        """
        altura, ancho = frame.shape[:2]
        
        # Fondo semi-transparente para el panel de info
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (ancho, 140), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Título
        cv2.putText(frame, "FACEGUARD - Sistema de Reconocimiento", 
                   (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # Información
        info_textos = [
            f"Frame: {self.frame_count}",
            f"Personas registradas: {len(self.sistema.roles_cache)}",
            f"Detecciones activas: {len(self.detecciones_actuales)}",
            f"Total detectado: {len(self.detecciones_sesion)}"
        ]
        
        y_pos = 65
        for texto in info_textos:
            cv2.putText(frame, texto, (20, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_pos += 22
        
        # Leyenda de colores (roles)
        leyenda_x = ancho - 350
        leyenda_y = 20
        cv2.putText(frame, "Roles:", 
                   (leyenda_x, leyenda_y + 15), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        roles = [
            ('Empleado', self.colores_roles['Empleado']),
            ('VIP', self.colores_roles['VIP']),
            ('Visitante', self.colores_roles['Visitante']),
            ('Desconocido', self.colores_roles['Desconocido'])
        ]
        
        y_rol = leyenda_y + 35
        for nombre_rol, color in roles:
            # Cuadrado de color
            cv2.rectangle(frame, 
                         (leyenda_x, y_rol - 12), 
                         (leyenda_x + 15, y_rol + 3), 
                         color, -1)
            cv2.rectangle(frame, 
                         (leyenda_x, y_rol - 12), 
                         (leyenda_x + 15, y_rol + 3), 
                         (255, 255, 255), 1)
            
            # Texto del rol
            cv2.putText(frame, nombre_rol, 
                       (leyenda_x + 25, y_rol), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_rol += 20
        
        # Controles
        cv2.putText(frame, "Controles:", 
                   (ancho - 350, altura - 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        controles = [
            "Q - Salir",
            "ESPACIO - Pausar",
            "R - Reiniciar stats",
            "S - Screenshot"
        ]
        
        y_pos = altura - 70
        for control in controles:
            cv2.putText(frame, control, 
                       (ancho - 350, y_pos), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_pos += 20
        
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
            bbox = deteccion['bbox']
            nombre = deteccion['nombre']
            rol = deteccion['rol']
            confianza = deteccion['confianza']
            autorizado = deteccion['autorizado']
            
            x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
            
            # Color según rol
            if autorizado:
                color = self.colores_roles.get(rol, (0, 255, 0))
                color_fondo = tuple(int(c * 0.8) for c in color)
            else:
                color = (0, 0, 255)  # Rojo para desconocidos
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
            
            # Borde del panel con color del rol
            cv2.rectangle(frame, 
                         (x, y_panel), 
                         (x + max(w_texto + 20, 200), y_panel + 75), 
                         color, 3)
            
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
            
            # Icono de estado con color del rol
            centro_icono = (x + w - 30, y + 30)
            if autorizado:
                # Check con color del rol
                cv2.circle(frame, centro_icono, 20, color, -1)
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
    
    def mostrar_alerta(self, frame, alerta):
        """
        Muestra una alerta en pantalla
        
        Args:
            frame: Frame de OpenCV
            alerta: Información de la alerta
        """
        altura, ancho = frame.shape[:2]
        
        # Panel de alerta en la parte superior
        if alerta['tipo_alerta'] == 'critico':
            color_alerta = (0, 0, 255)
            texto_nivel = "ALERTA CRITICA"
        elif alerta['tipo_alerta'] == 'alto':
            color_alerta = (0, 165, 255)
            texto_nivel = "ALERTA ALTA"
        elif alerta['tipo_alerta'] == 'medio':
            color_alerta = (0, 255, 255)
            texto_nivel = "ALERTA MEDIA"
        else:
            color_alerta = (0, 255, 0)
            texto_nivel = "NOTIFICACION"
        
        # Parpadeo para alertas críticas
        if alerta['tipo_alerta'] == 'critico' and self.frame_count % 10 < 5:
            # Fondo de alerta
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 150), (ancho, 250), color_alerta, -1)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        
        # Panel de alerta
        cv2.rectangle(frame, (50, 150), (ancho - 50, 250), color_alerta, 3)
        cv2.rectangle(frame, (50, 150), (ancho - 50, 190), color_alerta, -1)
        
        # Texto de alerta
        cv2.putText(frame, texto_nivel, 
                   (70, 180),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        
        cv2.putText(frame, f"Persona: {alerta['nombre']}", 
                   (70, 215),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(frame, f"Rol: {alerta['rol']}", 
                   (70, 240),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    def guardar_screenshot(self, frame):
        """Guarda un screenshot del frame actual"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"screenshot_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Screenshot guardado: {filename}")
    
    def mostrar_estadisticas_finales(self):
        """Muestra estadísticas al finalizar"""
        print("\n" + "="*70)
        print("📊 ESTADÍSTICAS DE LA SESIÓN")
        print("="*70)
        
        stats = self.sistema.obtener_estadisticas()
        
        print(f"\n🔢 Frames procesados: {self.frame_count}")
        print(f"👥 Total detecciones: {stats['total_detecciones']}")
        print(f"✅ Detecciones exitosas: {stats['detecciones_exitosas']}")
        print(f"⚠️  Alertas generadas: {stats['alertas_generadas']}")
        print(f"📈 Tasa de éxito: {stats['tasa_exito']}%")
        
        if self.detecciones_sesion:
            print(f"\n👤 Personas detectadas en esta sesión:")
            personas_unicas = set([d['nombre'] for d in self.detecciones_sesion])
            for persona in personas_unicas:
                cantidad = sum(1 for d in self.detecciones_sesion if d['nombre'] == persona)
                print(f"  • {persona}: {cantidad} veces")
        
        if self.alertas_sesion:
            print(f"\n🚨 Alertas generadas:")
            for alerta in self.alertas_sesion[-5:]:  # Últimas 5
                print(f"  • {alerta['timestamp']}: {alerta['nombre']} ({alerta['tipo_alerta']})")
        
        print("\n" + "="*70)
    
    def ejecutar(self):
        """Ejecuta la aplicación principal"""
        
        # Iniciar cámara
        if not self.sistema.iniciar_camara():
            print("❌ Error: No se pudo iniciar la cámara")
            return
        
        print("\n📹 Cámara iniciada")
        print("\n⌨️  CONTROLES:")
        print("  • Q - Salir")
        print("  • ESPACIO - Pausar/Reanudar")
        print("  • R - Reiniciar estadísticas")
        print("  • S - Capturar screenshot")
        print("\n🎬 Iniciando detección...\n")
        
        pausado = False
        ultima_alerta = None
        frames_desde_alerta = 0
        
        try:
            while True:
                if not pausado:
                    # Capturar frame
                    frame = self.sistema.capturar_frame()
                    
                    if frame is None:
                        print("❌ Error capturando frame")
                        break
                    
                    # Procesar cada N frames
                    if self.frame_count % Config.PROCESAR_CADA_N_FRAMES == 0:
                        resultado = self.sistema.procesar_frame(frame)
                        
                        # Actualizar detecciones actuales
                        if resultado['detecciones']:
                            self.detecciones_actuales = resultado['detecciones']
                            self.frames_sin_actualizacion = 0
                            
                            # Guardar detecciones en historial
                            self.detecciones_sesion.extend(resultado['detecciones'])
                            
                            # Log en consola (mostrar TODAS las detecciones)
                            print(f"\n📍 Frame {self.frame_count}:")
                            for det in resultado['detecciones']:
                                icono = "✓" if det['autorizado'] else "⚠"
                                print(f"  {icono} {det['nombre']} - {det['rol']} ({det['confianza']:.2f}%)")
                            
                            # Generar alertas
                            for det in resultado['detecciones']:
                                if det['genera_alerta']:
                                    ultima_alerta = det
                                    frames_desde_alerta = 0
                                    self.alertas_sesion.append({
                                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                                        'nombre': det['nombre'],
                                        'rol': det['rol'],
                                        'tipo_alerta': det['tipo_alerta']
                                    })
                                    print(f"  🚨 ALERTA: {det['nombre']} - {det['tipo_alerta']}")
                        else:
                            # No hay detecciones nuevas, incrementar contador
                            self.frames_sin_actualizacion += 1
                            
                            # Si han pasado muchos frames sin detectar, limpiar
                            if self.frames_sin_actualizacion > self.max_frames_persistencia:
                                self.detecciones_actuales = []
                    else:
                        # Frame no procesado, incrementar contador de persistencia
                        self.frames_sin_actualizacion += 1
                        
                        # Limpiar detecciones si no hay actualización reciente
                        if self.frames_sin_actualizacion > self.max_frames_persistencia:
                            self.detecciones_actuales = []
                    
                    # Dibujar detecciones actuales (persistentes)
                    if self.detecciones_actuales:
                        frame = self.dibujar_detecciones(frame, self.detecciones_actuales)
                    
                    # Mostrar alerta si hay una reciente
                    if ultima_alerta and frames_desde_alerta < 100:
                        self.mostrar_alerta(frame, ultima_alerta)
                        frames_desde_alerta += 1
                    
                    # Información en pantalla
                    frame = self.mostrar_info_pantalla(frame)
                    
                    self.frame_count += 1
                
                else:
                    # Mensaje de pausa
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 0), -1)
                    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
                    
                    cv2.putText(frame, "PAUSADO", 
                               (frame.shape[1]//2 - 100, frame.shape[0]//2),
                               cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 4)
                    cv2.putText(frame, "Presiona ESPACIO para continuar", 
                               (frame.shape[1]//2 - 250, frame.shape[0]//2 + 50),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                
                # Mostrar frame
                cv2.imshow('FaceGuard - Sistema de Reconocimiento', frame)
                
                # Controles de teclado
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == ord('Q'):
                    print("\n⏹️  Deteniendo sistema...")
                    break
                elif key == ord(' '):
                    pausado = not pausado
                    estado = "⏸️  PAUSADO" if pausado else "▶️  REANUDADO"
                    print(f"\n{estado}")
                elif key == ord('r') or key == ord('R'):
                    self.detecciones_sesion = []
                    self.alertas_sesion = []
                    self.detecciones_actuales = []
                    self.frame_count = 0
                    print("\n🔄 Estadísticas reiniciadas")
                elif key == ord('s') or key == ord('S'):
                    self.guardar_screenshot(frame)
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Programa interrumpido por el usuario")
        
        finally:
            # Limpiar
            self.sistema.detener_camara()
            cv2.destroyAllWindows()
            
            # Mostrar estadísticas finales
            self.mostrar_estadisticas_finales()
            
            print("\n✅ Sistema detenido correctamente")
            print("👋 ¡Hasta luego!\n")


# ============================================
# PUNTO DE ENTRADA
# ============================================

if __name__ == "__main__":
    try:
        app = AplicacionSimple()
        app.ejecutar()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()