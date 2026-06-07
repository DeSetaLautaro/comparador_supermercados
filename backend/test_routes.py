from app.core.config import ROOT_DIR, DATA_DIR, ZIP_PATH, DB_PATH

print("=" * 50)
print("🔍 PROBANDO EL GPS DEL PROYECTO")
print("=" * 50)
print(f"📁 Raíz del proyecto: {ROOT_DIR}")
print(f"📁 Carpeta de datos:  {DATA_DIR}")
print(f"📦 Ruta del ZIP:      {ZIP_PATH}")
print(f"🦆 Ruta de DuckDB:    {DB_PATH}")
print("=" * 50)

# Verificación de seguridad chiquita:
if DATA_DIR.exists():
    print("✅ ¡Espectacular! La carpeta /data ya existe en tu proyecto.")
else:
    print("⚠️  Aviso: La carpeta /data no existe todavía (el script de Python la va a crear sola).")
print("=" * 50)