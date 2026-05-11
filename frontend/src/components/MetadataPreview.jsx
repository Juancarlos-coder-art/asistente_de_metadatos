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

function formatValue(key, value) {
  if (value === null || value === undefined || value === "") return null;

  // access_rights — extraer la parte final de la URI
  if (key === "access_rights" && typeof value === "string") {
    const parts = value.split("/");
    const code = parts[parts.length - 1];
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
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.name && <span><strong>Nombre:</strong> {value.name}</span>}
        {value.email && <span><strong>Email:</strong> {value.email}</span>}
        {value.telephone && <span><strong>Teléfono:</strong> {value.telephone}</span>}
        {value.contact_page && <span><strong>Web:</strong> <a href={value.contact_page} target="_blank" rel="noreferrer">{value.contact_page}</a></span>}
        {value.type && <span><strong>Tipo:</strong> {value.type.split("/").pop()}</span>}
      </div>
    );
  }
  // contact — objeto con email y url
  if (key === "contact" && typeof value === "object") {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
        {value.email && <span><strong>Email:</strong> {value.email}</span>}
        {value.url && <span><strong>Web:</strong> <a href={value.url} target="_blank" rel="noreferrer">{value.url}</a></span>}
      </div>
    );
  }

  // health_category y theme — array de URIs, mostrar solo el código final
  if ((key === "health_category" || key === "theme") && Array.isArray(value)) {
    return value.map(uri => uri.split("/").pop()).join(", ");
  }

  // dcat_type — URI, mostrar solo el código final
  if (key === "dcat_type" && typeof value === "string") {
    return value.split("/").pop();
  }
  // applicable_legislation — array
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
  const entries = Object.entries(metadata).filter(([, v]) => v !== null && v !== "" && !(Array.isArray(v) && v.length === 0));

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
