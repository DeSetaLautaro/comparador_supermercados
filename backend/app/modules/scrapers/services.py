import zipfile
import pandas as pd
import duckdb
from pathlib import Path
import requests
from pathlib import Path

from app.core.config import ZIP_PATH, DB_PATH


# ─────────────────────────────────────────────
# Paso cero: extraer datos de internet con request
# ─────────────────────────────────────────────



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

# ─────────────────────────────────────────────
# PASO 1 y 2: Extraer comercios y productos (tablas maestras)
# ─────────────────────────────────────────────

def extraer_comercios(zip_principal: zipfile.ZipFile) -> pd.DataFrame:
    """
    Lee el archivo comercio.csv que viene dentro del ZIP principal.
    Devuelve un DataFrame con todos los comercios del país.
    """
    with zip_principal.open("comercio.csv") as f:
        df = pd.read_csv(f, sep="|", dtype=str)  # dtype=str para no perder ceros a la izquierda en los IDs
    
    # Normalizamos nombres de columnas: sin espacios, en minúsculas
    df.columns = df.columns.str.strip().str.lower()
    
    print(f"  Comercios encontrados: {len(df)}")
    return df


def extraer_productos_maestro(zip_principal: zipfile.ZipFile) -> pd.DataFrame:
    """
    Lee el archivo productos.csv que viene dentro del ZIP principal.
    Este es el catálogo general: EAN, descripción, marca.
    """
    with zip_principal.open("productos.csv") as f:
        df = pd.read_csv(f, sep="|", dtype=str)
    
    df.columns = df.columns.str.strip().str.lower()
    
    print(f"  Productos en catálogo: {len(df)}")
    return df


# ─────────────────────────────────────────────
# PASO 3: Extraer precios de cada supermercado
# ─────────────────────────────────────────────

def extraer_precios_de_un_super(zip_principal: zipfile.ZipFile, ruta_zip_interno: str) -> pd.DataFrame | None:
    """
    Dado el ZIP principal y la ruta de un ZIP interno (un supermercado),
    extrae el CSV de precios, estandariza los tipos de datos y devuelve un DataFrame limpio.
    """
    try:
        with zip_principal.open(ruta_zip_interno) as archivo_virtual:
            with zipfile.ZipFile(archivo_virtual) as zip_interno:
                
                archivos_csv = [n for n in zip_interno.namelist() if "productos" in n.lower()]
                
                if not archivos_csv:
                    print(f"  AVISO: No se encontró CSV de productos en {ruta_zip_interno}")
                    return None
                
                with zip_interno.open(archivos_csv[0]) as csv_file:
                    df = pd.read_csv(
                        csv_file,
                        sep="|",
                        dtype={
                            "id_comercio": str,
                            "id_bandera": str,
                            "id_sucursal": str,
                            "id_producto": str,
                            "productos_ean": str,
                        }
                    )
        
        df.columns = df.columns.str.strip().str.lower()
        
        columnas_utiles = [
            "productos_ean",
            "id_comercio",
            "id_bandera",
            "id_sucursal",
            "productos_precio",
        ]
        
        columnas_presentes = [c for c in columnas_utiles if c in df.columns]
        df = df[columnas_presentes].copy() 
        
        # BLINDAJE DE PRECIOS: Convertimos a float y lo que no sea número lo transforma en NaN
        if "productos_precio" in df.columns:
            df["productos_precio"] = pd.to_numeric(df["productos_precio"], errors="coerce")
            # Opcional: Eliminamos filas que se hayan quedado sin precio válido
            df = df.dropna(subset=["productos_precio"])
        
        return df

    except Exception as e:
        print(f"  ERROR procesando {ruta_zip_interno}: {e}")
        return None

    except Exception as e:
        print(f"  ERROR procesando {ruta_zip_interno}: {e}")
        return None


def extraer_todos_los_precios(zip_principal: zipfile.ZipFile) -> pd.DataFrame:
    """
    Itera sobre todos los ZIPs internos del ZIP principal,
    extrae los precios de cada supermercado y los une en un solo DataFrame.
    """
    # Listamos todos los archivos dentro del ZIP principal
    todos_los_archivos = zip_principal.namelist()
    
    # Nos quedamos solo con los que son ZIPs (uno por supermercado)
    zips_internos = [f for f in todos_los_archivos if f.endswith(".zip")]
    
    print(f"  Supermercados encontrados: {len(zips_internos)}")
    
    # Acumulamos los DataFrames de cada supermercado en esta lista
    lista_dataframes = []
    
    for i, ruta_zip in enumerate(zips_internos, start=1):
        print(f"  Procesando {i}/{len(zips_internos)}: {ruta_zip}")
        df_super = extraer_precios_de_un_super(zip_principal, ruta_zip)
        
        if df_super is not None and not df_super.empty:
            lista_dataframes.append(df_super)
    
    if not lista_dataframes:
        raise ValueError("No se pudo extraer ningún dato de precios del ZIP.")
    
    # pd.concat une todos los DataFrames en uno solo (apilando filas)
    df_precios = pd.concat(lista_dataframes, ignore_index=True)
    
    print(f"  Total de registros de precios: {len(df_precios):,}")
    return df_precios


# ─────────────────────────────────────────────
# PASO 4: Guardar todo en DuckDB
# ─────────────────────────────────────────────

def guardar_en_duckdb(df_comercios: pd.DataFrame, df_productos: pd.DataFrame, df_precios: pd.DataFrame) -> None:
    """
    Guarda los tres DataFrames en DuckDB de forma eficiente y limpia.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    con = duckdb.connect(str(DB_PATH))
    
    # Usar el método nativo de DuckDB para registrar dataframes es más rápido y seguro
    print("  Escribiendo tablas en DuckDB de forma nativa...")
    con.execute("CREATE OR REPLACE TABLE comercios AS SELECT * FROM df_comercios")
    con.execute("CREATE OR REPLACE TABLE productos AS SELECT * FROM df_productos")
    con.execute("CREATE OR REPLACE TABLE precios AS SELECT * FROM df_precios")
    
    # ⚡ OPTIMIZACIÓN EXTRA: Creamos un índice en la tabla de precios por EAN
    # Esto va a hacer que cuando busques un producto en tu comparador, la respuesta sea instantánea.
    print("  Creando índices analíticos...")
    con.execute("CREATE INDEX IF NOT EXISTS idx_precios_ean ON precios (productos_ean)")
    
    con.close()
    print(f"  Base de datos optimizada y guardada en: {DB_PATH}")


# ─────────────────────────────────────────────
# Función principal: orquesta todo el proceso ETL
# ─────────────────────────────────────────────

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
    
    if not zip_path.exists():
        URL_OFICIAL_SEPA = "https://datos.produccion.gob.ar/dataset/.../precios.zip" # El link real de donde se baja
    
    ## 🔥 PASO 0: Descarga fresca de internet
     #   print("\n[0/4] Descargando datos actualizados de internet...")
      #  descargar_zip_precios(URL_OFICIAL_SEPA, ZIP_PATH)
    
    # Abrimos el ZIP principal UNA sola vez y lo reutilizamos en todos los pasos
    with zipfile.ZipFile(zip_path, "r") as zip_principal:
        
        print("\n[1/4] Extrayendo comercios...")
        df_comercios = extraer_comercios(zip_principal)
        
        print("\n[2/4] Extrayendo catálogo de productos...")
        df_productos = extraer_productos_maestro(zip_principal)
        
        print("\n[3/4] Extrayendo precios de todos los supermercados...")
        df_precios = extraer_todos_los_precios(zip_principal)
    
    print("\n[4/4] Guardando en DuckDB...")
    guardar_en_duckdb(df_comercios, df_productos, df_precios)
    
    print("\n" + "=" * 50)
    print("ETL finalizado correctamente.")
    print("=" * 50)


# ─────────────────────────────────────────────
# Permite ejecutar el ETL directamente con: python services.py
# ─────────────────────────────────────────────

if __name__ == "__main__":
    correr_etl()
