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
  "HRAD": "Datos administrativos sanitarios",
  "MRMR": "Datos de registros médicos y mortalidad",
  "RPDG": "Datos de patógenos",
  "RQSH": "Datos de cohortes e investigación",
  "PHDR": "Registros de salud pública",
  "EHCT": "Datos de ensayos clínicos",
  "HGPD": "Datos genéticos y genómicos",
  "EINS": "Datos de biobancos",
  "EMRD": "Datos de dispositivos médicos",
  "HPML": "Datos moleculares",
  "WELA": "Datos de aplicaciones de bienestar",
  "RMMD": "Datos de medicamentos",
  "NRPE": "Datos agregados sanitarios",
  "PGEH": "Datos electrónicos personales",
  "IDHP": "Datos de profesionales de la salud",
  "DIOH": "Datos sobre factores de salud",
};

const THEME_LABELS = {
  "HEAL": "Salud",
  "TECH": "Ciencia y tecnología",
  "SOCI": "Población y sociedad",
  "GOVE": "Gobierno y sector público",
  "EDUC": "Educación, cultura y deportes",
  "ECON": "Economía y finanzas",
  "ENVI": "Medio ambiente",
  "AGRI": "Agricultura, pesca y alimentación",
  "TRAN": "Transporte",
  "JUST": "Justicia y seguridad pública",
  "REGI": "Regiones y ciudades",
  "INTR": "Asuntos internacionales",
};

const DCAT_TYPE_LABELS = {
  "STATISTICAL": "Datos estadísticos",
  "GEOSPATIAL": "Datos geoespaciales",
  "HVD": "Conjunto de datos de alto valor",
  "SYNTHETIC_DATA": "Datos sintéticos",
  "ONTOLOGY": "Ontología",
  "SCHEMA": "Esquema",
  "CODE_LIST": "Lista de códigos",
  "APROF": "Perfil de aplicación",
  "TEST_DATA": "Datos de prueba",
  "CORE_COMP": "Componente básico",
  "MAPPING": "Correspondencia",
  "DIRECTORY": "Directorio",
  "GLOSSARY": "Glosario",
  "THESAURUS": "Tesauro",
  "TAXONOMY": "Taxonomía",
  "DOMAIN_MODEL": "Modelo de dominio",
  "RELEASE": "Publicación",
};

const PUBLISHER_TYPE_LABELS = {
  "public-health-institute": "Instituto de salud pública",
  "research-institute-org": "Instituto/organización de investigación",
  "national-authority": "Autoridad nacional",
  "regional-authority": "Autoridad regional",
  "university": "Universidad",
  "public-health-registry": "Registro de salud pública",
  "public-health-org": "Organización de salud pública",
  "stat-agency": "Agencia de estadísticas",
  "biobank": "Biobanco",
  "inpatient-institute": "Hospital",
  "laboratory": "Laboratorio",
  "private-company": "Empresa privada",
  "gov-public-sector-org": "Organización gubernamental",
  "healthcare-providers": "Proveedores de atención médica",
  "research-infra": "Infraestructura de investigación",
  "non-gov-org": "Organización no gubernamental",
  "mental-health-org": "Organización de salud mental",
  "primary-care-org": "Organización de atención primaria",
  "quality-registry": "Registro de calidad",
  "pathology-registry": "Registro de patología",
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
        {value.contact_page && <span><strong>Web:</strong> <a href={value.contact_page} target="_blank" rel="noreferrer">{value.contact_page}</a></span>}
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
