# metadata_state.py

import json
import re
from schema_loader import HealthDCATAPSchema
import yaml
from assistant.rag_helper import FIELD_INDEX

class MetadataState:
    """
    Mantiene el estado acumulado de los metadatos HealthDCAT-AP
    durante la conversación por bloques.
    """
    def __init__(self, schema_path="health_dcat_ap.yaml"):
        # Cargar esquema crudo
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = yaml.safe_load(f)

        # Cargar reglas generadas desde HealthDCATAPSchema
        self.restrictions = HealthDCATAPSchema(schema_path).extract_restrictions()

        # Estado final del dataset
        self.data = {}

    # -------------------------------------------------------------
    # FUSIÓN DE DATOS PARCIALES. Se unen bloques
    # -------------------------------------------------------------
    def merge_partial(self, partial):
        for key, value in partial.items():

            # Si llega un valor válido, lo guardamos
            if value is not None:
                self.data[key] = value

            # Si no llega valor y el campo no existe, lo creamos vacío
            elif key not in self.data:
                self.data[key] = None
    # -------------------------------------------------------------
    # CAMPOS OBLIGATORIOS
    # -------------------------------------------------------------
    def required_fields(self):
        """
        Devuelve una lista con los nombres de los campos
        que son obligatorios, basándose en FIELD_INDEX.
        """
        return [
            key for key, info in FIELD_INDEX.items()
            if info.get("obligatorio", False)
        ]


    def missing_required(self):
        missing = []
        format_errors = self.validate_types_basic()

        for field_name in self.required_fields():
            val = self.data.get(field_name)
            # si es vacío:
            if val in (None, "", [], {}):
                missing.append(field_name)
                continue
            # error de formato:
            if any(f"[{field_name}]" in err for err in format_errors):
                missing.append(field_name)
        return missing

    # -------------------------------------------------------------
    # VALIDACIONES BASADAS EN SCHEMA
    # -------------------------------------------------------------
    def validate_types_basic(self):
        errors = []
        obligatorios = set(self.required_fields())

        def _tag(f):
            return "[OBLIG]" if f in obligatorios else "[OPT]"

        for field, value in self.data.items():

            rule = self.restrictions.get(field)
            if rule is None:
                continue

            field_type = rule["type"]
            tag = _tag(field)

            # Obligatorio
            if rule.get("required") and value in (None, "", [], {}):
                errors.append(f"{tag} {field} es obligatorio.")
                continue

            # Lista
            if field_type == "list":
                if value is not None and not isinstance(value, list):
                    errors.append(f"{tag} {field} debe ser una lista.")

            # Email
            if field_type == "email" and value:
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
                    errors.append(f"{tag} {field} debe ser un email válido.")

            # URL
            if field_type == "url" and value:
                if not value.startswith(("http://", "https://")):
                    errors.append(f"{tag} {field} debe ser una URL válida.")

            # Slug
            if field_type == "slug" and value:
                if not re.match(r"^[a-z0-9\-]+$", value):
                    errors.append(f"{tag} {field} debe ser un slug válido.")

            # Lista de objetos
            if field_type == "list_object" and value:
                if not isinstance(value, (list, dict)):
                    errors.append(f"{tag} {field} debe tener completados todos los campos.")
                    continue

                items = value if isinstance(value, list) else [value]
                for i, obj in enumerate(items):
                    if not isinstance(obj, dict):
                        errors.append(f"{tag} {field}[{i}] debe tener completados todos los campos.")
                        continue

                    for subfield, subtype in rule["subfields"].items():
                        subvalue = obj.get(subfield)

                        if not subvalue:
                            continue

                        sf_label = rule.get("subfield_labels", {}).get(subfield, subfield)
                        sf_required = rule.get("subfield_required", {}).get(subfield, False)
                        sf_tag = "[OBLIG]" if sf_required else "[OPT]"

                        if subtype == "email" and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", subvalue):
                            errors.append(f"{sf_tag} [{field}] {sf_label} debe ser un email válido.")

                        if subtype == "url" and not re.match(r"^https?://[^\s/]+\.[^\s/]+", subvalue):
                            errors.append(f"{sf_tag} [{field}] {sf_label} debe ser una URL válida.")
                        
                        if subtype == "telephone" and subvalue:
                            digits_only = re.sub(r"[^\d]", "", subvalue)
                            if not re.match(r"^[\d\s\+\-\(\)]+$", subvalue) or len(digits_only) < 9:
                                errors.append(f"{sf_tag} [{field}] {sf_label} debe ser un teléfono válido.")

        # ── Validación de identifier (DOI) según access_rights ──
        identifier_val = self.data.get("identifier", "")
        access_rights_val = self.data.get("access_rights", "")
        is_non_public = access_rights_val and access_rights_val.rsplit("/", 1)[-1] == "NON_PUBLIC"

        if identifier_val and not is_non_public:
            if not re.match(r'^[^\s"<>]+$', identifier_val):
                label = FIELD_INDEX.get("identifier", {}).get("label", "identifier")
                errors.append(f"{_tag('identifier')} [identifier] {label} debe ser un DOI válido (ej: 10.1234/dataset-salud).")

        return errors