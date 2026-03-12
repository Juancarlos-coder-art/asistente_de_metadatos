#!/usr/bin/env python3
import requests
import sys
import json
import os

API_URL = "https://www.itb.ec.europa.eu/shacl/api/validation/validate"

def validate(data_path, shapes_path):
    if not os.path.exists(data_path):
        print(f"❌ ERROR: No se encuentra el archivo de datos: {data_path}")
        sys.exit(1)

    if not os.path.exists(shapes_path):
        print(f"❌ ERROR: No se encuentra el archivo de shapes SHACL: {shapes_path}")
        sys.exit(1)

    print("⏳ Validando mediante la API SHACL de la Comisión Europea...")
    print(f"📄 DataGraph:  {data_path}")
    print(f"📐 ShapesGraph: {shapes_path}")
    print("----------------------------------------------------")

    files = {
        "dataGraph": open(data_path, "rb"),
        "shapesGraph": open(shapes_path, "rb")
    }

    try:
        response = requests.post(API_URL, files=files)
    except Exception as e:
        print(f"❌ Error de conexión con la API: {e}")
        sys.exit(1)

    if response.status_code != 200:
        print(f"❌ Error HTTP {response.status_code}: {response.text}")
        sys.exit(1)

    result = response.json()

    print("✔ Resultado recibido:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result.get("conforms", False):
        print("\n🎉 VALIDACIÓN CORRECTA — El dataset cumple con las SHACL")
    else:
        print("\n⚠ VALIDACIÓN FALLIDA — El dataset NO cumple las SHACL")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso:")
        print("  python validate.py <dataset.ttl> <shapes.ttl>")
        sys.exit(1)

    data_file = sys.argv[1]
    shapes_file = sys.argv[2]

    validate(data_file, shapes_file)