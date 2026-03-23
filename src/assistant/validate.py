import requests
import os

API_URL = "https://www.itb.ec.europa.eu/shacl/api/validation/validate"

def validar_shacl(self, ttl_path):
    from assistant.validate import validar_shacl
    from pathlib import Path

    print("\n🧪 Validando mediante SHACL (API Comisión Europea)...")

    # Convertir la ruta del TTL REAL introducida por el usuario
    ttl_path = Path(ttl_path).expanduser().resolve()

    # SUBIR dos niveles /assistant/ → /src/ → /asistente_de_metadatos/
    base_dir = Path(__file__).resolve().parents[3]

    # Ruta REAL del SHACL
    shapes_path = base_dir / "tools" / "shacl" / "shacl_dataset_shape.ttl"

    shapes_path = shapes_path.resolve()

    print(f"📍 TTL (usuario):  {ttl_path}")
    print(f"📍 SHACL:         {shapes_path}")

    # Comprobaciones
    if not ttl_path.exists():
        raise FileNotFoundError(f"❌ EL TTL NO EXISTE: {ttl_path}")

    if not shapes_path.exists():
        raise FileNotFoundError(f"❌ EL SHACL NO EXISTE: {shapes_path}")

    # Llamada al validador oficial
    return validar_shacl(str(ttl_path), str(shapes_path))