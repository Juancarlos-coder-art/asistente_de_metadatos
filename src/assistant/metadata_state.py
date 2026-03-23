# metadata_state.py
# Clase que gestiona el estado completo de los metadatos HealthDCAT-AP
# y realiza validaciones básicas.

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, DCTERMS, FOAF, XSD
import json
import re
from assistant.validate import ejecutar_validacion_shacl


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
    # -------------------------------------------------------------
    # VALIDACIÓN SHACL (HealthDCAT-AP)
    # -------------------------------------------------------------
    def validar_shacl(self, ttl_path):
        from pathlib import Path
        from assistant.validate import ejecutar_validacion_shacl

        print("\n🧪 Validando mediante SHACL (API Comisión Europea)...")

        # 1. Convertir la ruta del TTL del usuario a absoluta
        ttl_path = Path(ttl_path).expanduser().resolve()

        # 2. Raíz del proyecto (src → asistente_de_metadatos)
        project_root = Path(__file__).resolve().parents[2]

        # 3. Carpeta con los SHACL
        shacl_dir = project_root / "tools" / "shacl"

        if not shacl_dir.exists():
            raise FileNotFoundError(f"❌ Carpeta de SHACL no encontrada: {shacl_dir}")

        # 4. Cargar shapes *.ttl
        shapes = list(shacl_dir.glob("*.ttl"))
        if not shapes:
            raise FileNotFoundError(f"❌ No se encontraron shapes SHACL en: {shacl_dir}")

        # 5. Comprobar que el TTL existe
        if not ttl_path.exists():
            raise FileNotFoundError(f"❌ El TTL no existe: {ttl_path}")

        print(f"📍 TTL (usuario): {ttl_path}")
        print(f"📍 SHACL encontrados ({len(shapes)}):")
        for s in shapes:
            print(f"   - {s.name}")

        resultados = []

        # 6. Validar cada shape
        for shape in shapes:
            print(f"\n🔎 Validando con shape: {shape.name}")
            resultado = ejecutar_validacion_shacl(str(ttl_path), str(shape.resolve()))
            resultados.append((shape.name, resultado))

        return resultados
  # -------------------------------------------------------------
    # EXPORTAR A RDF (Turtle)
    # -------------------------------------------------------------
    
    def export_to_rdf(self, output_path="dataset.ttl"):
        """
        Convierte self.data (JSON del asistente) a RDF DCAT-AP
        y lo exporta en formato Turtle.
        """
        g = Graph()

        # Namespaces
        DCAT = Namespace("http://www.w3.org/ns/dcat#")
        DCT = DCTERMS
        VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

        g.bind("dcat", DCAT)
        g.bind("dct", DCT)
        g.bind("vcard", VCARD)

        # URI del dataset (si no tienes uno, se crea uno genérico)
        dataset_uri = URIRef(self.data.get("identifier", "http://example.org/dataset/1"))

        g.add((dataset_uri, RDF.type, DCAT.Dataset))

        # Título
        if "title" in self.data:
            g.add((dataset_uri, DCT.title, Literal(self.data["title"], lang="es")))

        # Descripción
        if "description" in self.data:
            g.add((dataset_uri, DCT.description, Literal(self.data["description"], lang="es")))

        # Palabras clave
        for kw in self.data.get("tag_string", []):
            g.add((dataset_uri, DCAT.keyword, Literal(kw, lang="es")))

        # Contacto
        for c in self.data.get("contact", []):
            contact_uri = URIRef(dataset_uri + "/contact")
            g.add((dataset_uri, DCAT.contactPoint, contact_uri))

            if c.get("name"):
                g.add((contact_uri, VCARD.fn, Literal(c["name"])))
            if c.get("email"):
                g.add((contact_uri, VCARD.hasEmail, Literal("mailto:" + c["email"])))

        g.serialize(destination=output_path, format="turtle")
        print(f"💾 RDF exportado en: {output_path}")

        return output_path
