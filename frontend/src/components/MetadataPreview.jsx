// src/components/MetadataPreview.jsx
import { useState } from "react";

const FIELD_INFO = {
  title: { label: "Título", description: "Nombre del dataset" },
  notes: { label: "Descripción", description: "Descripción del contenido" },
  identifier: { label: "Identificador", description: "DOI o identificador único" },
  name: { label: "URL", description: "Dirección en el portal" },
  access_rights: { label: "Derechos de acceso", description: "Quién puede acceder" },
  hdab: { label: "Organismo de acceso (HDAB)", description: "Entidad gestora del acceso" },
  applicable_legislation: { label: "Legislación aplicable", description: "Marco legal" },
  health_category: { label: "Categoría sanitaria", description: "Categoría EHDS" },
  theme: { label: "Tema", description: "Tema principal del dataset" },
  dcat_type: { label: "Tipo de dataset", description: "Tipo según Publications Office" },
  provenance: { label: "Procedencia", description: "Origen de los datos" },
  keyword: { label: "Palabras clave", description: "Etiquetas descriptivas" },
  contact: { label: "Punto de contacto", description: "Contacto para consultas" },
  access_url: { label: "URL de Acceso", description: "URL de acceso al dataset" },
  distribution: { label: "Distribución", description: "URL de acceso al dataset" },
  purpose: { label: "Finalidad", description: "Propósito del dataset" },
  language: { label: "Idioma", description: "Idioma en el que están disponibles los datos" },
  population_coverage: { label: "Cobertura poblacional", description: "Población cubierta por el dataset" },
  number_of_unique_individuals: { label: "Número de personas individuales", description: "Número de personas únicas representadas en el dataset" },
  number_of_records: { label: "Número de registros", description: "Número total de registros en el dataset" },
  min_typical_age: { label: "Edad mínima típica", description: "Edad mínima típica de los individuos representados en el dataset" },
  max_typical_age: { label: "Edad máxima típica", description: "Edad máxima típica de los individuos representados en el dataset" },
  personal_data: { label: "Datos personales", description: "Indica si el dataset contiene datos personales" },
  legal_basis: { label: "Base jurídica", description: "Base jurídica del tratamiento" },
  retention_period: { label: "Periodo de conservación", description: "Periodo de conservación de los datos" },
  coding_system: { label: "Sistema de codificación", description: "Sistema de codificación utilizado" },
  health_theme: { label: "Tema de salud", description: "Tema de salud específico" },
  code_values: { label: "Valores codificados", description: "Valores codificados del dataset" },
  publisher: { label: "Editor", description: "Organización que publica el dataset" },
  publisher_note: { label: "Nota del editor", description: "Notas adicionales del editor" },
  creator: { label: "Creador", description: "Organización o persona que creó el dataset" },
  qualified_attribution: { label: "Atribución cualificada", description: "Agente con rol específico" },
  was_generated_by: { label: "Se generó por", description: "Actividad sanitaria que generó los datos" },
  spatial: { label: "Cobertura geográfica", description: "Países o territorios cubiertos" },
  temporal_coverage: { label: "Cobertura temporal", description: "Periodo temporal cubierto" },
  temporal_resolution: { label: "Resolución temporal", description: "Mínima resolución temporal" },
  spatial_resolution_in_meters: { label: "Resolución espacial (m)", description: "Resolución espacial en metros" },
  frequency: { label: "Frecuencia", description: "Frecuencia de actualización" },
  issued: { label: "Fecha de publicación", description: "Fecha de publicación original" },
  modified: { label: "Fecha de modificación", description: "Última modificación" },
  alternate_identifier: { label: "Identificador alternativo", description: "DOI, URN u otros identificadores" },
  conforms_to: { label: "Se ajusta a", description: "Estándar al que se ajusta" },
  related_resource: { label: "Recurso relacionado", description: "Recurso relacionado" },
  is_referenced_by: { label: "Referenciado por", description: "Recursos que referencian este dataset" },
  url: { label: "Página de entrada", description: "Landing page del dataset" },
  documentation: { label: "Documentación", description: "Documentación asociada" },
  version: { label: "Versión", description: "Versión actual" },
  has_version: { label: "Tiene versión", description: "Versiones disponibles" },
  version_notes: { label: "Notas de versión", description: "Notas sobre la versión" },
};

// Campos que se pueden editar inline (tipos simples de texto)
const EDITABLE_FIELDS = new Set([
  "title", "notes", "identifier", "name", "provenance", "keyword",
  "purpose", "population_coverage", "number_of_unique_individuals",
  "number_of_records", "min_typical_age", "max_typical_age",
  "publisher_note", "temporal_resolution", "spatial_resolution_in_meters",
  "issued", "modified", "alternate_identifier", "version",
  "has_version", "version_notes", "access_url",
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
function EditableFieldRow({ fieldKey, value, label, schemaInfo, onSave }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(typeof value === "string" ? value : "");
  const isEditable = EDITABLE_FIELDS.has(fieldKey) && typeof value === "string";

  const handleSave = () => {
    onSave(fieldKey, draft);
    setEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSave();
    if (e.key === "Escape") setEditing(false);
  };

  const formatted = formatValue(fieldKey, value, schemaInfo);
  if (!formatted) return null;

  return (
    <div
      className="field-row"
      style={{ position: "relative" }}
    >
      <div className="field-key">{label}</div>
      <div className="field-val" style={{ flex: 1 }}>
        {editing ? (
          <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
            <input
              autoFocus
              style={{
                flex: 1,
                border: "1px solid #0f62fe",
                padding: "4px 8px",
                fontSize: "0.85rem",
                fontFamily: "'IBM Plex Sans', sans-serif",
                outline: "none",
                background: "white",
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
            schemaInfo={schemaInfo}
            onSave={handleSave}
          />
        );
      })}
    </div>
  );
}
