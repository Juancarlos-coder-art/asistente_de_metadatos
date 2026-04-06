# metadata_state.py

import json
import re
from schema_loader import HealthDCATAPSchema

class MetadataState:
    """
    Mantiene el estado acumulado de los metadatos HealthDCAT-AP
    durante la conversación por bloques.
    """

    def __init__(self, schema_path="health_dcat_ap.json"):
        # Cargar esquema crudo
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        # Cargar reglas generadas desde HealthDCATAPSchema
        self.restrictions = HealthDCATAPSchema(schema_path).extract_restrictions()

        # Estado final del dataset
        self.data = {}

    # -------------------------------------------------------------
    # FUSIÓN DE DATOS PARCIALES
    # -------------------------------------------------------------
    def merge_partial(self, partial: dict):
        for key, value in partial.items():
            if value is None:
                self.data.setdefault(key, None)
            else:
                self.data[key] = value

    # -------------------------------------------------------------
    # CAMPOS OBLIGATORIOS
    # -------------------------------------------------------------
    def required_fields(self):
        return [
            f["field_name"]
            for f in self.schema.get("dataset_fields", [])
            if f.get("required")
        ]

    def missing_required(self):
        missing = []
        for field_name in self.required_fields():
            val = self.data.get(field_name)
            if val in (None, "", [], {}):
                missing.append(field_name)
        return missing

    # -------------------------------------------------------------
    # VALIDACIONES BASADAS EN SCHEMA
    # -------------------------------------------------------------
    def validate_types_basic(self):
        errors = []

        for field, value in self.data.items():
            rule = self.restrictions.get(field)
            if not rule:
                continue

            ftype = rule["type"]

            # REQUIRED
            if rule.get("required") and value in (None, "", [], {}):
                errors.append(f"{field} es obligatorio.")

            # LIST
            if ftype == "list" and value is not None:
                if not isinstance(value, list):
                    errors.append(f"{field} debe ser lista.")

            # EMAIL
            if ftype == "email" and value:
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
                    errors.append(f"{field} debe ser email válido.")

            # URL
            if ftype == "url" and value:
                if not (value.startswith("http://") or value.startswith("https://")):
                    errors.append(f"{field} debe ser URL válida.")

            # SLUG
            if ftype == "slug" and value:
                if not re.match(r"^[a-z0-9\-]+$", value):
                    errors.append(f"{field} debe ser un slug válido (minús+guiones).")

            # LIST OBJECT
            if ftype == "list_object" and value:
                if not isinstance(value, list):
                    errors.append(f"{field} debe ser lista de objetos.")
                else:
                    for i, obj in enumerate(value):
                        if not isinstance(obj, dict):
                            errors.append(f"{field}[{i}] debe ser objeto.")
                            continue

                        for sf, stype in rule["subfields"].items():
                            if sf in obj and obj[sf]:
                                if stype == "email" and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", obj[sf]):
                                    errors.append(f"{field}[{i}].{sf} debe ser email válido.")
                                if stype == "url" and not (obj[sf].startswith("http://") or obj[sf].startswith("https://")):
                                    errors.append(f"{field}[{i}].{sf} debe ser URL válida.")

        return errors