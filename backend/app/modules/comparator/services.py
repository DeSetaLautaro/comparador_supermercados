import duckdb
import pandas as pd
from pathlib import Path
import sys

# ── Resolución de imports propios ────────────────────────────────────────────
ruta_actual = Path(__file__).resolve()
ruta_raiz_backend = ruta_actual.parents[3]
if str(ruta_raiz_backend) not in sys.path:
    sys.path.insert(0, str(ruta_raiz_backend))

from app.core.config import DB_PATH


# ==============================================================================
# CONEXIÓN
# ==============================================================================

def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Devuelve una conexión a DuckDB en modo solo-lectura.

    read_only=True es importante: permite que múltiples consultas
    (ej: varios usuarios en Streamlit) accedan al mismo tiempo
    sin bloquearse entre sí.
    """
    return duckdb.connect(str(DB_PATH), read_only=True)


# ==============================================================================
# 1. BUSCADOR DE PRODUCTOS
# ==============================================================================

def buscar_productos(texto: str, limite: int = 30) -> pd.DataFrame:
    """
    Busca productos cuya descripción contenga el texto ingresado.
    Devuelve una lista de productos únicos (sin duplicados entre cadenas).

    Args:
        texto:  lo que escribe el usuario, ej: "leche entera"
        limite: máximo de resultados a devolver

    Returns:
        DataFrame con columnas: productos_ean, productos_descripcion
    """
    if not texto or not texto.strip():
        return pd.DataFrame(columns=["productos_ean", "productos_descripcion"])

    # ILIKE = case-insensitive LIKE (busca sin importar mayúsculas/minúsculas)
    # El % antes y después significa "cualquier cosa antes y después del texto"
    query = """
        SELECT DISTINCT
            productos_ean,
            productos_descripcion
        FROM precios
        WHERE productos_descripcion ILIKE '%' || ? || '%'
          AND productos_ean IS NOT NULL
        ORDER BY productos_descripcion
        LIMIT ?
    """

    with get_connection() as con:
        resultado = con.execute(query, [texto.strip(), limite]).df()

    return resultado


# ==============================================================================
# 2. COMPARADOR DE CARRITO
# ==============================================================================

def comparar_carrito(lista_eans: list[str]) -> pd.DataFrame:
    """
    Dado un carrito (lista de EANs), calcula el costo total en cada cadena
    de supermercados y devuelve el ranking de más barato a más caro.

    Lógica:
      - Por cada cadena, toma el precio MÍNIMO de cada producto
        entre todas sus sucursales.
      - Solo incluye cadenas que tengan el 100% de los productos del carrito.
      - Ordena de menor a mayor precio total.

    Args:
        lista_eans: lista de códigos EAN, ej: ["7790580005155", "7790040956167"]

    Returns:
        DataFrame con columnas:
            - comercio_bandera_nombre : nombre de la cadena (ej: "Carrefour")
            - total_carrito           : precio total del carrito en esa cadena
            - productos_encontrados   : cuántos productos del carrito tiene
    """
    if not lista_eans:
        return pd.DataFrame()

    # Creamos los placeholders para el IN de SQL: (?, ?, ?)
    placeholders = ", ".join(["?"] * len(lista_eans))
    total_productos = len(lista_eans)

    # La consulta tiene dos partes (CTEs = Common Table Expressions):
    #
    # CTE 1 - "precio_minimo_por_cadena":
    #   Une precios con comercios para saber a qué cadena pertenece cada precio.
    #   Por cada combinación (cadena + producto), se queda con el precio mínimo.
    #
    # CTE 2 - "totales":
    #   Suma esos mínimos por cadena y cuenta cuántos productos encontró.
    #
    # SELECT final:
    #   Filtra solo las cadenas que tienen TODOS los productos del carrito.

    query = f"""
        WITH precio_minimo_por_cadena AS (
            SELECT
                c.comercio_bandera_nombre,
                p.productos_ean,
                MIN(p.productos_precio_lista) AS precio_minimo
            FROM precios p
            JOIN comercios c
                ON p.id_comercio = c.id_comercio
               AND p.id_bandera  = c.id_bandera
            WHERE p.productos_ean         IN ({placeholders})
              AND p.productos_precio_lista  > 0
              AND p.productos_precio_lista IS NOT NULL
            GROUP BY c.comercio_bandera_nombre, p.productos_ean
        ),
        totales AS (
            SELECT
                comercio_bandera_nombre,
                SUM(precio_minimo)          AS total_carrito,
                COUNT(DISTINCT productos_ean) AS productos_encontrados
            FROM precio_minimo_por_cadena
            GROUP BY comercio_bandera_nombre
        )
        SELECT
            comercio_bandera_nombre,
            ROUND(total_carrito, 2)  AS total_carrito,
            productos_encontrados
        FROM totales
        WHERE productos_encontrados = {total_productos}
        ORDER BY total_carrito ASC
    """

    with get_connection() as con:
        resultado = con.execute(query, lista_eans).df()

    return resultado


# ==============================================================================
# 3. DETALLE DE UN PRODUCTO EN TODAS LAS CADENAS
# ==============================================================================

def obtener_detalle_producto(ean: str) -> pd.DataFrame:
    """
    Muestra el precio de un producto específico en cada cadena.
    útil para mostrarle al usuario un desglose dentro del carrito.

    Args:
        ean: código EAN del producto, ej: "7790580005155"

    Returns:
        DataFrame con columnas:
            - comercio_bandera_nombre
            - productos_descripcion
            - precio_minimo   (el mejor precio de esa cadena para ese producto)
    """
    query = """
        SELECT
            c.comercio_bandera_nombre,
            p.productos_descripcion,
            MIN(p.productos_precio_lista) AS precio_minimo
        FROM precios p
        JOIN comercios c
            ON p.id_comercio = c.id_comercio
           AND p.id_bandera  = c.id_bandera
        WHERE p.productos_ean          = ?
          AND p.productos_precio_lista  > 0
          AND p.productos_precio_lista IS NOT NULL
        GROUP BY c.comercio_bandera_nombre, p.productos_descripcion
        ORDER BY precio_minimo ASC
    """

    with get_connection() as con:
        resultado = con.execute(query, [ean]).df()

    return resultado
