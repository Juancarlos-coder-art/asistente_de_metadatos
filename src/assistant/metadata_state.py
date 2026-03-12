# metadata_state.py
# Clase que gestiona el estado completo de los metadatos HealthDCAT-AP
# y realiza validaciones básicas.

import json
import re

class MetadataState:
    """
    Mantiene el estado acumulado de los metadatos HealthDCAT-AP
    durante la conversación por bloques.
    """

    def __init__(self, schema_path="health_dcat_ap.json"):
        with open(schema_path, "r", encoding="utf-8") as f:
            self.schema = json.load(f)

        self.data = {}  # Aquí se acumulan todos los metadatos del usuario/LLM

    # -------------------------------------------------------------
    # FUSIÓN DE DATOS PARCIALES
    # -------------------------------------------------------------
    def merge_partial(self, partial: dict):
        """
        Fusiona un JSON parcial en el estado global.
        Si el parcial trae null, mantiene el valor previo si ya existía.
        """
        for key, value in partial.items():
            if value is None:
                self.data.setdefault(key, None)
            else:
                self.data[key] = value

    # -------------------------------------------------------------
    # CAMPOS OBLIGATORIOS
    # -------------------------------------------------------------
    def required_fields(self):
        """
        Devuelve la lista de campos marcados como 'required' en el esquema.
        """
        required = []
        for field in self.schema.get("dataset_fields", []):
            if field.get("required"):
                required.append(field["field_name"])
        return required

    def missing_required(self):
        """
        Detecta qué campos obligatorios aún no han sido rellenados.
        """
        missing = []
        for field_name in self.required_fields():
            value = self.data.get(field_name)
            if value in (None, "", [], {}):
                missing.append(field_name)
        return missing

    # -------------------------------------------------------------
    # VALIDACIONES BÁSICAS
    # -------------------------------------------------------------
    def validate_types_basic(self):
        """
        Comprobaciones simples:
        - emails con formato válido
        - fechas ISO (AAAA-MM-DD)
        - listas donde deben ser listas
        """
        errors = []

        # validación simple de email
        def is_email(s):
            return bool(re.match(r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", s))

        # -------- validar "contact" ----------
        contact = self.data.get("contact")
        if contact:
            if not isinstance(contact, list):
                errors.append("contact debe ser una lista.")
            else:
                for i, c in enumerate(contact):
                    if not isinstance(c, dict):
                        errors.append(f"contact[{i}] debe ser un objeto.")
                    else:
                        if "email" in c and c["email"]:
                            if not is_email(c["email"]):
                                errors.append(f"contact[{i}].email no es válido.")

        # -------- validar "language" ----------
        language = self.data.get("language")
        if language and not isinstance(language, list):
            errors.append("language debe ser una lista de strings.")

        # -------- validar "temporal_coverage" ----------
        temp_cov = self.data.get("temporal_coverage")
        if temp_cov:
            if not isinstance(temp_cov, list):
                errors.append("temporal_coverage debe ser una lista de objetos.")
            else:
                for i, item in enumerate(temp_cov):
                    if not isinstance(item, dict):
                        errors.append(f"temporal_coverage[{i}] debe ser objeto.")
                        continue

                    for key in ("start", "end"):
                        val = item.get(key)
                        if val:
                            if not re.match(r"^\\d{4}-\\d{2}-\\d{2}$", val):
                                errors.append(
                                    f"temporal_coverage[{i}].{key} debe ser fecha YYYY-MM-DD."
                                )

        return errors