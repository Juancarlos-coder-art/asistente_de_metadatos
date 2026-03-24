# -*- coding: utf-8 -*-

"""
Definición de bloques de preguntas para el asistente HealthDCAT‑AP.
Este archivo es cargado por cli.py para mantener el código limpio.
"""

BLOQUES = [

    {
        "name": "identificacion_basica",
        "fields": [
            "title",
            "identifier",
            "notes",
            "uri",
            "version",
            "version_notes",
            "has_version"
        ],
        "question": "Indica el título del dataset, su identificador, descripción, URI si existe, versión actual, notas de versión y versiones relacionadas."
    },

    {
        "name": "palabras_clave_y_tipologia",
        "fields": [
            "tag_string",
            "theme",
            "dcat_type",
            "health_category",
            "health_theme",
            "code_values",
            "coding_system"
        ],
        "question": "Indica palabras clave, temática, tipo de dataset, categoría sanitaria, tema de salud y sistemas de codificación utilizados."
    },

    {
        "name": "responsables_dataset",
        "fields": [
            "publisher",
            "creator",
            "contact",
            "owner_org",
            "publisher_note",
            "publisher_type",
            "trusted_data_holder",
            "hdab"
        ],
        "question": "Indica quién publica el dataset, quién lo creó, puntos de contacto, tipo de publicador y si es un trusted data holder."
    },

    {
        "name": "documentacion_relacionada",
        "fields": [
            "homepage",
            "url",
            "documentation",
            "conforms_to",
            "is_referenced_by",
            "analytics"
        ],
        "question": "Indica la página principal, URL del dataset, documentación, estándares aplicados, recursos que lo referencian y herramientas analíticas."
    },

    {
        "name": "licencia_y_acceso",
        "fields": [
            "license_id",
            "access_rights",
            "applicable_legislation",
            "legal_basis"
        ],
        "question": "Indica la licencia del dataset, derechos de acceso, legislación aplicable y base legal del tratamiento de datos."
    },

    {
        "name": "fechas_y_ciclo_vida",
        "fields": [
            "issued",
            "modified",
            "frequency",
            "provenance",
            "provenance_activity"
        ],
        "question": "Indica fecha de publicación, última modificación, frecuencia de actualización y procedencia del dataset."
    },

    {
        "name": "cobertura_temporal_y_espacial",
        "fields": [
            "temporal_coverage",
            "temporal_resolution",
            "spatial_coverage",
            "spatial_resolution_in_meters"
        ],
        "question": "Indica periodo temporal cubierto, resolución temporal, cobertura geográfica y resolución espacial en metros."
    },

    {
        "name": "idioma_e_identificadores",
        "fields": [
            "language",
            "alternate_identifier"
        ],
        "question": "Indica el idioma del dataset y cualquier identificador alternativo (DOI, DataCite, etc.)."
    },

    {
        "name": "finalidad_y_contexto_sanitario",
        "fields": [
            "purpose",
            "population_coverage",
            "personal_data",
            "health_category",
            "health_theme"
        ],
        "question": "Indica la finalidad del dataset, cobertura poblacional, si contiene datos personales y categoría/tema sanitario."
    },

    {
        "name": "variables_demograficas",
        "fields": [
            "min_typical_age",
            "max_typical_age",
            "number_of_records",
            "number_of_unique_individuals"
        ],
        "question": "Indica edades mínima y máxima típicas, número total de registros e individuos únicos."
    },

    {
        "name": "relaciones_y_atribuciones",
        "fields": [
            "qualified_relation",
            "qualified_attribution"
        ],
        "question": "Indica relaciones con otros recursos y atribuciones formales."
    },

    {
        "name": "calidad_dataset",
        "fields": [
            "quality_annotation"
        ],
        "question": "Indica anotaciones de calidad, evidencias, certificaciones o mediciones del dataset."
    },

    {
        "name": "campos_especificos_salud",
        "fields": [
            "publisher_type",
            "publisher_note",
            "code_values",
            "coding_system"
        ],
        "question": "Indica tipo de publicador, notas del publicador y sistemas de codificación utilizados."
    },

    {
        "name": "recursos_dataset",
        "fields": [
            "url",
            "name",
            "description",
            "format",
            "mimetype",
            "compress_format",
            "package_format",
            "size",
            "hash",
            "hash_algorithm"
        ],
        "question": "Indica la URL del recurso, su nombre, descripción, formato, tipo MIME, compresión, empaquetado, tamaño y hash."
    },

    {
        "name": "derechos_recurso",
        "fields": [
            "rights",
            "availability",
            "status",
            "license"
        ],
        "question": "Indica los derechos, disponibilidad, estado y licencia del recurso."
    },

    {
        "name": "acceso_y_descarga_recurso",
        "fields": [
            "access_url",
            "download_url",
            "issued",
            "modified"
        ],
        "question": "Indica URLs de acceso y descarga, fecha de publicación y modificación del recurso."
    },

    {
        "name": "cobertura_idioma_conformidad_recurso",
        "fields": [
            "temporal_resolution",
            "spatial_resolution_in_meters",
            "language",
            "documentation",
            "conforms_to",
            "applicable_legislation",
            "uri"
        ],
        "question": "Indica resolución temporal y espacial, idioma, documentación, conformidad y legislación aplicable del recurso."
    },

    {
        "name": "servicios_acceso",
        "fields": [
            "access_services"
        ],
        "question": "Indica los servicios de acceso, incluyendo su URI, formato, endpoints, idiomas y legislación aplicable."
    }
]