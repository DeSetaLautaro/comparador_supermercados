# ==============================================================================
# 0. CONFIGURACIÓN E IMPORTS
# ==============================================================================
import zipfile
import pandas as pd
import duckdb
from pathlib import Path
import requests
from pathlib import Path
import sys
import datetime


# 1. Buscamos la ruta absoluta de donde está parado este archivo 'services.py'
ruta_actual = Path(__file__).resolve()

# 2. Viajamos hacia atrás en el árbol de carpetas hasta llegar a la carpeta 'backend'
# Estructura: services.py (actual) -> scrapers -> services -> modules -> app -> backend
ruta_raiz_backend = ruta_actual.parents[3] 

# 3. Le agregamos esa ruta al cerebro de Python si es que no está ya metida
if str(ruta_raiz_backend) not in sys.path:
    sys.path.insert(0, str(ruta_raiz_backend))

# ------------------------------------------------------------------------
# ¡RECIÉN ACÁ HAGO MIS IMPORTS A ARCHIVOS DEL PROYECTO!
# Python ahora va a encontrar 'app' sin importar desde dónde ejecutes.
# ------------------------------------------------------------------------
from app.core.config import ZIP_PATH, DB_PATH


# ==============================================================================
# 1. PASO CERO: DESCARGA EXTERNA
# ==============================================================================

# ──────────────────────────────────────────────────────────────────────────────────────────
# obtener la url según el día de la semana
# ──────────────────────────────────────────────────────────────────────────────────────────

def obtener_url_zip_dinamica() -> str:
    # 1. Armamos un diccionario para pasar del inglés de Python al español de la URL
    dias_semana = {
        "Monday": "lunes",
        "Tuesday": "martes",
        "Wednesday": "miercoles",
        "Thursday": "jueves",
        "Friday": "viernes",
        "Saturday": "sabado",
        "Sunday": "domingo"
    }
    
    dia_ingles = datetime.datetime.today().strftime('%A')
    dia_espanol = dias_semana[dia_ingles]
    
    # 3. 🚀 ¡Tu F-String directo a la vena! Construimos el link exacto de hoy
    url_del_dia = f"https://datos.produccion.gob.ar/dataset/e9ffbef0-c8a3-4d7d-9c50-ae55a2a8f98e/resource/14694559-88b5-4e4a-af83-a57527267828/download/sepa_{dia_espanol}.zip"
    
    print(f"🎯 Día detectado: {dia_espanol.upper()} -> URL generada: {url_del_dia}")
    return url_del_dia


# ──────────────────────────────────────────────────────────────────────────────────────────
# ------------------------------DESCARGAR---------------------------------------------------
# ──────────────────────────────────────────────────────────────────────────────────────────

def descargar_zip_precios(url: str, ruta_destino: Path) -> None:
    """
    Se conecta a internet, descarga el ZIP masivo de Precios Claros
    y lo guarda en la carpeta del proyecto.
    """
    print(f"🌍 Conectándose a: {url}")
    
    # 1. Hacemos la petición a la web (stream=True permite bajar archivos gigantes en pedazos)
    with requests.get(url, stream=True) as respuesta:
        # Verificamos si la página web respondió bien (Código 200 significa OK)
        respuesta.raise_for_status() 
        
        print("📥 Descargando archivo gigante... (esto puede tardar unos minutos)")
        
        # 2. Abrimos el archivo en nuestra computadora para escribir los datos que entran
        with open(ruta_destino, "wb") as f:
            # Leemos el archivo de internet en bloques de 8 KB para no saturar la memoria RAM
            for bloque in respuesta.iter_content(chunk_size=8192):
                f.write(bloque)
                
    print(f"✅ Descarga completada. Archivo guardado en: {ruta_destino}")




# ==============================================================================
# 2. MICRO-EXTRACTORES DE CSV (UN SUPERMERCADO INDIVIDUAL)
# ==============================================================================

# ──────────────────────────────────────────────────────────────────────────────────────────
# Extraer los datos de las sucursales de un super
# ──────────────────────────────────────────────────────────────────────────────────────────
def extraer_datos_de_sucursales(zip_comercio : zipfile.ZipFile) -> pd.DataFrame | None:
    
    df_lista_sucursales_del_comercio = [s for s in zip_comercio.namelist() if "sucursal" in s.lower()]
    
    if not df_lista_sucursales_del_comercio:
                    print(f"  AVISO: No se encontró CSV de sucursales en {zip_comercio}")
                    return None
    
    df_sucursales_del_comercio =df_lista_sucursales_del_comercio[0]
    
    with zip_comercio.open(df_sucursales_del_comercio) as arcivo_virtual:
        
        df_sucursales_del_comercio = pd.read_csv(arcivo_virtual, sep ="|",
                                                 dtype={
                                                     'id_comercio' : str, 
                                                      'id_bandera': str, 
                                                      'id_sucursal': str,
                                                      'sucursales_numero': str
                                                 })
        
        columnas_utiles = ['id_comercio', 'id_bandera', 'id_sucursal', 'sucursales_nombre',
       'sucursales_tipo', 'sucursales_calle', 'sucursales_numero']
       
       # normalización de columnas del dataframe
        df_sucursales_del_comercio.columns = df_sucursales_del_comercio.columns.str.strip().str.lower()
        
        columnas_df = [c for c in columnas_utiles if c in df_sucursales_del_comercio.columns]
        df_sucursales_del_comercio = df_sucursales_del_comercio[columnas_df].copy()
        
        
    return df_sucursales_del_comercio
    
# ──────────────────────────────────────────────────────────────────────────────────────────
# Extraer los datos del comercio de un super
# ──────────────────────────────────────────────────────────────────────────────────────────
def extraer_datos_del_comercio(zip_comercio : zipfile.ZipFile) -> pd.DataFrame | None:
    
    lista_datos_comercio = [c for c in zip_comercio.namelist() if "comercio" in c.lower() and not "sucursal" in c.lower()]
    
    if not lista_datos_comercio:
                    print(f"  AVISO: No se encontró CSV de comercio en {zip_comercio}")
                    return None
    
    datos_comercio = lista_datos_comercio[0]
    
    with zip_comercio.open(datos_comercio) as arcivo_virtual:
        df_comercio = pd.read_csv(arcivo_virtual, sep ="|", dtype={
            'id_comercio' : str, 
            'id_bandera'  : str
        })
        
        
    return df_comercio

# ──────────────────────────────────────────────────────────────────────────────────────────
# Extraer los datos útiles de la tabla "Productos" de un super
# ──────────────────────────────────────────────────────────────────────────────────────────

def extraer_precios_del_comercio(zip_comercio: zipfile.ZipFile) -> pd.DataFrame:
    
    lista_precio_comercios = [p for p in zip_comercio.namelist() if "productos" in p.lower()]
    
    if not lista_precio_comercios:
                    print(f"  AVISO: No se encontró CSV de productos en {zip_comercio}")
                    return None
    
    precio_comercios = lista_precio_comercios[0]
    
    with zip_comercio.open(precio_comercios) as arcivo_virtual:
        
        df_precios = pd.read_csv(arcivo_virtual, sep= "|",
                                 dtype={
                            "id_comercio": str,
                            "id_bandera": str,
                            "id_sucursal": str,
                            "id_producto": str,
                            "productos_ean": str,
                        })
        df_precios.columns = df_precios.columns.str.strip().str.lower()
        
        columnas_utiles = [
            "productos_ean",
            "id_comercio",
            "id_bandera",
            "id_sucursal",
            "productos_precio_lista",
            "productos_precio_referencia",
            "productos_descripcion",
            "productos_precio_unitario_promo1",
            "productos_precio_unitario_promo2"
        ]
        
        columnas_presentes = [c for c in columnas_utiles if c in df_precios.columns]
        df_precios = df_precios[columnas_presentes].copy()
    return df_precios


# ==============================================================================
# 3. ACUMULADOR GENERAL (EL BUCLE MAMUSHKA RECURSIVO)
# ==============================================================================

def extraer_todos_los_zips(zip_principal : zipfile.ZipFile) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:

    lista_comercios = []
    lista_sucursales = []
    lista_productos = []
    lista_zips_internos = [z for z in zip_principal.namelist() if z.endswith(".zip")]
    
    if not lista_zips_internos:
        print (f"No se encontraron archivos zip en {zip_principal}")
        return None
    
    for i in range(0, len(lista_zips_internos)):
    
        with zip_principal.open(lista_zips_internos[i]) as carpeta_virtual:
            zip_super_individual = zipfile.ZipFile(carpeta_virtual)  
            df_comercio = extraer_datos_del_comercio(zip_super_individual)
            df_sucur = extraer_datos_de_sucursales(zip_super_individual)
            df_productos = extraer_precios_del_comercio(zip_super_individual)
        
            lista_comercios.append(df_comercio)
            lista_sucursales.append(df_sucur)
            lista_productos.append(df_productos)
        
    df_comercios_acumulados = pd.concat(lista_comercios, ignore_index=True) 
    df_sucursales_acumuladas = pd.concat(lista_sucursales, ignore_index=True)
    df_productos_acumulados = pd.concat(lista_productos, ignore_index=True)   
        
    return df_comercios_acumulados, df_sucursales_acumuladas, df_productos_acumulados

# ==============================================================================
# 4. PERSISTENCIA EN ALMACENAMIENTO COLUMNAR (DUCKDB)
# ==============================================================================
 

def guardar_en_duckdb(df_comercios: pd.DataFrame, df_sucursales: pd.DataFrame, df_precios: pd.DataFrame) -> None:
    """
    Guarda los tres DataFrames maestros en DuckDB de forma eficiente, limpia y optimizada.
    """
    # Creamos la carpeta contenedora si no existe de forma segura
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"⏳ Conectando a la base de datos en: {DB_PATH}...")
    con = duckdb.connect(str(DB_PATH))
    
    try:
        print("💾 Escribiendo tablas en DuckDB de forma nativa...")
        # DuckDB mapea directo las variables df_comercios, df_sucursales y df_precios de la RAM
        con.execute("CREATE OR REPLACE TABLE comercios AS SELECT * FROM df_comercios")
        con.execute("CREATE OR REPLACE TABLE sucursales AS SELECT * FROM df_sucursales")
        con.execute("CREATE OR REPLACE TABLE precios AS SELECT * FROM df_precios")
        
        # OPTIMIZACIÓN
        print("⚡ Creando índices analíticos para búsquedas instantáneas...")
        con.execute("CREATE INDEX IF NOT EXISTS idx_precios_ean ON precios (productos_ean)")
        
        print(f"🚀 ¡Base de datos optimizada y guardada con éxito!")
        
    except Exception as e:
        print(f"❌ Error crítico al guardar en DuckDB: {e}")
        
    finally:
        con.close()
        print("🔒 Conexión cerrada de forma segura.")
        
        
        
# ==============================================================================
# 5. ORQUESTADOR PRINCIPAL DEL ETL
# ==============================================================================

def correr_etl(zip_path: Path = ZIP_PATH) -> None:
    """
    Función principal del ETL. Orquesta todos los pasos:
      1. Abre el ZIP principal
      2. Extrae comercios y productos (tablas maestras)
      3. Extrae precios de cada supermercado
      4. Guarda todo en DuckDB

    Se puede llamar diariamente para mantener los datos actualizados.
    """
    print("=" * 50)
    print("Iniciando ETL de SEPA - Precios Claros")
    print("=" * 50)
    
    
    URL_OFICIAL_SEPA = obtener_url_zip_dinamica()
    

    descargar_zip_precios(URL_OFICIAL_SEPA, ZIP_PATH)
    
    
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_principal:
        print("\n[1-3/4] Extrayendo y acumulando todos los comercios, sucursales y precios en la RAM...")
        
        resultado = extraer_todos_los_zips(zip_principal)
        
        if resultado is None:
            print("❌ ERROR: El motor de extracción devolvió None.")
            return
        
        df_comercios_acumulados, df_sucursales_acumuladas, df_productos_acumulados = resultado
    
    print("\n[4/4] Guardando en DuckDB...")
    guardar_en_duckdb(df_comercios_acumulados, df_sucursales_acumuladas, df_productos_acumulados
)
    
    print("\n" + "=" * 50)
    print("ETL finalizado correctamente.")
    print("=" * 50)
    
    # LIMPIEZA. Borramos el archivo zip
    print("\n🧹 Limpiando archivos temporales...")
    if zip_path.exists():
        zip_path.unlink() 
        print("🗑️ Archivo ZIP eliminado correctamente para liberar espacio.")
    
    print("\n" + "=" * 50)
    print("ETL finalizado correctamente. ¡Pipeline 100% optimizado!")
    print("=" * 50)
    
    
# ==============================================================================
# 6. DISPARADOR DE CONSOLA
# ==============================================================================
if __name__ == "__main__":
    correr_etl()