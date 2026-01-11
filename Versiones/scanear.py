import sqlite3
import os

def generar_reporte():
    # --- CONFIGURACIÓN ---
    carpeta_objetivo = 'Versiones' 
    # ---------------------

    if not os.path.exists(carpeta_objetivo):
        print(f"❌ No veo la carpeta '{carpeta_objetivo}'.")
        print(f"Lo que veo aquí es: {os.listdir('.')}")
        return

    # Buscamos archivos dentro de esa carpeta
    archivos = [f for f in os.listdir(carpeta_objetivo) if 'sql' in f.lower() or f.lower().endswith('.db')]
    
    if not archivos:
        print(f"❌ Carpeta '{carpeta_objetivo}' encontrada, pero está vacía o no tiene archivos .sqlite3")
        return

    with open("REPORTE_ESTRUCTURA.txt", "w", encoding="utf-8") as reporte:
        reporte.write(f"=== REPORTE DE ESTRUCTURA (Carpeta: {carpeta_objetivo}) ===\n\n")
        
        for nombre_archivo in archivos:
            ruta_completa = os.path.join(carpeta_objetivo, nombre_archivo)
            reporte.write(f"NOMBRE DEL ARCHIVO: {nombre_archivo}\n")
            
            try:
                conn = sqlite3.connect(ruta_completa)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tablas = cursor.fetchall()
                
                for tabla in tablas:
                    nombre_tabla = tabla[0]
                    reporte.write(f"  TABLA: {nombre_tabla}\n")
                    cursor.execute(f"PRAGMA table_info('{nombre_tabla}');")
                    columnas = cursor.fetchall()
                    for col in columnas:
                        reporte.write(f"    - {col[1]} ({col[2]})\n")
                    reporte.write("  " + "-"*20 + "\n")
                conn.close()
            except Exception as e:
                reporte.write(f"  ERROR: {e}\n")
            
            reporte.write("\n" + "="*40 + "\n\n")
            
    print(f"✅ ¡Hecho! Revisa el archivo 'REPORTE_ESTRUCTURA.txt' que se creó afuera.")

if __name__ == "__main__":
    generar_reporte()