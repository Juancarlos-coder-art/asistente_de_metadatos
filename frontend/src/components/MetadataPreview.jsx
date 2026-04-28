// src/components/MetadataPreview.jsx

const FIELD_INFO = {
  title: { label: "Título", icon: "📋", description: "Nombre del dataset" },
  notes: { label: "Descripción", icon: "📝", description: "Descripción del contenido" },
  identifier: { label: "Identificador", icon: "🔗", description: "DOI o identificador único" },
  name: { label: "URL", icon: "🌐", description: "Dirección en el portal" },
  access_rights: { label: "Derechos de acceso", icon: "🔒", description: "Quién puede acceder" },
  hdab: { label: "Organismo de acceso (HDAB)", icon: "🏛️", description: "Entidad gestora del acceso" },
  applicable_legislation: { label: "Legislación aplicable", icon: "⚖️", description: "Marco legal" },
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
      <div style={styles.empty}>
        <span style={styles.emptyIcon}>📭</span>
        <p style={styles.emptyText}>Aún no hay datos. Completa el primer bloque.</p>
      </div>
    );
  }

  return (
    <div style={styles.grid}>
      {entries.map(([key, value]) => {
        const info = FIELD_INFO[key] || { label: key, icon: "📄", description: "" };
        const formatted = formatValue(key, value);
        if (!formatted) return null;

        return (
          <div key={key} style={styles.card}>
            <div style={styles.cardHeader}>
              <span style={styles.cardIcon}>{info.icon}</span>
              <span style={styles.cardLabel}>{info.label}</span>
            </div>
            <div style={styles.cardValue}>{formatted}</div>
          </div>
        );
      })}
    </div>
  );
}

const styles = {
  grid: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "8px",
  },
  card: {
    background: "white",
    border: "1px solid var(--color-border)",
    borderLeft: "3px solid var(--color-interactive)",
    padding: "12px 14px",
  },
  cardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginBottom: "6px",
  },
  cardIcon: {
    fontSize: "0.9rem",
  },
  cardLabel: {
    fontFamily: "var(--font-mono)",
    fontSize: "0.7rem",
    color: "var(--color-text-secondary)",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
    fontWeight: 600,
  },
  cardValue: {
    fontSize: "0.9rem",
    color: "var(--color-text-primary)",
    lineHeight: 1.5,
    wordBreak: "break-word",
  },
  empty: {
    textAlign: "center",
    padding: "32px 16px",
    border: "1px dashed var(--color-border)",
    background: "white",
  },
  emptyIcon: {
    fontSize: "2rem",
    display: "block",
    marginBottom: "8px",
  },
  emptyText: {
    fontSize: "0.875rem",
    color: "var(--color-text-secondary)",
  },
};
