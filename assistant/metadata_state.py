# metadata_state.py

import json
import re
from schema_loader import HealthDCATAPSchema
import yaml
ACTIVE_FIELDS = {"Título","Identificador", "Descripción", "Derechos_de_Acceso", "Organismo_a_los_datos_sanitarios"}
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
        que son obligatorios y están activos.
        """

        required = []

        # Recorremos todos los campos definidos en el esquema
        for field in self.schema.get("dataset_fields", []):

            # Obtenemos el nombre del campo
            field_name = field.get("field_name")

            # Comprobamos si el campo es obligatorio
            is_required = field.get("required", False)

            # Comprobamos si el campo está activo
            is_active = field_name in ACTIVE_FIELDS

            # Solo si cumple ambas condiciones, lo añadimos
            if is_required and is_active:
                required.append(field_name)

        # Devolvemos la lista final
        return required


    def missing_required(self):
        errors = []
        for field, value in self.data.items():
            if field not in ACTIVE_FIELDS:  # ignorar campos fuera del scope
                continue
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
            if rule is None:
                continue

            field_type = rule["type"]

            # Obligatorio
            if rule.get("required") and value in (None, "", [], {}):
                errors.append(f"{field} es obligatorio.")
                continue

            # Lista
            if field_type == "list":
                if value is not None and not isinstance(value, list):
                    errors.append(f"{field} debe ser una lista.")

            # Email
            if field_type == "email" and value:
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
                    errors.append(f"{field} debe ser un email válido.")

            # URL
            if field_type == "url" and value:
                if not value.startswith(("http://", "https://")):
                    errors.append(f"{field} debe ser una URL válida.")

            # Slug
            if field_type == "slug" and value:
                if not re.match(r"^[a-z0-9\-]+$", value):
                    errors.append(f"{field} debe ser un slug válido.")

            # Lista de objetos
            if field_type == "list_object" and value:
                if not isinstance(value, list):
                    errors.append(f"{field} debe ser una lista.")
                    continue

                for i, obj in enumerate(value):
                    if not isinstance(obj, dict):
                        errors.append(f"{field}[{i}] deben de rellenarse todos los campos.")
                        continue

                    for subfield, subtype in rule["subfields"].items():
                        subvalue = obj.get(subfield)

                        if not subvalue:
                            continue

                        if subtype == "email" and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", subvalue):
                            errors.append(f"{field}[{i}].{subfield} debe ser email válido.")

                        if subtype == "url" and not subvalue.startswith(("http://", "https://")):
                            errors.append(f"{field}[{i}].{subfield} debe ser URL válida.")

        return errors