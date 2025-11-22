"""
Script mejorado para renombrar archivos con timestamps
"""
import os
import shutil
from pathlib import Path

# Configuración manual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')

def listar_archivos():
    """Primero lista qué archivos hay"""
    print("🔍 Verificando archivos en database...\n")
    
    for carpeta in ['empleados', 'vip', 'visitantes']:
        ruta_carpeta = os.path.join(DATABASE_DIR, carpeta)
        print(f"📁 {carpeta}: {ruta_carpeta}")
        
        if os.path.exists(ruta_carpeta):
            archivos = os.listdir(ruta_carpeta)
            print(f"   Archivos encontrados: {len(archivos)}")
            for archivo in archivos[:5]:  # Mostrar solo los primeros 5
                print(f"   - {archivo}")
            if len(archivos) > 5:
                print(f"   ... y {len(archivos) - 5} más")
        else:
            print(f"   ⚠️  Carpeta no existe")
        print()

def renombrar_archivos():
    """
    Renombra todos los archivos quitando timestamps
    """
    print("\n🔧 Iniciando renombrado...\n")
    
    total_renombrados = 0
    
    for carpeta in ['empleados', 'vip', 'visitantes']:
        ruta_carpeta = os.path.join(DATABASE_DIR, carpeta)
        
        if not os.path.exists(ruta_carpeta):
            print(f"⚠️  Carpeta no existe: {carpeta}")
            continue
        
        print(f"📁 Procesando: {carpeta}")
        
        archivos = [f for f in os.listdir(ruta_carpeta) 
                   if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if not archivos:
            print(f"   No hay imágenes\n")
            continue
        
        print(f"   Archivos encontrados: {len(archivos)}")
        
        # Procesar cada archivo
        archivos_por_nombre = {}
        
        for archivo in archivos:
            ruta_actual = os.path.join(ruta_carpeta, archivo)
            
            # Extraer extensión
            nombre_sin_ext, extension = os.path.splitext(archivo)
            
            # Dividir por guion bajo
            partes = nombre_sin_ext.split('_')
            
            # Extraer solo el nombre (antes del primer número de 8+ dígitos)
            nombre_limpio = []
            for parte in partes:
                # Si es un número largo (timestamp), detenerse
                if parte.isdigit() and len(parte) >= 8:
                    break
                nombre_limpio.append(parte)
            
            # Construir nuevo nombre base
            if nombre_limpio:
                nuevo_nombre_base = '_'.join(nombre_limpio)
            else:
                nuevo_nombre_base = partes[0]
            
            # Manejar duplicados
            if nuevo_nombre_base not in archivos_por_nombre:
                archivos_por_nombre[nuevo_nombre_base] = 0
                nuevo_nombre = f"{nuevo_nombre_base}{extension}"
            else:
                archivos_por_nombre[nuevo_nombre_base] += 1
                nuevo_nombre = f"{nuevo_nombre_base}_{archivos_por_nombre[nuevo_nombre_base]}{extension}"
            
            ruta_nueva = os.path.join(ruta_carpeta, nuevo_nombre)
            
            # Renombrar
            if ruta_actual != ruta_nueva:
                # Verificar si el destino ya existe
                contador = 1
                while os.path.exists(ruta_nueva) and ruta_nueva != ruta_actual:
                    nuevo_nombre = f"{nuevo_nombre_base}_{contador}{extension}"
                    ruta_nueva = os.path.join(ruta_carpeta, nuevo_nombre)
                    contador += 1
                
                try:
                    shutil.move(ruta_actual, ruta_nueva)
                    print(f"   ✓ {archivo} → {nuevo_nombre}")
                    total_renombrados += 1
                except Exception as e:
                    print(f"   ❌ Error con {archivo}: {e}")
            else:
                print(f"   ⏭️  {archivo} (ya tiene nombre correcto)")
        
        print(f"   Renombrados: {len(archivos_por_nombre)}\n")
    
    print(f"\n✅ Total renombrados: {total_renombrados}")
    
    # Sugerencia
    if total_renombrados > 0:
        print("\n💡 RECOMENDACIÓN:")
        print("   Si tienes múltiples fotos de la misma persona (Carlos_1, Carlos_2, etc.),")
        print("   considera dejar SOLO UNA foto por persona para mejorar el rendimiento.")

def main():
    print("="*70)
    print("🔧 RENOMBRADOR DE ARCHIVOS - Sistema de Reconocimiento Facial")
    print("="*70 + "\n")
    
    # Primero listar
    listar_archivos()
    
    # Preguntar confirmación
    respuesta = input("¿Deseas proceder con el renombrado? (s/n): ").lower()
    
    if respuesta == 's':
        renombrar_archivos()
    else:
        print("\n❌ Operación cancelada")

if __name__ == "__main__":
    main()