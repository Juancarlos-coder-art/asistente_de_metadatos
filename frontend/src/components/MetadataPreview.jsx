// src/components/MetadataPreview.jsx
import { useState } from "react";

const FIELD_INFO = {
  title: { label: "Título", tooltip: "Nombre oficial del dataset. Debe ser claro, descriptivo y único. Ejemplo: 'Casos de Mpox en España 2023'." },
  notes: { label: "Descripción", tooltip: "Descripción completa del contenido, alcance, metodología y propósito del dataset." },
  identifier: { label: "Identificador", tooltip: "Identificador único y persistente del dataset, preferiblemente un DOI. Para datasets no públicos se asigna automáticamente." },
  name: { label: "URL", tooltip: "Dirección URL del dataset en el portal de datos." },
  access_rights: { label: "Derechos de acceso", tooltip: "Indica quién puede acceder al dataset: Público, Restringido, No público o Sensible." },
  hdab: { label: "Organismo de acceso (HDAB)", tooltip: "Health Data Access Body: organismo responsable de gestionar y autorizar el acceso a los datos sanitarios según el Reglamento EHDS." },
  applicable_legislation: { label: "Legislación aplicable", tooltip: "Marco legal bajo el que se tratan los datos. El GDPR es obligatorio para datasets con datos personales." },
  health_category: { label: "Categoría sanitaria", tooltip: "Categoría del dato sanitario según el Artículo 33 del Reglamento EHDS." },
  theme: { label: "Tema", tooltip: "Tema principal del dataset según el vocabulario europeo DCAT-AP." },
  dcat_type: { label: "Tipo de dataset", tooltip: "Tipo de dataset según el vocabulario de la Publications Office de la UE." },
  provenance: { label: "Procedencia", tooltip: "Descripción del origen de los datos: cómo se recogieron, de qué fuentes provienen y qué transformaciones han sufrido." },
  keyword: { label: "Palabras clave", tooltip: "Etiquetas descriptivas que facilitan la búsqueda y descubrimiento del dataset." },
  contact: { label: "Punto de contacto", tooltip: "Persona u organismo al que dirigirse para consultas sobre el dataset." },
  access_url: { label: "URL de Acceso", tooltip: "URL donde se puede acceder o solicitar acceso al dataset. Obligatoria según DCAT-AP y HealthDCAT-AP." },
  download_url: { label: "URL de descarga", tooltip: "URL de descarga directa del fichero de datos." },
  description: { label: "Descripción de la distribución", tooltip: "Descripción específica de esta distribución del dataset." },
  license: { label: "Licencia", tooltip: "Licencia bajo la que se publican los datos. Ejemplos: CC BY 4.0, CC BY-NC, CC0." },
  format: { label: "Formato", tooltip: "Formato técnico del fichero de distribución. Ejemplos: CSV, JSON, XML, XLSX, Parquet, RDF." },
  mimetype: { label: "Tipo de medio", tooltip: "Tipo MIME del fichero para sistemas informáticos. Ejemplos: text/csv, application/json." },
  compress_format: { label: "Formato de compresión", tooltip: "Formato de compresión aplicado al fichero. Ejemplos: zip, gzip, bzip2." },
  package_format: { label: "Formato de empaquetado", tooltip: "Formato de empaquetado cuando la distribución agrupa varios ficheros." },
  size: { label: "Tamaño (bytes)", tooltip: "Tamaño del fichero de distribución en bytes." },
  hash: { label: "Hash", tooltip: "Valor hash del fichero para verificar su integridad." },
  hash_algorithm: { label: "Algoritmo hash", tooltip: "Algoritmo criptográfico usado para calcular el hash. Ejemplos: MD5, SHA-256, SHA-512." },
  rights: { label: "Derechos", tooltip: "Declaración de derechos de uso del recurso." },
  availability: { label: "Disponibilidad", tooltip: "Indica durante cuánto tiempo estará disponible esta distribución." },
  status: { label: "Estado", tooltip: "Estado actual del recurso según ADMS: Completado, En desarrollo, Obsoleto o Retirado." },
  distribution: { label: "Distribución", tooltip: "Representación física o accesible del dataset." },
  purpose: { label: "Finalidad", tooltip: "Propósito para el que se recogieron y pueden usarse los datos. Importante para cumplimiento del GDPR." },
  language: { label: "Idioma", tooltip: "Idioma o idiomas en los que están disponibles los datos y la documentación del dataset." },
  population_coverage: { label: "Cobertura poblacional", tooltip: "Descripción de la población representada en el dataset." },
  number_of_unique_individuals: { label: "Número de personas individuales", tooltip: "Número de personas únicas representadas en el dataset." },
  number_of_records: { label: "Número de registros", tooltip: "Número total de filas, observaciones o entradas en el dataset." },
  min_typical_age: { label: "Edad mínima típica", tooltip: "Edad mínima típica de los individuos representados." },
  max_typical_age: { label: "Edad máxima típica", tooltip: "Edad máxima típica de los individuos representados." },
  personal_data: { label: "Datos personales", tooltip: "Categorías de datos personales presentes en el dataset según el vocabulario DPV-PD." },
  legal_basis: { label: "Base jurídica", tooltip: "Base jurídica del tratamiento de datos personales según el Art. 6 del GDPR." },
  retention_period: { label: "Periodo de conservación", tooltip: "Periodo durante el cual se conservarán los datos, con fechas de inicio y fin." },
  coding_system: { label: "Sistema de codificación", tooltip: "Sistema de codificación médica utilizado en el dataset. Ejemplos: ICD-10, SNOMED CT, LOINC." },
  health_theme: { label: "Tema de salud", tooltip: "Tema de salud específico del dataset según la taxonomía OMS/EHDS." },
  code_values: { label: "Valores codificados", tooltip: "Lista de valores o códigos utilizados en el dataset para representar categorías." },
  publisher: { label: "Editor", tooltip: "Organización responsable de publicar el dataset. Incluye nombre, tipo, correo, teléfono y página web." },
  publisher_note: { label: "Nota del editor", tooltip: "Notas adicionales del editor sobre el dataset: advertencias de uso, limitaciones conocidas." },
  creator: { label: "Creador", tooltip: "Persona u organización que creó o generó los datos originales." },
  qualified_attribution: { label: "Atribución cualificada", tooltip: "Agente con un rol específico en la creación, gestión o publicación del dataset." },
  quality_annotation: { label: "Anotación de calidad", tooltip: "Anotación sobre la calidad del dataset según el modelo W3C OA. Incluye organismo, objetivo y motivación." },
  was_generated_by: { label: "Se generó por", tooltip: "Actividad o proceso sanitario que generó los datos. Ejemplos: ensayo clínico, encuesta de salud, registros hospitalarios." },
  spatial: { label: "Cobertura geográfica", tooltip: "Países o territorios cubiertos por el dataset." },
  temporal_coverage: { label: "Cobertura temporal", tooltip: "Periodo temporal cubierto por los datos, con fecha de inicio y fin." },
  temporal_resolution: { label: "Resolución temporal", tooltip: "Mínima granularidad temporal de los datos en formato ISO 8601. Ejemplos: P1D (diaria), PT1H (horaria)." },
  spatial_resolution_in_meters: { label: "Resolución espacial (m)", tooltip: "Resolución espacial mínima de los datos en metros." },
  frequency: { label: "Frecuencia", tooltip: "Frecuencia con la que se actualiza el dataset." },
  issued: { label: "Fecha de publicación", tooltip: "Fecha en que el dataset fue publicado por primera vez (YYYY-MM-DD)." },
  modified: { label: "Fecha de modificación", tooltip: "Fecha de la última modificación del dataset (YYYY-MM-DD)." },
  alternate_identifier: { label: "Identificador alternativo", tooltip: "Identificadores adicionales del dataset en otros sistemas: DOI, URN, handle." },
  conforms_to: { label: "Se ajusta a", tooltip: "Estándar o especificación al que se ajusta el dataset. Ejemplos: HealthDCAT-AP, DCAT-AP 3.0." },
  related_resource: { label: "Recurso relacionado", tooltip: "Recursos externos relacionados: publicaciones científicas, informes, otros datasets." },
  is_referenced_by: { label: "Referenciado por", tooltip: "Recursos que citan o referencian este dataset." },
  url: { label: "Página de entrada", tooltip: "URL de la página web principal del dataset en el portal de datos." },
  documentation: { label: "Documentación", tooltip: "Documentación técnica asociada: diccionario de variables, manual de usuario, protocolo de recogida." },
  version: { label: "Versión", tooltip: "Número o código de la versión actual del dataset." },
  has_version: { label: "Tiene versión", tooltip: "Lista de versiones disponibles del dataset." },
  version_notes: { label: "Notas de versión", tooltip: "Descripción de los cambios introducidos en esta versión respecto a la anterior." },
};

// ── Vocabularios de etiquetas ──────────────────────────────────────────────
const HEALTH_CATEGORY_LABELS = {
  "EHRS": "Registros Electrónicos de Salud",
  "HRAD": "Datos administrativos relacionados con la salud",
  "MRMR": "Datos de registros médicos y registros de mortalidad",
  "RPDG": "Datos de patógenos que afectan a la salud humana",
  "RQSH": "Datos de cohortes de investigación y encuestas de salud",
  "PHDR": "Registros de datos de salud basados en la población",
  "EHCT": "Datos de ensayos clínicos e investigaciones clínicas",
  "HGPD": "Datos genéticos, epigenómicos y genómicos humanos",
  "EINS": "Datos de salud de biobancos y bases de datos asociadas",
  "EMRD": "Otros datos de salud de dispositivos médicos",
  "HPML": "Otros datos moleculares humanos",
  "WELA": "Datos de aplicaciones de bienestar",
  "RMMD": "Datos de registros de productos medicinales y dispositivos médicos",
  "NRPE": "Datos agregados sobre necesidades de atención sanitaria",
  "PGEH": "Datos electrónicos de salud personales generados automáticamente",
  "IDHP": "Datos sobre estado profesional de profesionales de la salud",
  "DIOH": "Datos sobre factores que afectan a la salud",
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
  "OP_DATPRO": "Datos Provisionales", "IEPD": "Descripción de paquete de intercambio",
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
  "pharma-company": "Empresas Farmacéuticas",
  "private-sector-entities": "Entidades del sector privado",
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
  "other-company": "Otro tipo de empresa que recopila datos de salud",
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
  "COHORT": "Cohorte", "SAMPLE_COLLECTIONS": "Colecciones de muestras",
  "OBSERVATIONAL_DATA": "Datos de observación", "CENSUS_DATA": "Datos del censo",
  "PROBABILITY_SURVEY": "Encuesta de probabilidad", "HEALTH_SURVEY": "Encuesta de salud",
  "CLINICAL_TRIAL": "Ensayo clínico", "AUTOMATIC_GENERATION": "Generado automáticamente",
  "ADMISSION_DISCHARGE": "Ingreso, atención y alta del paciente",
  "MEASUREMENTS": "Mediciones", "MODELS_SIMULATIONS": "Modelos y simulaciones",
  "PRESCRIBING_DISPENSING": "Prescripción o dispensación de medicamentos",
  "ADMINISTRATIVE_PROCESSES": "Procesos administrativos",
  "PATIENT_OUTCOMES": "PROM (Medidas de resultados comunicados por los pacientes)",
  "RESEARCH_PROJECT": "Proyecto de investigación",
  "LABORATORY_TESTS": "Pruebas de laboratorio",
  "INSURANCE_CLAIMS": "Reclamaciones, seguros y reembolsos",
  "QUALITY_REGISTRY": "Registro de Calidad", "MEDICAL_REGISTRY": "Registro médico",
  "ROUTINE_RECORDS": "Registros de rutina (no sanitarios)",
  "QUALITY_REGISTRIES": "Registros Nacionales de Calidad Médica",
  "HEALTH_REGISTRIES": "Registros Nacionales de Salud",
  "MUNICIPAL_REPOSITORY": "Repositorio municipal de datos sanitarios",
  "GEOSPATIAL_MONITORING": "Seguimiento geoespacial",
  "MEDICAL_DEVICES": "Uso de productos sanitarios", "SURVEILLANCE": "Vigilancia",
  "DISEASE_MONITORING": "Vigilancia de enfermedades infecciosas",
  "HEALTH_SURVEILLANCE": "Vigilancia de la salud pública",
  "HEALTHCARE_VISIT": "Visita sanitaria",
};
const HEALTH_THEME_LABELS = {
  "CLIMATE_HEALTH": "Clima y salud planetaria", "CANCER_DISEASE": "Cáncer",
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
  "DAILY": "Diario", "DAILY_2": "Dos veces al día",
  "AS_NEEDED": "En función de las necesidades", "IRREG": "Irregular",
  "MONTHLY": "Mensual", "NOT_PLANNED": "No previsto", "NEVER": "Nunca",
  "OTHER": "Otro", "BIWEEKLY": "Quincenal", "WEEKLY": "Semanal",
  "ANNUAL_2": "Semestral", "QUARTERLY": "Trimestral",
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
const ROLE_LABELS = {
  "author": "Autor", "coAuthor": "Co autor", "collaborator": "Colaborador",
  "contributor": "Contribuyente", "custodian": "Custodio", "distributor": "Distribuidor",
  "publisher": "Editor", "funder": "Financiador",
  "principalInvestigator": "Investigador principal", "originator": "Originador",
  "owner": "Propietario", "pointOfContact": "Punto de contacto",
  "rightsHolder": "Titular de los derechos", "user": "Usuario",
};
const STATUS_LABELS = {
  "http://purl.org/adms/status/Completed": "Completado",
  "http://purl.org/adms/status/UnderDevelopment": "En desarrollo",
  "http://purl.org/adms/status/Deprecated": "Obsoleto",
  "http://purl.org/adms/status/Withdrawn": "Retirado",
};
const ACCESS_RIGHTS_LABELS = {
  PUBLIC: "Público", RESTRICTED: "Restringido", CONFIDENTIAL: "Confidencial",
  NON_PUBLIC: "No público", SENSITIVE: "Sensible", NORMAL: "Normal",
  OP_DATPRO: "Datos provisionales",
};

// ── Formato solo para mostrar (no edición) ────────────────────────────────
function formatDisplayValue(key, value) {
  if (value === null || value === undefined || value === "") return null;

  if (key === "access_rights" && typeof value === "string")
    return ACCESS_RIGHTS_LABELS[value.split("/").pop()] || value.split("/").pop();

  if (key === "health_category" && Array.isArray(value))
    return value.map(u => HEALTH_CATEGORY_LABELS[u.split("/").pop()] || u.split("/").pop()).join(", ");

  if (key === "theme" && Array.isArray(value))
    return value.map(u => THEME_LABELS[u.split("/").pop()] || u.split("/").pop()).join(", ");

  if (key === "dcat_type" && typeof value === "string")
    return DCAT_TYPE_LABELS[value.split("/").pop()] || value.split("/").pop();

  if (key === "language" && Array.isArray(value))
    return value.map(u => LANGUAGE_LABELS[u.split("/").pop()] || u.split("/").pop()).join(", ");

  if (key === "personal_data" && Array.isArray(value))
    return value.map(u => PERSONAL_DATA_LABELS[u.split("#").pop()] || u.split("#").pop().replace(/([a-z])([A-Z])/g, "$1 $2")).join(", ");

  if (key === "was_generated_by" && Array.isArray(value))
    return value.map(u => HEALTH_ACTIVITY_LABELS[u.split("/").pop()] || u.split("/").pop()).join(", ");

  if (key === "health_theme" && Array.isArray(value))
    return value.map(u => HEALTH_THEME_LABELS[u.split("/").pop()] || u.split("/").pop()).join(", ");

  if (key === "spatial" && Array.isArray(value))
    return value.map(u => COUNTRY_LABELS[u.split("/").pop()] || u.split("/").pop()).join(", ");

  if (key === "frequency" && typeof value === "string")
    return FREQUENCY_LABELS[value.split("/").pop()] || value.split("/").pop();

  if (key === "status" && typeof value === "string")
    return STATUS_LABELS[value] || value.split("/").pop();

  if ((key === "access_url" || key === "download_url") && typeof value === "string")
    return <a href={value} target="_blank" rel="noreferrer">{value}</a>;

  if (key === "applicable_legislation" && Array.isArray(value))
    return value.map((v, i) => <span key={i}>{v.label || v.uri}</span>);

  if (key === "distribution" && Array.isArray(value))
    return value.map((dist, i) => dist.access_url && (
      <span key={i}><a href={dist.access_url} target="_blank" rel="noreferrer">{dist.access_url}</a></span>
    ));

  if (key === "hdab" && typeof value === "object" && !Array.isArray(value)) {
    const typeCode = value.type ? value.type.split("/").pop() : null;
    const freqCode = value.opening_hours_frequency ? value.opening_hours_frequency.split("/").pop() : null;
    const sfreqCode = value.special_opening_hours_frequency ? value.special_opening_hours_frequency.split("/").pop() : null;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {value.name && <span><strong>Nombre:</strong> {value.name}</span>}
        {typeCode && <span><strong>Tipo:</strong> {PUBLISHER_TYPE_LABELS[typeCode] || typeCode}</span>}
        {(value.contact || value.contact_page) && <span><strong>Contacto:</strong> {value.contact || value.contact_page}</span>}
        {value.email && <span><strong>Correo:</strong> {value.email}</span>}
        {value.telephone && <span><strong>Teléfono:</strong> {value.telephone}</span>}
        {value.opening_hours_description && <span><strong>Horario:</strong> {value.opening_hours_description}</span>}
        {freqCode && <span><strong>Frec. horario:</strong> {FREQUENCY_LABELS[freqCode] || freqCode}</span>}
        {value.special_opening_hours_description && <span><strong>Horario especial:</strong> {value.special_opening_hours_description}</span>}
        {sfreqCode && <span><strong>Frec. horario especial:</strong> {FREQUENCY_LABELS[sfreqCode] || sfreqCode}</span>}
      </div>
    );
  }

  if (key === "contact") {
    const v = Array.isArray(value) ? value[0] : value;
    if (typeof v === "object") return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {v.email && <span><strong>Correo:</strong> {v.email}</span>}
        {v.url && <span><strong>Web:</strong> <a href={v.url} target="_blank" rel="noreferrer">{v.url}</a></span>}
      </div>
    );
  }

  if (key === "legal_basis") {
    const v = Array.isArray(value) ? value[0] : value;
    if (typeof v === "object") return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {v.description && <span><strong>Descripción:</strong> {v.description}</span>}
        {v.source && <span><strong>Fuente:</strong> {v.source}</span>}
      </div>
    );
  }

  if (key === "retention_period") {
    const v = Array.isArray(value) ? value[0] : value;
    if (typeof v === "object") return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {v.start && <span><strong>Inicio:</strong> {v.start}</span>}
        {v.end && <span><strong>Fin:</strong> {v.end}</span>}
      </div>
    );
  }

  if (key === "coding_system") {
    const v = Array.isArray(value) ? value[0] : value;
    if (typeof v === "object") return <span>{v.label || v.uri}</span>;
    return <span>{v}</span>;
  }

  if (key === "publisher" && typeof value === "object" && !Array.isArray(value)) {
    const typeCode = value.type ? value.type.split("/").pop() : null;
    const freqCode = value.opening_hours_frequency ? value.opening_hours_frequency.split("/").pop() : null;
    const sfreqCode = value.special_opening_hours_frequency ? value.special_opening_hours_frequency.split("/").pop() : null;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {value.name && <span><strong>Nombre:</strong> {value.name}</span>}
        {typeCode && <span><strong>Tipo:</strong> {PUBLISHER_TYPE_LABELS[typeCode] || typeCode}</span>}
        {value.contact_page && <span><strong>Contacto:</strong> {value.contact_page}</span>}
        {value.email && <span><strong>Correo:</strong> {value.email}</span>}
        {value.telephone && <span><strong>Teléfono:</strong> {value.telephone}</span>}
        {value.opening_hours_description && <span><strong>Horario:</strong> {value.opening_hours_description}</span>}
        {freqCode && <span><strong>Frec. horario:</strong> {FREQUENCY_LABELS[freqCode] || freqCode}</span>}
        {value.special_opening_hours_description && <span><strong>Horario especial:</strong> {value.special_opening_hours_description}</span>}
        {sfreqCode && <span><strong>Frec. horario especial:</strong> {FREQUENCY_LABELS[sfreqCode] || sfreqCode}</span>}
      </div>
    );
  }

  if (key === "creator") {
    const v = Array.isArray(value) ? value[0] : value;
    if (typeof v === "object") {
      const typeCode = v.type ? v.type.split("/").pop() : null;
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
          {v.name && <span><strong>Nombre:</strong> {v.name}</span>}
          {typeCode && <span><strong>Tipo:</strong> {PUBLISHER_TYPE_LABELS[typeCode] || typeCode}</span>}
          {v.email && <span><strong>Correo:</strong> {v.email}</span>}
          {v.url && <span><strong>URL:</strong> {v.url}</span>}
        </div>
      );
    }
  }

  if (key === "qualified_attribution") {
    const v = Array.isArray(value) ? value[0] : value;
    if (typeof v === "object") {
      const typeCode = (v.qualified_attribution_agent_type || "").split("/").pop();
      const roleCode = (v.qualified_attribution_role || v.role || "").split("#").pop();
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
          {(v.qualified_attribution_agent_name || v.name) && <span><strong>Nombre:</strong> {v.qualified_attribution_agent_name || v.name}</span>}
          {typeCode && <span><strong>Tipo:</strong> {PUBLISHER_TYPE_LABELS[typeCode] || typeCode}</span>}
          {(v.qualified_attribution_agent_email || v.email) && <span><strong>Correo:</strong> {v.qualified_attribution_agent_email || v.email}</span>}
          {roleCode && <span><strong>Rol:</strong> {ROLE_LABELS[roleCode] || roleCode}</span>}
        </div>
      );
    }
  }

  if (key === "quality_annotation" && typeof value === "object" && !Array.isArray(value)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {value.body && <span><strong>Organismo:</strong> {value.body}</span>}
        {value.target && <span><strong>Objetivo:</strong> {value.target}</span>}
        {value.motivated_by && <span><strong>Motivación:</strong> {value.motivated_by}</span>}
      </div>
    );
  }

  if (key === "temporal_coverage" && typeof value === "object" && !Array.isArray(value)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {value.start && <span><strong>Inicio:</strong> {value.start}</span>}
        {value.end && <span><strong>Fin:</strong> {value.end}</span>}
      </div>
    );
  }

  if (["conforms_to", "related_resource", "documentation"].includes(key) && typeof value === "object" && !Array.isArray(value)) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
        {value.uri && <span><strong>URI:</strong> <a href={value.uri} target="_blank" rel="noreferrer">{value.uri}</a></span>}
        {value.label && <span><strong>Etiqueta:</strong> {value.label}</span>}
      </div>
    );
  }

  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}

// ── Editor inline para cada campo ─────────────────────────────────────────
function InlineEditor({ fieldKey, value, schemaInfo, onSave, onCancel }) {
  const [draft, setDraft] = useState(() => {
    if (typeof value === "object" && value !== null) return { ...value };
    return value ?? "";
  });

  const update = (k, v) => setDraft(prev =>
    typeof prev === "object" ? { ...prev, [k]: v } : v
  );

  const inputStyle = {
    width: "100%", boxSizing: "border-box",
    border: "1px solid #0f62fe", padding: "5px 8px",
    fontSize: "0.83rem", fontFamily: "'IBM Plex Sans', sans-serif",
    outline: "none", background: "white", marginTop: "2px",
  };
  const selectStyle = { ...inputStyle };
  const subLabelStyle = {
    fontSize: "0.75rem", color: "#525252",
    fontFamily: "'IBM Plex Sans', sans-serif",
    display: "block", marginTop: "6px", marginBottom: "1px",
  };

  // Campos de texto simple
  const SIMPLE_TEXT = [
    "title", "notes", "identifier", "name", "provenance", "keyword",
    "purpose", "population_coverage", "number_of_unique_individuals",
    "number_of_records", "min_typical_age", "max_typical_age",
    "publisher_note", "temporal_resolution", "spatial_resolution_in_meters",
    "issued", "modified", "alternate_identifier", "version",
    "has_version", "version_notes", "access_url", "download_url", "description",
    "license", "format", "mimetype", "compress_format", "package_format",
    "size", "hash", "hash_algorithm", "rights", "availability",
    "url", "is_referenced_by", "code_values",
  ];

  const renderEditor = () => {
    // Select: access_rights
    if (fieldKey === "access_rights") {
      const opts = [
        { v: "http://publications.europa.eu/resource/authority/access-right/PUBLIC", l: "Público" },
        { v: "http://publications.europa.eu/resource/authority/access-right/RESTRICTED", l: "Restringido" },
        { v: "http://publications.europa.eu/resource/authority/access-right/NON_PUBLIC", l: "No público" },
      ];
      return (
        <select style={selectStyle} value={draft} onChange={e => setDraft(e.target.value)}>
          {opts.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
        </select>
      );
    }

    // Select: status
    if (fieldKey === "status") {
      return (
        <select style={selectStyle} value={draft} onChange={e => setDraft(e.target.value)}>
          {Object.entries(STATUS_LABELS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      );
    }

    // Select: dcat_type
    if (fieldKey === "dcat_type") {
      return (
        <select style={selectStyle} value={draft} onChange={e => setDraft(e.target.value)}>
          <option value="">— Selecciona —</option>
          {Object.entries(DCAT_TYPE_LABELS).map(([code, label]) => (
            <option key={code} value={`http://publications.europa.eu/resource/authority/dataset-type/${code}`}>{label}</option>
          ))}
        </select>
      );
    }

    // Select: frequency
    if (fieldKey === "frequency") {
      return (
        <select style={selectStyle} value={draft} onChange={e => setDraft(e.target.value)}>
          <option value="">— Selecciona —</option>
          {Object.entries(FREQUENCY_LABELS).map(([code, label]) => (
            <option key={code} value={`http://publications.europa.eu/resource/authority/frequency/${code}`}>{label}</option>
          ))}
        </select>
      );
    }

    // Campos de texto simple
    if (SIMPLE_TEXT.includes(fieldKey)) {
      return (
        <input style={inputStyle} value={draft}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter") onSave(draft); if (e.key === "Escape") onCancel(); }}
          autoFocus />
      );
    }

    // contact
    if (fieldKey === "contact") {
      const d = typeof draft === "object" ? draft : {};
      return (
        <>
          <label style={subLabelStyle}>Correo</label>
          <input style={inputStyle} value={d.email || ""} onChange={e => update("email", e.target.value)} autoFocus />
          <label style={subLabelStyle}>URL</label>
          <input style={inputStyle} value={d.url || ""} onChange={e => update("url", e.target.value)} />
        </>
      );
    }

    // legal_basis
    if (fieldKey === "legal_basis") {
      const d = typeof draft === "object" ? draft : {};
      return (
        <>
          <label style={subLabelStyle}>Descripción</label>
          <input style={inputStyle} value={d.description || ""} onChange={e => update("description", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Fuente</label>
          <input style={inputStyle} value={d.source || ""} onChange={e => update("source", e.target.value)} />
        </>
      );
    }

    // retention_period
    if (fieldKey === "retention_period") {
      const d = typeof draft === "object" ? draft : {};
      return (
        <>
          <label style={subLabelStyle}>Inicio</label>
          <input style={inputStyle} type="date" value={d.start || ""} onChange={e => update("start", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Fin</label>
          <input style={inputStyle} type="date" value={d.end || ""} onChange={e => update("end", e.target.value)} />
        </>
      );
    }

    // temporal_coverage
    if (fieldKey === "temporal_coverage") {
      const d = typeof draft === "object" ? draft : {};
      return (
        <>
          <label style={subLabelStyle}>Inicio</label>
          <input style={inputStyle} type="date" value={d.start || ""} onChange={e => update("start", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Fin</label>
          <input style={inputStyle} type="date" value={d.end || ""} onChange={e => update("end", e.target.value)} />
        </>
      );
    }

    // coding_system
    if (fieldKey === "coding_system") {
      const d = typeof draft === "object" ? draft : {};
      return (
        <>
          <label style={subLabelStyle}>URI</label>
          <input style={inputStyle} value={d.uri || ""} onChange={e => update("uri", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Etiqueta</label>
          <input style={inputStyle} value={d.label || ""} onChange={e => update("label", e.target.value)} />
        </>
      );
    }

    // conforms_to / related_resource / documentation
    if (["conforms_to", "related_resource", "documentation"].includes(fieldKey)) {
      const d = typeof draft === "object" ? draft : {};
      return (
        <>
          <label style={subLabelStyle}>URI</label>
          <input style={inputStyle} value={d.uri || ""} onChange={e => update("uri", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Etiqueta</label>
          <input style={inputStyle} value={d.label || ""} onChange={e => update("label", e.target.value)} />
        </>
      );
    }

    // quality_annotation
    if (fieldKey === "quality_annotation") {
      const d = typeof draft === "object" ? draft : {};
      return (
        <>
          <label style={subLabelStyle}>Organismo (URI)</label>
          <input style={inputStyle} value={d.body || ""} onChange={e => update("body", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Objetivo</label>
          <input style={inputStyle} value={d.target || ""} onChange={e => update("target", e.target.value)} />
          <label style={subLabelStyle}>Motivación</label>
          <input style={inputStyle} value={d.motivated_by || ""} onChange={e => update("motivated_by", e.target.value)} />
        </>
      );
    }

    // hdab
    if (fieldKey === "hdab") {
      const d = typeof draft === "object" ? draft : {};
      const typeChoices = schemaInfo?.hdab?.subfields?.find(sf => sf.field_name === "type")?.choices || [];
      return (
        <>
          <label style={subLabelStyle}>* Nombre</label>
          <input style={inputStyle} value={d.name || ""} onChange={e => update("name", e.target.value)} autoFocus />
          <label style={subLabelStyle}>* Tipo</label>
          <select style={selectStyle} value={d.type || ""} onChange={e => update("type", e.target.value)}>
            <option value="">— Selecciona —</option>
            {typeChoices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
          </select>
          <label style={subLabelStyle}>* Página de contacto</label>
          <input style={inputStyle} value={d.contact || d.contact_page || ""} onChange={e => update("contact", e.target.value)} />
          <label style={subLabelStyle}>* Correo</label>
          <input style={inputStyle} value={d.email || ""} onChange={e => update("email", e.target.value)} />
          <label style={subLabelStyle}>Teléfono</label>
          <input style={inputStyle} value={d.telephone || ""} onChange={e => update("telephone", e.target.value)} />
          <label style={subLabelStyle}>Horario habitual (descripción)</label>
          <input style={inputStyle} value={d.opening_hours_description || ""} onChange={e => update("opening_hours_description", e.target.value)} />
          <label style={subLabelStyle}>Horario especial (descripción)</label>
          <input style={inputStyle} value={d.special_opening_hours_description || ""} onChange={e => update("special_opening_hours_description", e.target.value)} />
        </>
      );
    }

    // publisher
    if (fieldKey === "publisher") {
      const d = typeof draft === "object" ? draft : {};
      const typeChoices = schemaInfo?.publisher?.subfields?.find(sf => sf.field_name === "type")?.choices || [];
      return (
        <>
          <label style={subLabelStyle}>Nombre</label>
          <input style={inputStyle} value={d.name || ""} onChange={e => update("name", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Tipo</label>
          <select style={selectStyle} value={d.type || ""} onChange={e => update("type", e.target.value)}>
            <option value="">— Selecciona —</option>
            {typeChoices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
          </select>
          <label style={subLabelStyle}>Correo</label>
          <input style={inputStyle} value={d.email || ""} onChange={e => update("email", e.target.value)} />
          <label style={subLabelStyle}>Teléfono</label>
          <input style={inputStyle} value={d.telephone || ""} onChange={e => update("telephone", e.target.value)} />
          <label style={subLabelStyle}>Página de contacto</label>
          <input style={inputStyle} value={d.contact_page || ""} onChange={e => update("contact_page", e.target.value)} />
          <label style={subLabelStyle}>Horario habitual (descripción)</label>
          <input style={inputStyle} value={d.opening_hours_description || ""} onChange={e => update("opening_hours_description", e.target.value)} />
          <label style={subLabelStyle}>Horario especial (descripción)</label>
          <input style={inputStyle} value={d.special_opening_hours_description || ""} onChange={e => update("special_opening_hours_description", e.target.value)} />
        </>
      );
    }

    // creator
    if (fieldKey === "creator") {
      const d = typeof draft === "object" ? draft : {};
      const typeChoices = schemaInfo?.creator?.subfields?.find(sf => sf.field_name === "type")?.choices || [];
      return (
        <>
          <label style={subLabelStyle}>Nombre</label>
          <input style={inputStyle} value={d.name || ""} onChange={e => update("name", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Tipo</label>
          <select style={selectStyle} value={d.type || ""} onChange={e => update("type", e.target.value)}>
            <option value="">— Selecciona —</option>
            {typeChoices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
          </select>
          <label style={subLabelStyle}>Correo</label>
          <input style={inputStyle} value={d.email || ""} onChange={e => update("email", e.target.value)} />
          <label style={subLabelStyle}>URL</label>
          <input style={inputStyle} value={d.url || ""} onChange={e => update("url", e.target.value)} />
        </>
      );
    }

    // qualified_attribution
    if (fieldKey === "qualified_attribution") {
      const d = typeof draft === "object" ? draft : {};
      const qaSubfields = schemaInfo?.qualified_attribution?.subfields || [];
      const typeChoices = qaSubfields.find(sf => sf.field_name === "qualified_attribution_agent_type")?.choices || [];
      const roleChoices = qaSubfields.find(sf => sf.field_name === "qualified_attribution_role")?.choices || [];
      return (
        <>
          <label style={subLabelStyle}>Nombre</label>
          <input style={inputStyle} value={d.qualified_attribution_agent_name || d.name || ""} onChange={e => update("qualified_attribution_agent_name", e.target.value)} autoFocus />
          <label style={subLabelStyle}>Tipo</label>
          <select style={selectStyle} value={d.qualified_attribution_agent_type || ""} onChange={e => update("qualified_attribution_agent_type", e.target.value)}>
            <option value="">— Selecciona —</option>
            {typeChoices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
          </select>
          <label style={subLabelStyle}>Correo</label>
          <input style={inputStyle} value={d.qualified_attribution_agent_email || d.email || ""} onChange={e => update("qualified_attribution_agent_email", e.target.value)} />
          <label style={subLabelStyle}>Página de contacto</label>
          <input style={inputStyle} value={d.qualified_attribution_agent_contact_page || d.contact_page || ""} onChange={e => update("qualified_attribution_agent_contact_page", e.target.value)} />
          <label style={subLabelStyle}>Rol</label>
          <select style={selectStyle} value={d.qualified_attribution_role || d.role || ""} onChange={e => update("qualified_attribution_role", e.target.value)}>
            <option value="">— Selecciona —</option>
            {roleChoices.map(ch => <option key={ch.value} value={ch.value}>{ch.label}</option>)}
          </select>
        </>
      );
    }

    // Fallback
    return (
      <input style={inputStyle} value={typeof draft === "string" ? draft : JSON.stringify(draft)}
        onChange={e => setDraft(e.target.value)} autoFocus />
    );
  };

  return (
    <div style={{ width: "100%" }}>
      {renderEditor()}
      <div style={{ display: "flex", gap: "6px", marginTop: "8px" }}>
        <button onClick={() => onSave(draft)} style={{
          background: "#0f62fe", color: "white", border: "none",
          padding: "4px 14px", fontSize: "0.78rem", cursor: "pointer",
          fontFamily: "'IBM Plex Mono', monospace",
        }}>✓ Guardar</button>
        <button onClick={onCancel} style={{
          background: "transparent", color: "#525252", border: "1px solid #c6c6c6",
          padding: "4px 10px", fontSize: "0.78rem", cursor: "pointer",
        }}>✕</button>
      </div>
    </div>
  );
}

// ── Fila editable ──────────────────────────────────────────────────────────
function EditableFieldRow({ fieldKey, value, label, tooltip, schemaInfo, onSave }) {
  const [editing, setEditing] = useState(false);
  const [tooltipPos, setTooltipPos] = useState(null);

  const handleInfoClick = (e) => {
    if (tooltipPos) { setTooltipPos(null); return; }
    const rect = e.currentTarget.getBoundingClientRect();
    setTooltipPos({
      top: rect.bottom + 6,
      left: Math.min(rect.left, window.innerWidth - 360),
    });
  };

  const formatted = formatDisplayValue(fieldKey, value);
  if (!formatted) return null;

  return (
    <div className="field-row" style={{ position: "relative", alignItems: "flex-start" }}>
      {tooltipPos && (
        <>
          <div onClick={() => setTooltipPos(null)}
            style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, zIndex: 999 }} />
          <div style={{
            position: "fixed", top: tooltipPos.top, left: tooltipPos.left, zIndex: 1000,
            background: "#1c1c1c", color: "#f4f4f4", fontSize: "0.82rem", lineHeight: 1.6,
            padding: "14px 16px", width: "340px", boxShadow: "0 8px 24px rgba(0,0,0,0.45)",
            fontFamily: "'IBM Plex Sans', sans-serif", borderLeft: "3px solid #0f62fe", borderRadius: "2px",
          }}>
            <div style={{ fontWeight: 600, marginBottom: "6px", color: "#78a9ff", fontSize: "0.85rem", fontFamily: "'IBM Plex Mono', monospace" }}>
              {label}
            </div>
            {tooltip}
          </div>
        </>
      )}

      <div className="field-key" style={{ display: "flex", alignItems: "center", gap: "5px", paddingTop: "2px" }}>
        <span>{label}</span>
        {tooltip && (
          <button onClick={handleInfoClick} title="Más información" style={{
            background: "none", border: "1.5px solid #0f62fe", cursor: "pointer",
            color: "#0f62fe", fontSize: "0.68rem", padding: "0", fontWeight: 700,
            fontFamily: "serif", width: "14px", height: "14px", minWidth: "14px",
            display: "inline-flex", alignItems: "center", justifyContent: "center",
            borderRadius: "50%", flexShrink: 0, lineHeight: 1,
          }}>i</button>
        )}
      </div>

      <div className="field-val" style={{ flex: 1 }}>
        {editing ? (
          <InlineEditor
            fieldKey={fieldKey}
            value={value}
            schemaInfo={schemaInfo}
            onSave={(newVal) => { onSave(fieldKey, newVal); setEditing(false); }}
            onCancel={() => setEditing(false)}
          />
        ) : (
          <span>{formatted}</span>
        )}
      </div>

      {!editing && (
        <button
          onClick={() => setEditing(true)}
          style={{
            background: "transparent", border: "1px solid #0f62fe",
            cursor: "pointer", color: "#0f62fe", fontSize: "0.72rem",
            padding: "2px 8px", fontFamily: "'IBM Plex Mono', monospace",
            flexShrink: 0, letterSpacing: "0.03em",
          }}
        >Editar</button>
      )}
    </div>
  );
}

// ── Componente principal ───────────────────────────────────────────────────
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

  return (
    <div className="preview-list">
      {entries.map(([key, value]) => {
        const info = FIELD_INFO[key] || { label: key, tooltip: null };
        return (
          <EditableFieldRow
            key={key}
            fieldKey={key}
            value={value}
            label={info.label}
            tooltip={info.tooltip}
            schemaInfo={schemaInfo}
            onSave={(fieldKey, newValue) => onFieldSave && onFieldSave(fieldKey, newValue)}
          />
        );
      })}
    </div>
  );
}
