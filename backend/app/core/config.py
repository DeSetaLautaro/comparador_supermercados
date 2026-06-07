from pathlib import Path

# ─────────────────────────────────────────────
# Rutas base del proyecto
# ─────────────────────────────────────────────

# Carpeta raíz del proyecto (dos niveles arriba de este archivo)
ROOT_DIR = Path(__file__).resolve().parents[3]

# Carpeta donde se guarda el ZIP descargado de datos.gob.ar
DATA_DIR = ROOT_DIR / "data"

# Ruta del archivo ZIP principal de SEPA
ZIP_PATH = DATA_DIR / "sepa_viernes.zip"

# Ruta de la base de datos DuckDB (se crea sola si no existe)
DB_PATH = DATA_DIR / "sepa.db"
