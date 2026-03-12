import json

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