// src/components/MetadataPreview.jsx

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
};

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
  "HEAL": "Salud",
  "TECH": "Ciencia y Tecnología",
  "SOCI": "Población y sociedad",
  "GOVE": "Gobierno y sector público",
  "EDUC": "Educación, cultura y deportes",
  "ECON": "Economía y finanzas",
  "ENVI": "Medio ambiente",
  "AGRI": "Agricultura, pesca, silvicultura y alimentación",
  "TRAN": "Transporte",
  "JUST": "Justicia, sistema judicial y seguridad pública",
  "REGI": "Regiones y ciudades",
  "INTR": "Asuntos Internacionales",
  "ENER": "Energía",
  "OP_DATPRO": "Datos provisionales",
};

const DCAT_TYPE_LABELS = {
  "STATISTICAL": "Datos Estadísticos",
  "GEOSPATIAL": "Datos Geoespaciales",
  "HVD": "Conjunto de datos de alto valor",
  "SYNTHETIC_DATA": "Datos Sintéticos",
  "ONTOLOGY": "Ontología",
  "SCHEMA": "Esquema",
  "CODE_LIST": "Lista de Códigos",
  "APROF": "Perfil de Aplicación",
  "TEST_DATA": "Datos de Prueba",
  "CORE_COMP": "Componente básico",
  "MAPPING": "Correspondencia",
  "DIRECTORY": "Directorio",
  "GLOSSARY": "Glosario",
  "THESAURUS": "Tesauro",
  "TAXONOMY": "Taxonomía",
  "DOMAIN_MODEL": "Modelo de Dominio",
  "RELEASE": "Publicación",
  "ATTO_LEX": "Cuadro ATTO – dominio EUR-Lex",
  "ATTO_PUB": "Cuadro ATTO – dominio Publicaciones",
  "OP_DATPRO": "Datos Provisionales",
  "IEPD": "Descripción de un paquete de intercambio de información",
  "DSCRP_SERV": "Descripción del Servicio",
  "STYLES": "Hojas de Estilo",
  "NAL": "Lista Autorizada de Nombres",
  "SYNTAX_ECD_SCHEME": "Esquema de codificación sintáctica",
};

const PUBLISHER_TYPE_LABELS = {
  "public-health-institute": "Instituto de Salud Pública",
  "research-institute-org": "Instituto/organización de investigación",
  "national-authority": "Autoridad Nacional",
  "regional-authority": "Autoridad Regional",
  "university": "Universidad",
  "public-health-registry": "Registro de Salud Pública",
  "public-health-org": "Organización de Salud Pública",
  "stat-agency": "Agencia de estadísticas",
  "biobank": "Biobanco",
  "inpatient-institute": "Institución de hospitalización/Hospital",
  "laboratory": "Laboratorio",
  "private-company": "Empresa Privada",
  "gov-public-sector-org": "Organizaciones gubernamentales y del sector público",
  "healthcare-providers": "Proveedor de Atención Médica",
  "health-insurance-company-org": "Compañía/organización de seguros de salud",
  "pharma-company": "Empresas Farmacéuticas",
  "private-sector-entities": "Entidades del sector privado",
  "health-technology-manufacturer": "Fabricante de aplicaciones/tecnología de salud",
  "software-manufacturer": "Fabricante de software",
  "pharmacy": "Farmacia",
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
  "quality-registry": "Registro de Calidad",
  "pathology-registry": "Registro de Patología",
  "private-health-insurance": "Seguro de salud privado",
};

function formatValue(key, value) {
  if (value === null || value === undefined || value === "") return null;

  // access_rights
  if (key === "access_rights" && typeof value === "string") {
    const code = value.split("/").pop();
    const map = {
      PUBLIC: "Público",
      RESTRICTED: "Restringido",
      CONFIDENTIAL: "Confidencial",
      NON_PUBLIC: "No público",
      SENSITIVE: "Sensible",
      NORMAL: "Normal",
      OP_DATPRO: "Datos provisionales",
    };
    return map[code] || code;
  }

  // hdab — objeto con subcampos
  if (key === "hdab" && typeof value === "object") {
    const typeCode = value.type ? value.type.split("/").pop() : null;
    const typeLabel = typeCode ? (PUBLISHER_TYPE_LABELS[typeCode] || typeCode) : null;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.name && <span><strong>Nombre:</strong> {value.name}</span>}
        {value.email && <span><strong>Email:</strong> {value.email}</span>}
        {value.telephone && <span><strong>Teléfono:</strong> {value.telephone}</span>}
        {(value.contact_page || value.contact) && <span><strong>Web:</strong> <a href={value.contact_page || value.contact} target="_blank" rel="noreferrer">{value.contact_page || value.contact}</a></span>}
        {typeLabel && <span><strong>Tipo:</strong> {typeLabel}</span>}
      </div>
    );
  }

  // contact
  if (key === "contact" && typeof value === "object") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.email && <span><strong>Email:</strong> {value.email}</span>}
        {value.url && <span><strong>Web:</strong> <a href={value.url} target="_blank" rel="noreferrer">{value.url}</a></span>}
      </div>
    );
  }

  // health_category → etiqueta en español
  if (key === "health_category" && Array.isArray(value)) {
    return value.map(uri => {
      const code = uri.split("/").pop();
      return HEALTH_CATEGORY_LABELS[code] || code;
    }).join(", ");
  }

  // theme → etiqueta en español
  if (key === "theme" && Array.isArray(value)) {
    return value.map(uri => {
      const code = uri.split("/").pop();
      return THEME_LABELS[code] || code;
    }).join(", ");
  }

  // dcat_type → etiqueta en español
  if (key === "dcat_type" && typeof value === "string") {
    const code = value.split("/").pop();
    return DCAT_TYPE_LABELS[code] || code;
  }

  // applicable_legislation
  if (key === "applicable_legislation" && Array.isArray(value)) {
    return value.map((v, i) => (
      <span key={i}>{v.label || v.uri}</span>
    ));
  }

  // Arrays genéricos
  if (Array.isArray(value)) {
    return value.join(", ");
  }

  return String(value);
}

export default function MetadataPreview({ metadata }) {
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
        const info = FIELD_INFO[key] || { label: key, description: "" };
        const formatted = formatValue(key, value);
        if (!formatted) return null;

        return (
          <div key={key} className="field-row">
            <div className="field-key">{info.label}</div>
            <div className="field-val">{formatted}</div>
          </div>
        );
      })}
    </div>
  );
}
