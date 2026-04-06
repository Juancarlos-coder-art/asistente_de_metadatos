import json
import yaml
class HealthDCATAPSchema:
    """
    Cargador y gestor del esquema HealthDCAT-AP.
    Permite que un asistente conversacional utilice automáticamente
    las propiedades definidas en el esquema.
    """

    def __init__(self, schema_path="health_dcat_ap.json"):
        self.schema = self._load_schema(schema_path)
        self.dataset_fields = self.schema.get("dataset_fields", [])
        self.resource_fields = self.schema.get("resource_fields", [])

    # ------------------------------
    # CARGA DEL ESQUEMA
    # ------------------------------
    def _load_schema(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------
    # OBTENER LISTAS DE CAMPOS
    # ------------------------------
    def list_dataset_fields(self):
        return [
            {
                "name": f.get("field_name"),
                "label": f.get("label"),
                "required": f.get("required", False),
                "preset": f.get("preset"),
                "help_text": f.get("help_text")
            }
            for f in self.dataset_fields
        ]

    def list_resource_fields(self):
        return [
            {
                "name": f.get("field_name"),
                "label": f.get("label"),
                "preset": f.get("preset"),
                "help_text": f.get("help_text")
            }
            for f in self.resource_fields
        ]

    # ------------------------------
    # GENERAR PREGUNTA PARA EL ASISTENTE
    # ------------------------------
    def build_question(self, field):
        """
        A partir de un campo del esquema, generar texto de pregunta conversacional.
        """
        name = field.get("name")
        label = field.get("label")
        required = field.get("required", False)
        help_text = field.get("help_text", "")

        pregunta = f"📌 **{label}**"
        if required:
            pregunta += " *(obligatorio)*"

        if help_text:
            pregunta += f"\nℹ️ {help_text}"

        return pregunta

    # ------------------------------
    # GET DETALLE DEL CAMPO
    # ------------------------------
    def get_field(self, field_name):
        for f in self.dataset_fields:
            if f.get("field_name") == field_name:
                return f
        return None

    # ------------------------------
    # CREAR PLANTILLA VACÍA DE METADATOS
    # ------------------------------
    def empty_metadata_template(self):
        """
        Crea una estructura vacía lista para rellenar con valores del usuario.
        """
        return { f["field_name"]: None for f in self.dataset_fields }
    

    # ------------------------------
    # EXTRAER RESTRICCIONES DEL ESQUEMA
    # -----------------------------

    # ------------------------------
    # EXTRAER RESTRICCIONES DEL ESQUEMA
    # ------------------------------
    def extract_restrictions(self):
        import yaml
        restrictions = {}

        # Intentar cargar el YAML completo de HealthDCAT-AP

        try:
            with open("health_dcat_ap.yaml", "r", encoding="utf-8") as f:
                yaml_schema = yaml.safe_load(f)
                print("DEBUG: YAML cargado correctamente")
        except FileNotFoundError:
            print("DEBUG: YAML NO encontrado")
            yaml_schema = {}

        yaml_fields = yaml_schema.get("dataset_fields", [])
        yaml_by_name = { f["field_name"]: f for f in yaml_fields if "field_name" in f }

        # Recorrer los campos del JSON del schema
        for field in self.dataset_fields:

            fname = field["field_name"]
            rule = {
                "required": field.get("required", False),
                "type": "text"
            }

            # ============================
            # 1. REGLAS BASADAS EN EL YAML
            # ============================
            yaml_field = yaml_by_name.get(fname)

            if yaml_field:

                # A. Validators completos (CKAN)
                if "validators" in yaml_field:
                    rule["validators"] = yaml_field["validators"]

                # B. Vocabularios / enumeraciones
                if "choices" in yaml_field:
                    rule["choices"] = [
                        choice["value"] for choice in yaml_field["choices"]
                    ]

                # C. Longitudes
                if "min_length" in yaml_field:
                    rule["min_length"] = yaml_field["min_length"]

                if "max_length" in yaml_field:
                    rule["max_length"] = yaml_field["max_length"]

                # D. Tipos DCAT / DCTerms / schema.org
                if "type" in yaml_field:
                    rule["dcat_type"] = yaml_field["type"]

                # E. Cardinalidad
                if "min_items" in yaml_field:
                    rule["min_items"] = yaml_field["min_items"]

                if "max_items" in yaml_field:
                    rule["max_items"] = yaml_field["max_items"]

                # F. Expresiones regulares
                if "regex" in yaml_field:
                    rule["regex"] = yaml_field["regex"]

            # ============================
            # 2. REGLAS DEL JSON
            # ============================

            preset = field.get("preset")
            if preset == "dataset_slug":
                rule["type"] = "slug"
            elif preset == "tag_string_autocomplete":
                rule["type"] = "list"
            elif preset == "title":
                rule["type"] = "text"

            if field.get("form_snippet") == "markdown.html":
                rule["type"] = "markdown"

            snippet = field.get("display_snippet")
            if snippet == "email.html":
                rule["type"] = "email"
            if snippet == "link.html":
                rule["type"] = "url"

            # Campos repetibles del JSON
            if "repeating_subfields" in field:
                rule["type"] = "list_object"
                rule["subfields"] = {
                    sf["field_name"]: (
                        "email" if sf.get("display_snippet") == "email.html"
                        else "url" if sf.get("display_snippet") == "link.html"
                        else "text"
                    )
                    for sf in field["repeating_subfields"]
                }
                # Cardinalidad mínima/máxima
                if field.get("repeating_once"):
                    rule["min_items"] = 1
                    rule["max_items"] = 1

            restrictions[fname] = rule

        return restrictions