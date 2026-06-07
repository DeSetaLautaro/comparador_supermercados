import requests
import zipfile
from app.core.config import ZIP_PATH, DATA_DIR

def descargar_datos_sepa():
    # URL oficial de la API de datos abiertos (este link simula el origen)
    url_fuente = "https://datos.produccion.gob.ar/dataset/6f47ec76-d1ce-4e34-a7e1-621fe9b1d0b5/resource/91bc072a-4726-44a1-85ec-4a8467aad27e/download/sepa_viernes.zipa-precios-claros.zip"
    
    print("=" * 50)
    print("🤖 ROBOT DESCARGADOR - PRECIOS CLAROS")
    print("=" * 50)
    
    # Aseguramos que la carpeta /data exista en la raíz
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"🌍 Conectándose a la plataforma de Datos Públicos...")
        # Hacemos la petición en modo stream (baja el archivo por pedacitos)
        with requests.get(url_fuente, stream=True, timeout=30) as respuesta:
            respuesta.raise_for_status() # Lanza un error si la web está caída
            
            print("📥 Descargando paquete masivo... (No cierres la terminal)")
            with open(ZIP_PATH, "wb") as archivo_local:
                for bloque in respuesta.iter_content(chunk_size=8192):
                    if bloque: # Filtramos bloques vacíos para mantener limpio el buffer
                        archivo_local.write(bloque)
                        
        print(f"✅ ¡Descarga exitosa! Archivo guardado en: {ZIP_PATH}")
        
        # 🛡️ Control de calidad chiquito: verificar que el ZIP abra bien y no esté dañado
        print("🔍 Verificando integridad del archivo...")
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_test:
            archivos_internos = zip_test.namelist()
            print(f"📦 El ZIP contiene {len(archivos_internos)} archivos listos para procesar.")
            
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN LA DESCARGA: {e}")

if __name__ == "__main__":
    descargar_datos_sepa()