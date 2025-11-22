"""
Diagnóstico del sistema
"""
import os
from config import Config
from utils import extraer_nombre_archivo

Config.init_app()

print("="*70)
print("🔍 DIAGNÓSTICO DEL SISTEMA")
print("="*70 + "\n")

print("📁 Estructura de carpetas:")
print(f"  DATABASE_DIR: {Config.DATABASE_DIR}")
print(f"  Existe: {os.path.exists(Config.DATABASE_DIR)}\n")

for rol in Config.ROLES.keys():
    carpeta = os.path.join(Config.DATABASE_DIR, rol)
    print(f"📂 {rol}:")
    print(f"   Ruta: {carpeta}")
    print(f"   Existe: {os.path.exists(carpeta)}")
    
    if os.path.exists(carpeta):
        archivos = [f for f in os.listdir(carpeta) if f.endswith(('.jpg', '.jpeg', '.png'))]
        print(f"   Archivos de imagen: {len(archivos)}")
        
        if archivos:
            print(f"   Ejemplos:")
            for archivo in archivos[:3]:
                nombre_extraido = extraer_nombre_archivo(archivo)
                print(f"     • {archivo}")
                print(f"       → Nombre extraído: '{nombre_extraido}'")
        
        # Buscar archivos de caché
        cache_files = [f for f in os.listdir(carpeta) if f.endswith('.pkl')]
        if cache_files:
            print(f"   ⚠️  Archivos de caché encontrados: {cache_files}")
    
    print()

print("="*70)
print("\n💡 Si hay archivos .pkl (caché), elimínalos y vuelve a ejecutar")