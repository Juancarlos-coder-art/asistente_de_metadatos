import json
import yaml
class HealthDCATAPSchema:
    """
    Cargador y gestor del esquema HealthDCAT-AP.
    Permite que un asistente conversacional utilice automáticamente
    las propiedades definidas en el esquema.
    """

    def __init__(self, schema_path="health_dcat_ap.yaml"):
        self.schema = self._load_schema(schema_path)
        self.dataset_fields = self.schema.get("dataset_fields", [])
        self.resource_fields = self.schema.get("resource_fields", [])

    # ------------------------------
    # CARGA DEL ESQUEMA. Abre el archivo y luego 
    # ------------------------------

    def _load_schema(self, path: str) -> dict:
        """
        Carga y devuelve el esquema YAML desde el fichero indicado.
        :return: Diccionario con el contenido del esquema
        """
        with open(path, "r", encoding="utf-8") as file:
            schema = yaml.safe_load(file)

        return schema


    # ------------------------------
    # OBTENER LISTAS DE CAMPOS
    # ------------------------------
    def list_dataset_fields(self):
<<<<<<< HEAD
        """
        Devuelve una lista de diccionarios con la información
        de los campos del dataset.
        """
=======
        return [
            {
                "name": f.get("field_name"),
                "label": f.get("label"),
                "required": f.get("required", False),
                "preset": f.get("preset"),
                "help_text": f.get("help_text"),
                "validators": f.get("validators")
            }
            for f in self.dataset_fields
        ]
>>>>>>> origin/master

        fields = []

        for field in self.dataset_fields:
            field_info = {
                "name": field.get("field_name"),
                "label": field.get("label"),
                "required": field.get("required", False),
                "preset": field.get("preset"),
                "help_text": field.get("help_text"),
            }

            fields.append(field_info)

        return fields

    #Obtiene listas de campos del bloque de resources
    def list_resource_fields(self):
        fields = []
        for field in self.resource_fields:
            field_info = {
                "name":field.get("field_name"),
                "label": field.get("label"),
                "preset": field.get ("help_text")
            }
            fields.append(field_info)
        return fields
       

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
        '''Aquí se ha cargado primero estas variables porque luego serán llamadas a la hora de preguntar.'''
        pregunta = f"📌 **{label}**"
        if required:
            pregunta += " *(obligatorio)*"

        if help_text:
            pregunta += f"\nℹ️ {help_text}"

        return pregunta

    # ------------------------------
    # GET DETALLE DEL CAMPO
    # ------------------------------
    def get_field(self, field_name: str) -> dict | None:
        """
        Devuelve el diccionario que describe un campo del dataset
        dado su nombre. Si no existe, devuelve None.
        """
        for field in self.dataset_fields:
            if field.get("field_name") == field_name:
                return field

        return None
    # ------------------------------
    # CREAR PLANTILLA VACÍA DE METADATOS
    # ------------------------------
    def empty_metadata_template(self):
        """
        Crea una estructura vacía lista para rellenar con valores del usuario.
        """

        result = {}

        for field in self.dataset_fields:
            field_name = field.get("field_name")
            result[field_name] = None

        return result



    def _load_healthdcat_yaml(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            return {}
        
    def _apply_yaml_rules(self, rule, yaml_field):
        """
        Aplica a la regla las restricciones definidas
        en el esquema YAML (HealthDCAT-AP).
        """

        # Validadores definidos en el YAML
        if "validators" in yaml_field:
            rule["validators"] = yaml_field["validators"]

        # Opciones permitidas (vocabularios controlados)
        if "choices" in yaml_field:
            values = []

            for choice in yaml_field["choices"]:
                value = choice.get("value")
                if value is not None:
                    values.append(value)

            rule["choices"] = values



    # ------------------------------
    # EXTRAER RESTRICCIONES DEL ESQUEMA
    # ------------------------------
    def extract_restrictions(self):
        """
        Genera un diccionario de reglas (restrictions) para cada
        campo del dataset, combinando información del YAML de
        HealthDCAT-AP y del schema JSON.
        """

        restrictions = {}

        # -------------------------------------------------
        # 1. Cargar esquema YAML (HealthDCAT-AP)
        # -------------------------------------------------
        # Cargamos el esquema completo desde el YAML
        yaml_schema = self._load_healthdcat_yaml("health_dcat_ap.yaml")

        # Obtenemos la lista de campos del dataset definida en el YAML
        yaml_fields = yaml_schema.get("dataset_fields", [])

        # Creamos un diccionario para acceder a los campos por su nombre
        yaml_by_name = {}

        for field in yaml_fields:
            field_name = field.get("field_name")

            if field_name is not None:
                yaml_by_name[field_name] = field

        # -------------------------------------------------
        # 2. Generar reglas por cada campo del dataset
        # -------------------------------------------------
        for field in self.dataset_fields:

            field_name = field["field_name"]

            rule = {
                "required": field.get("required", False),
                "type": "text",
            }

            # -------------------------------------------------
            # 2.1 Reglas basadas en el YAML
            # -------------------------------------------------
            yaml_field = yaml_by_name.get(field_name)
            if yaml_field:
                self._apply_yaml_rules(rule, yaml_field)
        return restrictions