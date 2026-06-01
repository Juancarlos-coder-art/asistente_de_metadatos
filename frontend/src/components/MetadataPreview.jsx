// src/components/MetadataPreview.jsx
import { useState } from "react";

const FIELD_INFO = {
  title: { label: "Título", tooltip: "Nombre oficial del dataset. Debe ser claro, descriptivo y único. Ejemplo: 'Casos de Mpox en España 2023'." },
  notes: { label: "Descripción", tooltip: "Descripción completa del contenido, alcance, metodología y propósito del dataset. Cuanta más información, mejor para que otros usuarios entiendan de qué tratan los datos." },
  identifier: { label: "Identificador", tooltip: "Identificador único y persistente del dataset, preferiblemente un DOI (Digital Object Identifier). Ejemplo: https://doi.org/10.5281/zenodo.123456. Para datasets no públicos se asigna automáticamente." },
  name: { label: "URL", tooltip: "Dirección URL del dataset en el portal de datos. Se genera automáticamente a partir del título." },
  access_rights: { label: "Derechos de acceso", tooltip: "Indica quién puede acceder al dataset según el vocabulario europeo: Público (cualquiera puede acceder), Restringido (acceso bajo condiciones o solicitud), No público (solo uso interno de la organización), Sensible (datos especialmente protegidos) o Datos provisionales." },
  hdab: { label: "Organismo de acceso (HDAB)", tooltip: "Health Data Access Body (HDAB): organismo responsable de gestionar y autorizar el acceso a los datos sanitarios según el Reglamento EHDS. Incluye nombre, tipo de organismo, correo, teléfono y página web de contacto." },
  applicable_legislation: { label: "Legislación aplicable", tooltip: "Marco legal bajo el que se tratan los datos. El GDPR (Reglamento UE 2016/679) es obligatorio para datasets con datos personales. Puede incluir también el EHDS (Reglamento UE 2025/327), la LOPDGDD española u otras normativas aplicables." },
  health_category: { label: "Categoría sanitaria", tooltip: "Categoría del dato sanitario según el Artículo 33 del Reglamento EHDS. Ejemplos: Registros Electrónicos de Salud (EHRS), Datos de ensayos clínicos (EHCT), Datos genómicos (HGPD), Registros de salud pública (PHDR). Puede seleccionarse más de una categoría." },
  theme: { label: "Tema", tooltip: "Tema principal del dataset según el vocabulario europeo de temas (EuroVoc/DCAT-AP). El tema 'Salud' (HEAL) es el más habitual para datasets sanitarios, pero puede combinarse con otros como Ciencia y Tecnología o Población y Sociedad." },
  dcat_type: { label: "Tipo de dataset", tooltip: "Tipo de dataset según el vocabulario de la Publications Office de la UE. Ejemplos: Datos Estadísticos (agregados y anonimizados), Datos Sintéticos (generados artificialmente), Datos de Alto Valor (HVD), Geoespaciales. Orienta sobre la naturaleza técnica de los datos." },
  provenance: { label: "Procedencia", tooltip: "Descripción del origen de los datos: cómo se recogieron, de qué fuentes provienen y qué transformaciones han sufrido. Ejemplo: 'Datos extraídos del Sistema de Información de Enfermedades de Declaración Obligatoria (EDO) del ISCIII'." },
  keyword: { label: "Palabras clave", tooltip: "Etiquetas descriptivas que facilitan la búsqueda y descubrimiento del dataset. Deben ser términos relevantes relacionados con el contenido, la enfermedad, la población, la metodología o la geografía. Ejemplo: 'mpox, viruela del mono, epidemiología, España, 2023'." },
  contact: { label: "Punto de contacto", tooltip: "Persona u organismo al que dirigirse para consultas sobre el dataset. Incluye correo electrónico y/o URL de la página de contacto. Es distinto del HDAB: el contacto responde preguntas sobre los datos, el HDAB gestiona el acceso." },
  access_url: { label: "URL de Acceso", tooltip: "URL donde se puede acceder o solicitar acceso al dataset. Puede ser una página web, un portal de datos o un formulario de solicitud. Es obligatoria según DCAT-AP y HealthDCAT-AP." },
  download_url: { label: "URL de descarga", tooltip: "URL de descarga directa del fichero de datos. A diferencia de la URL de acceso (que puede ser una página), esta URL apunta directamente al fichero descargable (ej: un .csv, .json o .zip). Opcional pero muy recomendable." },
  description: { label: "Descripción de la distribución", tooltip: "Descripción específica de esta distribución del dataset: qué contiene el fichero, qué variables incluye, cómo está estructurado. Puede diferir de la descripción general del dataset si hay varias distribuciones." },
  license: { label: "Licencia", tooltip: "Licencia bajo la que se publican los datos. Determina cómo pueden usarse, compartirse o modificarse. Ejemplos: CC BY 4.0 (libre con atribución), CC BY-NC (no comercial), CC0 (dominio público), licencia propietaria (uso restringido)." },
  format: { label: "Formato", tooltip: "Formato técnico del fichero de distribución. Ejemplos: CSV (texto separado por comas), JSON (JavaScript Object Notation), XML, XLSX (Excel), Parquet (columnar para big data), RDF (datos enlazados), GeoJSON (datos geoespaciales)." },
  mimetype: { label: "Tipo de medio", tooltip: "Tipo MIME (Media Type) del fichero, que identifica el formato de forma estándar para sistemas informáticos. Ejemplos: text/csv, application/json, application/xml, application/vnd.ms-excel, application/parquet." },
  compress_format: { label: "Formato de compresión", tooltip: "Formato de compresión aplicado al fichero para reducir su tamaño. Ejemplos: zip, gzip, bzip2, xz. Indica este campo si el fichero descargable está comprimido." },
  package_format: { label: "Formato de empaquetado", tooltip: "Formato de empaquetado cuando la distribución agrupa varios ficheros. Ejemplos: zip (varios ficheros en un zip), tar, tar.gz. Distinto del formato de compresión: el empaquetado agrupa ficheros, la compresión reduce el tamaño." },
  size: { label: "Tamaño (bytes)", tooltip: "Tamaño del fichero de distribución en bytes. Permite a los usuarios saber cuánto espacio ocupará antes de descargarlo. Ejemplo: 15728640 equivale a 15 MB." },
  hash: { label: "Hash", tooltip: "Valor hash o suma de comprobación del fichero, usado para verificar su integridad. Permite comprobar que el fichero descargado no ha sido alterado. Ejemplo: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'." },
  hash_algorithm: { label: "Algoritmo hash", tooltip: "Algoritmo criptográfico usado para calcular el hash del fichero. Los más habituales son MD5 (rápido pero menos seguro), SHA-256 y SHA-512 (más seguros y recomendados). Necesario para interpretar el valor del hash." },
  rights: { label: "Derechos", tooltip: "Declaración de derechos de uso del recurso de distribución, que puede complementar o especificar la licencia. Puede incluir restricciones de uso, condiciones de atribución o limitaciones geográficas. Formato libre." },
  availability: { label: "Disponibilidad", tooltip: "Indica durante cuánto tiempo estará disponible esta distribución. Valores recomendados según DCAT-AP: 'disponible', 'disponible temporalmente', 'experimental', 'estable'. Informa a los usuarios sobre la continuidad del recurso." },
  status: { label: "Estado", tooltip: "Estado actual del recurso de distribución según el vocabulario ADMS: Completado (datos finales y validados), En desarrollo (aún en elaboración), Obsoleto (reemplazado por una versión más reciente) o Retirado (ya no está disponible)." },
  distribution: { label: "Distribución", tooltip: "Representación física o accesible del dataset. Un dataset puede tener varias distribuciones en distintos formatos (CSV, JSON, API…). Cada distribución tiene su propia URL de acceso, formato y licencia." },
  purpose: { label: "Finalidad", tooltip: "Propósito o finalidades para las que se recogieron y pueden usarse los datos. Importante para cumplimiento del GDPR: los datos solo pueden usarse para los fines declarados. Ejemplo: 'vigilancia epidemiológica', 'investigación biomédica', 'gestión sanitaria'." },
  language: { label: "Idioma", tooltip: "Idioma o idiomas en los que están disponibles los datos y la documentación del dataset. Se expresa mediante códigos de idioma de la Publications Office de la UE (ej: SPA para español, ENG para inglés, CAT para catalán)." },
  population_coverage: { label: "Cobertura poblacional", tooltip: "Descripción de la población representada en el dataset: características demográficas, criterios de inclusión/exclusión, tamaño de la muestra. Ejemplo: 'Pacientes mayores de 18 años diagnosticados de COVID-19 en hospitales públicos españoles entre 2020 y 2023'." },
  number_of_unique_individuals: { label: "Número de personas individuales", tooltip: "Número de personas únicas e identificables (aunque sea de forma pseudónima) representadas en el dataset. Distinto del número de registros: una misma persona puede tener varios registros. Dato clave para evaluar el riesgo de reidentificación." },
  number_of_records: { label: "Número de registros", tooltip: "Número total de filas, observaciones o entradas en el dataset. Junto con el número de individuos, da una idea de la granularidad de los datos." },
  min_typical_age: { label: "Edad mínima típica", tooltip: "Edad mínima típica de los individuos representados en el dataset. 'Típica' significa que puede haber casos excepcionales fuera de este rango. Ayuda a entender el perfil de la población estudiada." },
  max_typical_age: { label: "Edad máxima típica", tooltip: "Edad máxima típica de los individuos representados en el dataset. Junto con la edad mínima, define el rango de edad habitual de la población del dataset." },
  personal_data: { label: "Datos personales", tooltip: "Categorías de datos personales presentes en el dataset según el vocabulario DPV-PD. Incluye categorías especiales del Art. 9 GDPR: datos de salud, genéticos, biométricos, origen étnico, etc. Fundamental para la evaluación de impacto de privacidad." },
  legal_basis: { label: "Base jurídica", tooltip: "Base jurídica del tratamiento de datos personales según el Art. 6 del GDPR. Ejemplos: consentimiento del interesado, interés público, investigación científica (Art. 9.2.j), obligación legal. Imprescindible para la conformidad legal del dataset." },
  retention_period: { label: "Periodo de conservación", tooltip: "Periodo durante el cual se conservarán los datos, con fechas de inicio y fin. El GDPR exige que los datos no se conserven más tiempo del necesario para la finalidad declarada. Ejemplo: datos conservados desde enero 2020 hasta diciembre 2030." },
  coding_system: { label: "Sistema de codificación", tooltip: "Sistema de codificación médica o científica utilizado en el dataset. Ejemplos: ICD-10 (Clasificación Internacional de Enfermedades), SNOMED CT (terminología clínica), LOINC (pruebas de laboratorio), ATC (medicamentos), MeSH (términos médicos)." },
  health_theme: { label: "Tema de salud", tooltip: "Tema de salud específico del dataset según la taxonomía de la OMS/EHDS. Permite clasificar el dataset dentro de áreas como enfermedades infecciosas, salud mental, oncología, salud materno-infantil, etc." },
  code_values: { label: "Valores codificados", tooltip: "Lista de valores o códigos utilizados en el dataset para representar categorías o variables. Ayuda a interpretar los datos sin necesidad de documentación externa. Ejemplo: '1=Masculino, 2=Femenino, 3=No especificado'." },
  publisher: { label: "Editor", tooltip: "Organización responsable de publicar y hacer disponible el dataset. Incluye nombre, tipo de organismo, correo, teléfono, página web y horario de atención. El editor es quien asume la responsabilidad pública de la publicación." },
  publisher_note: { label: "Nota del editor", tooltip: "Notas adicionales del editor sobre el dataset: advertencias de uso, limitaciones conocidas, contexto de publicación o cualquier información relevante que el editor quiera comunicar a los usuarios." },
  creator: { label: "Creador", tooltip: "Persona u organización que creó o generó los datos originales. Puede diferir del editor (quien publica). En investigación biomédica suele ser el equipo investigador o el hospital que recogió los datos." },
  qualified_attribution: { label: "Atribución cualificada", tooltip: "Agente que ha tenido un rol específico en la creación, gestión o publicación del dataset. Roles posibles: autor, custodio, financiador, propietario, distribuidor, punto de contacto, titular de derechos, etc. Sigue el estándar ISO 19115." },
  was_generated_by: { label: "Se generó por", tooltip: "Actividad o proceso sanitario que generó los datos. Ejemplos: ensayo clínico, encuesta de salud, registros hospitalarios, registros de dispensación, biobanco, vigilancia epidemiológica. Permite entender el contexto de recogida." },
  spatial: { label: "Cobertura geográfica", tooltip: "Países o territorios cubiertos por el dataset, expresados mediante códigos ISO 3166-1 alpha-3 (ej: ESP para España, FRA para Francia). Indica el ámbito geográfico de la población o los datos recogidos." },
  temporal_coverage: { label: "Cobertura temporal", tooltip: "Periodo temporal cubierto por los datos, con fecha de inicio y fin. Distinto de las fechas de publicación o modificación del dataset: indica el intervalo de tiempo al que pertenecen los datos recogidos." },
  temporal_resolution: { label: "Resolución temporal", tooltip: "Mínima granularidad temporal de los datos, expresada en formato ISO 8601. Ejemplos: P1D (diaria), PT1H (horaria), P1M (mensual), P1Y (anual). Indica la frecuencia con la que se recogieron o actualizaron los datos." },
  spatial_resolution_in_meters: { label: "Resolución espacial (m)", tooltip: "Resolución espacial mínima de los datos en metros. Relevante para datasets geoespaciales o con componente geográfico. Indica la precisión geográfica de los datos: a menor número, mayor precisión." },
  frequency: { label: "Frecuencia", tooltip: "Frecuencia con la que se actualiza el dataset. Ejemplos: Diario, Semanal, Mensual, Trimestral, Anual, Continuo, Irregular, No previsto. Informa a los usuarios sobre la actualidad de los datos." },
  issued: { label: "Fecha de publicación", tooltip: "Fecha en que el dataset fue publicado o puesto a disposición por primera vez, en formato YYYY-MM-DD. Distinta de la fecha de modificación: la fecha de publicación no cambia aunque el dataset se actualice." },
  modified: { label: "Fecha de modificación", tooltip: "Fecha de la última modificación del dataset, en formato YYYY-MM-DD. Se actualiza cada vez que se realizan cambios en los datos o en los metadatos. Permite saber cuán reciente es la última versión." },
  alternate_identifier: { label: "Identificador alternativo", tooltip: "Identificadores adicionales del dataset en otros sistemas: DOI de publicaciones relacionadas, URN, handle, ISBN, etc. Facilita encontrar el dataset desde diferentes catálogos o sistemas de referencia." },
  conforms_to: { label: "Se ajusta a", tooltip: "Estándar, especificación o esquema al que se ajusta el dataset. Ejemplos: HealthDCAT-AP, DCAT-AP 3.0, ISO 27001, HL7 FHIR. Indica conformidad con estándares de interoperabilidad o calidad." },
  related_resource: { label: "Recurso relacionado", tooltip: "Recursos externos relacionados con el dataset: publicaciones científicas, informes, otros datasets complementarios, herramientas de análisis. Enriquece el contexto y facilita la investigación." },
  is_referenced_by: { label: "Referenciado por", tooltip: "Recursos que citan o referencian este dataset: artículos científicos que lo han utilizado, informes que lo mencionan, otros datasets que lo incluyen. Permite conocer el impacto y uso del dataset." },
  url: { label: "Página de entrada", tooltip: "URL de la página web principal (landing page) del dataset en el portal de datos. Es la página donde el usuario accede a toda la información del dataset, distinta de la URL de descarga directa del fichero." },
  documentation: { label: "Documentación", tooltip: "Documentación técnica o descriptiva asociada al dataset: diccionario de variables, manual de usuario, protocolo de recogida de datos, informe metodológico. Esencial para que los usuarios entiendan y usen correctamente los datos." },
  version: { label: "Versión", tooltip: "Número o código de la versión actual del dataset. Se recomienda seguir el versionado semántico (ej: 1.0, 2.1.3). Permite distinguir entre distintas versiones del mismo dataset." },
  has_version: { label: "Tiene versión", tooltip: "Lista de versiones disponibles del dataset. Permite a los usuarios acceder a versiones anteriores o alternativas. Útil para reproducibilidad científica: garantiza que los análisis puedan repetirse con la misma versión de los datos." },
  version_notes: { label: "Notas de versión", tooltip: "Descripción de los cambios introducidos en esta versión respecto a la anterior: correcciones, nuevas variables, ampliación del periodo temporal, etc. Ayuda a los usuarios a decidir si deben actualizar a la nueva versión." },
};

// Campos que se pueden editar inline (tipos simples de texto)
const EDITABLE_FIELDS = new Set([
  "title", "notes", "identifier", "name", "provenance", "keyword",
  "purpose", "population_coverage", "number_of_unique_individuals",
  "number_of_records", "min_typical_age", "max_typical_age",
  "publisher_note", "temporal_resolution", "spatial_resolution_in_meters",
  "issued", "modified", "alternate_identifier", "version",
  "has_version", "version_notes", "access_url", "download_url", "description",
  "license", "format", "mimetype", "compress_format", "package_format",
  "size", "hash", "hash_algorithm", "rights", "availability",
]);

const HEALTH_CATEGORY_LABELS = {
  "EHRS": "Registros Electrónicos de Salud",
  "HRAD": "Datos administrativos relacionados con la salud, incluidos los datos de dispensación, reclamaciones y reembolsos",
  "MRMR": "Datos de registros médicos y registros de mortalidad",
  "RPDG": "Datos de patógenos que afectan a la salud humana",
  "RQSH": "Datos de cohortes de investigación, cuestionarios y encuestas relacionados con la salud, tras la primera publicación de los resultados",
  "PHDR": "Registros de datos de salud basados en la población (registros de salud pública)",
  "EHCT": "Datos de ensayos clínicos, estudios clínicos e investigaciones clínicas",
  "HGPD": "Datos genéticos, epigenómicos y genómicos humanos",
  "EINS": "Datos de salud de biobancos y bases de datos asociadas",
  "EMRD": "Otros datos de salud de dispositivos médicos",
  "HPML": "Otros datos moleculares humanos como datos proteómicos, transcriptómicos, metabolómicos, lipidómicos y otros datos ómicos",
  "WELA": "Datos de aplicaciones de bienestar",
  "RMMD": "Datos de registros de productos medicinales y dispositivos médicos",
  "NRPE": "Datos agregados sobre las necesidades de atención sanitaria, los recursos asignados a la atención sanitaria, el gasto sanitario y la financiación",
  "PGEH": "Datos electrónicos de salud personales generados automáticamente a través de dispositivos médicos",
  "IDHP": "Datos sobre el estado profesional, la especialización y la institución de los profesionales de la salud involucrados en el tratamiento de una persona física",
  "DIOH": "Datos sobre factores que afectan a la salud, incluidos los determinantes socioeconómicos, ambientales y de comportamiento de la salud",
};

const THEME_LABELS = {
  "HEAL": "Salud", "TECH": "Ciencia y Tecnología", "SOCI": "Población y sociedad",
  "GOVE": "Gobierno y sector público", "EDUC": "Educación, cultura y deportes",
  "ECON": "Economía y finanzas", "ENVI": "Medio ambiente",
  "AGRI": "Agricultura, pesca, silvicultura y alimentación", "TRAN": "Transporte",
  "JUST": "Justicia, sistema judicial y seguridad pública", "REGI": "Regiones y ciudades",
  "INTR": "Asuntos Internacionales", "ENER": "Energía", "OP_DATPRO": "Datos provisionales",
};

const DCAT_TYPE_LABELS = {
  "STATISTICAL": "Datos Estadísticos", "GEOSPATIAL": "Datos Geoespaciales",
  "HVD": "Conjunto de datos de alto valor", "SYNTHETIC_DATA": "Datos Sintéticos",
  "ONTOLOGY": "Ontología", "SCHEMA": "Esquema", "CODE_LIST": "Lista de Códigos",
  "APROF": "Perfil de Aplicación", "TEST_DATA": "Datos de Prueba",
  "CORE_COMP": "Componente básico", "MAPPING": "Correspondencia",
  "DIRECTORY": "Directorio", "GLOSSARY": "Glosario", "THESAURUS": "Tesauro",
  "TAXONOMY": "Taxonomía", "DOMAIN_MODEL": "Modelo de Dominio", "RELEASE": "Publicación",
  "ATTO_LEX": "Cuadro ATTO – dominio EUR-Lex", "ATTO_PUB": "Cuadro ATTO – dominio Publicaciones",
  "OP_DATPRO": "Datos Provisionales", "IEPD": "Descripción de un paquete de intercambio de información",
  "DSCRP_SERV": "Descripción del Servicio", "STYLES": "Hojas de Estilo",
  "NAL": "Lista Autorizada de Nombres", "SYNTAX_ECD_SCHEME": "Esquema de codificación sintáctica",
};

const PUBLISHER_TYPE_LABELS = {
  "public-health-institute": "Instituto de Salud Pública",
  "research-institute-org": "Instituto/organización de investigación",
  "national-authority": "Autoridad Nacional", "regional-authority": "Autoridad Regional",
  "university": "Universidad", "public-health-registry": "Registro de Salud Pública",
  "public-health-org": "Organización de Salud Pública", "stat-agency": "Agencia de estadísticas",
  "biobank": "Biobanco", "inpatient-institute": "Institución de hospitalización/Hospital",
  "laboratory": "Laboratorio", "private-company": "Empresa Privada",
  "gov-public-sector-org": "Organizaciones gubernamentales y del sector público",
  "healthcare-providers": "Proveedor de Atención Médica",
  "health-insurance-company-org": "Compañía/organización de seguros de salud",
  "pharma-company": "Empresas Farmacéuticas", "private-sector-entities": "Entidades del sector privado",
  "health-technology-manufacturer": "Fabricante de aplicaciones/tecnología de salud",
  "software-manufacturer": "Fabricante de software", "pharmacy": "Farmacia",
  "research-infra": "Infraestructuras de Investigación",
  "administrative-institution": "Institución administrativa",
  "outpatient-institution": "Institución ambulatoria",
  "national-cancer-institute": "Instituto Nacional del Cáncer",
  "municipality-or-other-area": "Municipio u otra área",
  "research-academic-org": "Organizaciones de investigación y académicas",
  "non-gov-org": "Organizaciones no gubernamentales",
  "primary-care-org": "Organización de atención primaria",
  "mental-health-org": "Organización de salud mental",
  "not-for-profit-org": "Organización sin ánimo de lucro",
  "other-government-agency": "Otra agencia gubernamental",
  "other-company": "Otro tipo de empresa que de alguna manera recopila datos de salud",
  "other-public-institute": "Otros institutos públicos que recogen datos de salud",
  "quality-registry": "Registro de Calidad", "pathology-registry": "Registro de Patología",
  "private-health-insurance": "Seguro de salud privado",
};

const LANGUAGE_LABELS = {
  "DEU": "Alemán", "NOB": "Bokmål", "BUL": "Búlgaro", "CES": "Checo",
  "HRV": "Croata", "DAN": "Danés", "SLK": "Eslovaco", "SLV": "Esloveno",
  "SPA": "Español", "EST": "Estonio", "FIN": "Finés", "FRA": "Francés",
  "ELL": "Griego", "HUN": "Húngaro", "ENG": "Inglés", "GLE": "Irlandés",
  "ISL": "Islandés", "ITA": "Italiano", "LAV": "Letón", "LIT": "Lituano",
  "MLT": "Maltés", "NLD": "Neerlandés", "NNO": "Nynorsk", "POL": "Polaco",
  "POR": "Portugués", "RON": "Rumano", "SWE": "Sueco",
  "CAT": "Catalán", "GLG": "Gallego", "EUS": "Euskera",
};

const HEALTH_ACTIVITY_LABELS = {
  "EHEALTH_APPLICATION": "Aplicación de sanidad electrónica",
  "NONMEDICAL_APPLICATION": "Aplicación no médica",
  "HOSPITAL_RECORDS": "Base de datos de historiales hospitalarios",
  "RESEARCH_DATABASE": "Base de datos de investigación específica",
  "BIOBANK_COLLECTION": "Biobanco/recogida de muestras",
  "COHORT": "Cohorte",
  "SAMPLE_COLLECTIONS": "Colecciones de muestras",
  "OBSERVATIONAL_DATA": "Datos de observación",
  "CENSUS_DATA": "Datos del censo",
  "PROBABILITY_SURVEY": "Encuesta de probabilidad",
  "HEALTH_SURVEY": "Encuesta de salud",
  "CLINICAL_TRIAL": "Ensayo clínico",
  "AUTOMATIC_GENERATION": "Generado automáticamente",
  "ADMISSION_DISCHARGE": "Ingreso, atención y alta del paciente",
  "MEASUREMENTS": "Mediciones",
  "MODELS_SIMULATIONS": "Modelos y simulaciones",
  "PRESCRIBING_DISPENSING": "Prescripción o dispensación de medicamentos",
  "ADMINISTRATIVE_PROCESSES": "Procesos administrativos",
  "PATIENT_OUTCOMES": "PROM (Medidas de resultados comunicados por los pacientes)",
  "RESEARCH_PROJECT": "Proyecto de investigación",
  "LABORATORY_TESTS": "Pruebas de laboratorio",
  "INSURANCE_CLAIMS": "Reclamaciones, seguros y reembolsos",
  "QUALITY_REGISTRY": "Registro de Calidad",
  "MEDICAL_REGISTRY": "Registro médico",
  "ROUTINE_RECORDS": "Registros de rutina (no sanitarios)",
  "QUALITY_REGISTRIES": "Registros Nacionales de Calidad Médica",
  "HEALTH_REGISTRIES": "Registros Nacionales de Salud",
  "MUNICIPAL_REPOSITORY": "Repositorio municipal de datos sanitarios",
  "GEOSPATIAL_MONITORING": "Seguimiento geoespacial",
  "MEDICAL_DEVICES": "Uso de productos sanitarios",
  "SURVEILLANCE": "Vigilancia",
  "DISEASE_MONITORING": "Vigilancia de enfermedades infecciosas",
  "HEALTH_SURVEILLANCE": "Vigilancia de la salud pública",
  "HEALTHCARE_VISIT": "Visita sanitaria",
};

const HEALTH_THEME_LABELS = {
  "CLIMATE_HEALTH": "Clima y salud planetaria",
  "CANCER_DISEASE": "Cáncer",
  "EMERGENCY_SETTINGS": "Emergencias, catástrofes, viajes y entornos humanitarios",
  "TROPICAL_DISEASES": "Enfermedades cutáneas tropicales, parasitarias y fúngicas desatendidas",
  "RESPIRATORY_DISEASES": "Enfermedades infecciosas respiratorias",
  "NONCOMMUNICABLE_DISEASES": "Enfermedades no transmisibles: metabólicas y cardiopulmonares",
  "VECTOR_DISEASES": "Enfermedades víricas de transmisión vectorial y zoonóticas",
  "BLOOD_INFECTIONS": "Infecciones de transmisión sanguínea y de transmisión sexual",
  "ENTERIC_INFECTIONS": "Infecciones entéricas, transmitidas por el agua y los alimentos",
  "IMMUNIZATION_DISEASES": "Inmunización y enfermedades prevenibles mediante vacunación",
  "INJURY_PREVENTION": "Lesiones, envenenamiento y ahogamiento",
  "NUTRITION_SECURITY": "Nutrición y seguridad alimentaria",
  "HEALTH_PRODUCTS": "Productos sanitarios, tecnologías, datos e investigación",
  "ANTIMICROBIAL_CONTROL": "Resistencia a los antimicrobianos y control de las infecciones",
  "LIFECOURSE_HEALTH": "Salud a lo largo de la vida: materna, neonatal, infantil, adolescente y envejecimiento",
  "ENVIRONMENTAL_HEALTH": "Salud ambiental, laboral y radiológica",
  "SENSORY_HEALTH": "Salud bucal, ocular y sensorial",
  "REPRODUCTIVE_HEALTH": "Salud y derechos sexuales y reproductivos",
  "HEALTH_SYSTEMS": "Sistemas de salud, calidad, modelos de atención y determinantes",
  "MENTAL_HEALTH": "Salud mental, neurológica y uso de sustancias",
};

const FREQUENCY_LABELS = {
  "ANNUAL": "Anual", "BIENNIAL": "Bienal", "MONTHLY_2": "Bimensual",
  "BIMONTHLY": "Bimestral", "WEEKLY_2": "Bisemanal", "CONT": "Continuo",
  "UPDATE_CONT": "Continuamente actualizado", "ANNUAL_3": "Cuatrimestral",
  "DAILY": "Diario", "DAILY_2": "Dos veces al día", "AS_NEEDED": "En función de las necesidades",
  "IRREG": "Irregular", "MONTHLY": "Mensual", "NOT_PLANNED": "No previsto",
  "NEVER": "Nunca", "OTHER": "Otro", "BIWEEKLY": "Quincenal",
  "WEEKLY": "Semanal", "ANNUAL_2": "Semestral", "QUARTERLY": "Trimestral",
  "TRIENNIAL": "Trienal", "UNKNOWN": "Desconocido",
};

const PERSONAL_DATA_LABELS = {
  "Age": "Edad", "AgeRange": "Rango de edad", "Biometric": "Datos biométricos",
  "BloodType": "Tipo de sangre", "BirthDate": "Fecha de nacimiento",
  "BirthCountry": "País de nacimiento", "Disability": "Discapacidad",
  "DNACode": "ADN", "Ethnicity": "Origen étnico", "Gender": "Género",
  "Genetic": "Datos genéticos", "HealthData": "Datos de salud",
  "HealthHistory": "Historial de salud", "HealthRecord": "Registro de salud",
  "Height": "Altura", "LifeSexual": "Vida sexual", "MedicalHealth": "Historial médico",
  "MentalHealth": "Salud mental", "PhysicalHealth": "Salud física",
  "Prescription": "Receta médica", "Race": "Origen racial",
  "SexualHistory": "Datos de salud sexual", "Weight": "Peso",
};

const COUNTRY_LABELS = {
  "ESP": "España", "DEU": "Alemania", "FRA": "Francia", "ITA": "Italia",
  "PRT": "Portugal", "NLD": "Países Bajos", "BEL": "Bélgica", "SWE": "Suecia",
  "FIN": "Finlandia", "DNK": "Dinamarca", "NOR": "Noruega", "AUT": "Austria",
  "CHE": "Suiza", "POL": "Polonia", "IRL": "Irlanda", "GRC": "Grecia",
  "CZE": "República Checa", "ROU": "Rumanía", "HUN": "Hungría",
  "EUR": "Unión Europea", "GBR": "Reino Unido", "USA": "Estados Unidos", "CAN": "Canadá",
};

function formatValue(key, value, schemaInfo = {}) {
  if (value === null || value === undefined || value === "") return null;

  if (key === "access_rights" && typeof value === "string") {
    const code = value.split("/").pop();
    const map = {
      PUBLIC: "Público", RESTRICTED: "Restringido", CONFIDENTIAL: "Confidencial",
      NON_PUBLIC: "No público", SENSITIVE: "Sensible", NORMAL: "Normal",
      OP_DATPRO: "Datos provisionales",
    };
    return map[code] || code;
  }

  if (key === "hdab" && typeof value === "object") {
    const typeCode = value.type ? value.type.split("/").pop() : null;
    const typeLabel = typeCode ? (PUBLISHER_TYPE_LABELS[typeCode] || typeCode) : null;
    const freqCode = value.opening_hours_frequency ? value.opening_hours_frequency.split("/").pop() : null;
    const freqLabel = freqCode ? (FREQUENCY_LABELS[freqCode] || freqCode) : null;
    const sfreqCode = value.special_opening_hours_frequency ? value.special_opening_hours_frequency.split("/").pop() : null;
    const sfreqLabel = sfreqCode ? (FREQUENCY_LABELS[sfreqCode] || sfreqCode) : null;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.name && <span><strong>Nombre:</strong> {value.name}</span>}
        {typeLabel && <span><strong>Tipo:</strong> {typeLabel}</span>}
        {value.contact && <span><strong>Página de contacto:</strong> <a href={value.contact} target="_blank" rel="noreferrer">{value.contact}</a></span>}
        {value.contact_page && <span><strong>Página de contacto:</strong> <a href={value.contact_page} target="_blank" rel="noreferrer">{value.contact_page}</a></span>}
        {value.email && <span><strong>Correo:</strong> {value.email}</span>}
        {value.telephone && <span><strong>Teléfono:</strong> {value.telephone}</span>}
        {value.opening_hours_description && <span><strong>Horario habitual:</strong> {value.opening_hours_description}</span>}
        {freqLabel && <span><strong>Frecuencia horario habitual:</strong> {freqLabel}</span>}
        {value.special_opening_hours_description && <span><strong>Horario especial:</strong> {value.special_opening_hours_description}</span>}
        {sfreqLabel && <span><strong>Frecuencia horario especial:</strong> {sfreqLabel}</span>}
      </div>
    );
  }

  if (key === "contact") {
    if (Array.isArray(value)) {
      return value.map((v, i) => (
        <div key={i} style={{ marginBottom: "4px" }}>
          {v.email && <span><strong>Correo:</strong> {v.email}</span>}
          {v.url && <span> · <strong>Web:</strong> <a href={v.url} target="_blank" rel="noreferrer">{v.url}</a></span>}
        </div>
      ));
    }
    if (typeof value === "object") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {value.email && <span><strong>Correo:</strong> {value.email}</span>}
          {value.url && <span><strong>Web:</strong> <a href={value.url} target="_blank" rel="noreferrer">{value.url}</a></span>}
        </div>
      );
    }
  }

  if (key === "health_category" && Array.isArray(value)) {
    return value.map(uri => {
      const code = uri.split("/").pop();
      return HEALTH_CATEGORY_LABELS[code] || code;
    }).join(", ");
  }

  if (key === "theme" && Array.isArray(value)) {
    return value.map(uri => {
      const code = uri.split("/").pop();
      return THEME_LABELS[code] || code;
    }).join(", ");
  }

  if (key === "dcat_type" && typeof value === "string") {
    const code = value.split("/").pop();
    return DCAT_TYPE_LABELS[code] || code;
  }

  if (key === "language" && Array.isArray(value)) {
    return value.map(uri => {
      const code = uri.split("/").pop();
      return LANGUAGE_LABELS[code] || code;
    }).join(", ");
  }

  if (key === "personal_data" && Array.isArray(value)) {
    const choices = schemaInfo?.personal_data?.choices || [];
    const labelMap = Object.fromEntries(choices.map(c => [c.value, c.label]));
    return value.map(uri => labelMap[uri] || uri.split("#").pop().replace(/([a-z])([A-Z])/g, "$1 $2")).join(", ");
  }

  if (key === "applicable_legislation" && Array.isArray(value)) {
    return value.map((v, i) => <span key={i}>{v.label || v.uri}</span>);
  }

  if (key === "access_url" && typeof value === "string") {
    return <a href={value} target="_blank" rel="noreferrer">{value}</a>;
  }

  if (key === "download_url" && typeof value === "string") {
    return <a href={value} target="_blank" rel="noreferrer">{value}</a>;
  }

  if (key === "status" && typeof value === "string") {
    const map = {
      "http://purl.org/adms/status/Completed": "Completado",
      "http://purl.org/adms/status/UnderDevelopment": "En desarrollo",
      "http://purl.org/adms/status/Deprecated": "Obsoleto",
      "http://purl.org/adms/status/Withdrawn": "Retirado",
    };
    return map[value] || value.split("/").pop();
  }

  if (key === "distribution" && Array.isArray(value)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.map((dist, i) => (
          <div key={i}>
            {dist.access_url && (
              <span><strong>URL:</strong> <a href={dist.access_url} target="_blank" rel="noreferrer">{dist.access_url}</a></span>
            )}
          </div>
        ))}
      </div>
    );
  }

  if (key === "health_theme" && Array.isArray(value)) {
    const choices = schemaInfo?.health_theme?.choices || [];
    const labelMap = Object.fromEntries(choices.map(c => [c.value, c.label]));
    return value.map(uri => labelMap[uri] || uri.split("/").pop()).join(", ");
  }

  if (key === "legal_basis") {
    if (Array.isArray(value)) {
      return value.map((v, i) => (
        <div key={i} style={{ marginBottom: "6px", paddingLeft: "8px", borderLeft: "2px solid #e0e0e0" }}>
          {v.description && <span><strong>Descripción:</strong> {v.description}</span>}<br/>
          {v.source && <span><strong>Fuente:</strong> {v.source}</span>}
        </div>
      ));
    }
    if (typeof value === "object") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {value.description && <span><strong>Descripción:</strong> {value.description}</span>}
          {value.source && <span><strong>Fuente:</strong> {value.source}</span>}
        </div>
      );
    }
  }

  if (key === "retention_period") {
    const v = Array.isArray(value) ? value[0] : value;
    if (typeof v === "object") {
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {v.start && <span><strong>Inicio:</strong> {v.start}</span>}
          {v.end && <span><strong>Fin:</strong> {v.end}</span>}
        </div>
      );
    }
  }

  if (key === "coding_system") {
    if (Array.isArray(value)) {
      return value.map((v, i) => (
        <div key={i} style={{ marginBottom: "4px" }}>
          {typeof v === "object"
            ? <span>{v.label || v.uri || JSON.stringify(v)}</span>
            : <span>{v}</span>
          }
        </div>
      ));
    }
    if (typeof value === "object") {
      return <span>{value.label || value.uri || JSON.stringify(value)}</span>;
    }
  }

  if (key === "publisher" && typeof value === "object") {
    const typeCode = value.type ? value.type.split("/").pop() : null;
    const typeLabel = typeCode ? (PUBLISHER_TYPE_LABELS[typeCode] || typeCode) : null;
    const freqCode = value.opening_hours_frequency ? value.opening_hours_frequency.split("/").pop() : null;
    const freqLabel = freqCode ? (FREQUENCY_LABELS[freqCode] || freqCode) : null;
    const sfreqCode = value.special_opening_hours_frequency ? value.special_opening_hours_frequency.split("/").pop() : null;
    const sfreqLabel = sfreqCode ? (FREQUENCY_LABELS[sfreqCode] || sfreqCode) : null;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.name && <span><strong>Nombre:</strong> {value.name}</span>}
        {typeLabel && <span><strong>Tipo:</strong> {typeLabel}</span>}
        {value.contact_page && <span><strong>Página de contacto:</strong> <a href={value.contact_page} target="_blank" rel="noreferrer">{value.contact_page}</a></span>}
        {value.email && <span><strong>Correo:</strong> {value.email}</span>}
        {value.telephone && <span><strong>Teléfono:</strong> {value.telephone}</span>}
        {value.opening_hours_description && <span><strong>Horario habitual:</strong> {value.opening_hours_description}</span>}
        {freqLabel && <span><strong>Frecuencia horario habitual:</strong> {freqLabel}</span>}
        {value.special_opening_hours_description && <span><strong>Horario especial:</strong> {value.special_opening_hours_description}</span>}
        {sfreqLabel && <span><strong>Frecuencia horario especial:</strong> {sfreqLabel}</span>}
      </div>
    );
  }

  if (key === "creator") {
    const renderCreator = (v) => {
      const typeCode = v.type ? v.type.split("/").pop() : null;
      const typeLabel = typeCode ? (PUBLISHER_TYPE_LABELS[typeCode] || typeCode) : null;
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {v.name && <span><strong>Nombre:</strong> {v.name}</span>}
          {typeLabel && <span><strong>Tipo:</strong> {typeLabel}</span>}
          {v.email && <span><strong>Correo:</strong> {v.email}</span>}
          {v.url && <span><strong>URL:</strong> <a href={v.url} target="_blank" rel="noreferrer">{v.url}</a></span>}
        </div>
      );
    };
    if (Array.isArray(value)) return value.map((v, i) => <div key={i}>{renderCreator(v)}</div>);
    if (typeof value === "object") return renderCreator(value);
  }

  if (key === "qualified_attribution") {
    const renderAttribution = (v) => {
      const typeCode = v.qualified_attribution_agent_type ? v.qualified_attribution_agent_type.split("/").pop() : null;
      const typeLabel = typeCode ? (PUBLISHER_TYPE_LABELS[typeCode] || typeCode) : null;
      const roleCode = v.qualified_attribution_role ? v.qualified_attribution_role.split("#").pop() :
                      v.role ? v.role.split("#").pop() : null;
      const ROLE_LABELS = {
        "author": "Autor", "coAuthor": "Co autor", "collaborator": "Colaborador",
        "contributor": "Contribuyente", "custodian": "Custodio", "distributor": "Distribuidor",
        "publisher": "Editor", "funder": "Financiador", "principalInvestigator": "Investigador principal",
        "originator": "Originador", "owner": "Propietario", "pointOfContact": "Punto de contacto",
        "rightsHolder": "Titular de los derechos", "user": "Usuario",
      };
      const roleLabel = roleCode ? (ROLE_LABELS[roleCode] || roleCode) : null;
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {(v.qualified_attribution_agent_name || v.name) && <span><strong>Nombre:</strong> {v.qualified_attribution_agent_name || v.name}</span>}
          {typeLabel && <span><strong>Tipo:</strong> {typeLabel}</span>}
          {(v.qualified_attribution_agent_email || v.email) && <span><strong>Correo:</strong> {v.qualified_attribution_agent_email || v.email}</span>}
          {(v.qualified_attribution_agent_contact_page || v.contact_page) && <span><strong>Página de contacto:</strong> <a href={v.qualified_attribution_agent_contact_page || v.contact_page} target="_blank" rel="noreferrer">{v.qualified_attribution_agent_contact_page || v.contact_page}</a></span>}
          {roleLabel && <span><strong>Rol:</strong> {roleLabel}</span>}
        </div>
      );
    };
    if (Array.isArray(value)) return value.map((v, i) => <div key={i} style={{ marginBottom: "6px" }}>{renderAttribution(v)}</div>);
    if (typeof value === "object") return renderAttribution(value);
  }

  if (key === "was_generated_by" && Array.isArray(value)) {
    const choices = schemaInfo?.was_generated_by?.choices || [];
    const labelMap = Object.fromEntries(choices.map(c => [c.value, c.label]));
    return value.map(uri => labelMap[uri] || uri.split("/").pop()).join(", ");
  }

  if (key === "spatial" && Array.isArray(value)) {
    const choices = schemaInfo?.spatial?.choices || [];
    const labelMap = Object.fromEntries(choices.map(c => [c.value, c.label]));
    return value.map(uri => labelMap[uri] || uri.split("/").pop()).join(", ");
  }

  if (key === "temporal_coverage" && typeof value === "object" && !Array.isArray(value)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.start && <span><strong>Inicio:</strong> {value.start}</span>}
        {value.end && <span><strong>Fin:</strong> {value.end}</span>}
      </div>
    );
  }

  if (key === "frequency" && typeof value === "string") {
    const choices = schemaInfo?.frequency?.choices || [];
    const match = choices.find(c => c.value === value);
    return match ? match.label : value.split("/").pop();
  }

  if ((key === "conforms_to" || key === "related_resource" || key === "documentation") && typeof value === "object" && !Array.isArray(value)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.uri && <span><strong>URI:</strong> <a href={value.uri} target="_blank" rel="noreferrer">{value.uri}</a></span>}
        {value.label && <span><strong>Etiqueta:</strong> {value.label}</span>}
      </div>
    );
  }

  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

// ── Fila editable inline ──
function EditableFieldRow({ fieldKey, value, label, tooltip, schemaInfo, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(typeof value === "string" ? value : "");
  const [tooltipPos, setTooltipPos] = useState(null);
  const isEditable = EDITABLE_FIELDS.has(fieldKey) && typeof value === "string";

  const handleSave = () => {
    onSave(fieldKey, draft);
    setEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") setEditing(false);
  };

  const handleInfoClick = (e) => {
    if (tooltipPos) { setTooltipPos(null); return; }
    const rect = e.currentTarget.getBoundingClientRect();
    const top = rect.bottom + 6;
    const left = Math.min(rect.left, window.innerWidth - 360);
    setTooltipPos({ top, left });
  };

  const formatted = formatValue(fieldKey, value, schemaInfo);
  if (!formatted) return null;

  return (
    <div className="field-row" style={{ position: "relative", alignItems: "flex-start" }}>
      {tooltipPos && (
        <>
          <div
            onClick={() => setTooltipPos(null)}
            style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 999 }}
          />
          <div style={{
            position: "fixed",
            top: tooltipPos.top,
            left: tooltipPos.left,
            zIndex: 1000,
            background: "#1c1c1c",
            color: "#f4f4f4",
            fontSize: "0.82rem",
            lineHeight: 1.6,
            padding: "14px 16px",
            width: "340px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.45)",
            fontFamily: "'IBM Plex Sans', sans-serif",
            borderLeft: "3px solid #0f62fe",
            borderRadius: "2px",
          }}>
            <div style={{
              fontWeight: 600, marginBottom: "6px",
              color: "#78a9ff", fontSize: "0.85rem",
              fontFamily: "'IBM Plex Mono', monospace",
            }}>{label}</div>
            {tooltip}
          </div>
        </>
      )}
      <div className="field-key" style={{ display: "flex", alignItems: "center", gap: "5px", paddingTop: "2px" }}>
        <span>{label}</span>
        {tooltip && (
          <button
            onClick={handleInfoClick}
            title="Más información"
            style={{
              background: "none", border: "1.5px solid #0f62fe", cursor: "pointer",
              color: "#0f62fe", fontSize: "0.68rem", padding: "0",
              fontWeight: 700, fontFamily: "serif",
              width: "14px", height: "14px", minWidth: "14px",
              display: "inline-flex", alignItems: "center", justifyContent: "center",
              borderRadius: "50%", flexShrink: 0, lineHeight: 1,
            }}
          >i</button>
        )}
      </div>
      <div className="field-val" style={{ flex: 1 }}>
        {editing ? (
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <input
              autoFocus
              style={{
                flex: 1, border: "1px solid #0f62fe", padding: "4px 8px",
                fontSize: "0.85rem", fontFamily: "'IBM Plex Sans', sans-serif",
                outline: "none", background: "white",
              }}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button
              onClick={handleSave}
              style={{
                background: "#0f62fe", color: "white", border: "none",
                padding: "4px 10px", fontSize: "0.78rem", cursor: "pointer",
                fontFamily: "'IBM Plex Mono', monospace",
              }}
            >✓</button>
            <button
              onClick={() => setEditing(false)}
              style={{
                background: "transparent", color: "#525252", border: "1px solid #c6c6c6",
                padding: "4px 8px", fontSize: "0.78rem", cursor: "pointer",
              }}
            >✕</button>
          </div>
        ) : (
          <span>{formatted}</span>
        )}
      </div>
      {isEditable && !editing && (
        <button
          className="edit-btn"
          onClick={() => { setDraft(typeof value === "string" ? value : ""); setEditing(true); }}
          title="Editar"
          style={{
            opacity: 1,
            background: "transparent",
            border: "1px solid #0f62fe",
            cursor: "pointer",
            color: "#0f62fe",
            fontSize: "0.72rem",
            padding: "2px 8px",
            fontFamily: "'IBM Plex Mono', monospace",
            flexShrink: 0,
            letterSpacing: "0.03em",
          }}
        >Editar</button>
      )}
    </div>
  );
}

export default function MetadataPreview({ metadata, schemaInfo = {}, onFieldSave }) {
  const entries = Object.entries(metadata).filter(
    ([, v]) => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0)
  );

  if (entries.length === 0) {
    return (
      <div className="preview-empty">
        <span className="preview-empty-icon">📭</span>
        <p className="preview-empty-text">Aún no hay datos. Completa el primer bloque.</p>
      </div>
    );
  }

  const handleSave = (fieldKey, newValue) => {
    if (onFieldSave) onFieldSave(fieldKey, newValue);
  };

  return (
    <div className="preview-list">
      {entries.map(([key, value]) => {
        const info = FIELD_INFO[key] || { label: key, description: "" };
        return (
          <EditableFieldRow
            key={key}
            fieldKey={key}
            value={value}
            label={info.label}
            tooltip={info.tooltip}
            schemaInfo={schemaInfo}
            onSave={handleSave}
          />
        );
      })}
    </div>
  );
}
