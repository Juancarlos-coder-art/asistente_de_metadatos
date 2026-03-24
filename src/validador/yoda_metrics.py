metrics = [

# ------------------------------------------------------------
# 1. IDENTIFICACIÓN BÁSICA (DCAT + HealthDCAT)
# ------------------------------------------------------------

{
 "dimension": "Findability",
 "indicator": "Dataset has a title",
 "metric": "dct:title",
 "weight": 20
},
{
 "dimension": "Findability",
 "indicator": "Dataset has a description",
 "metric": "dct:description",
 "weight": 20
},
{
 "dimension": "Findability",
 "indicator": "Identifier present",
 "metric": "dct:identifier",
 "weight": 15
},
{
 "dimension": "Findability",
 "indicator": "Landing page available",
 "metric": "dcat:landingPage",
 "weight": 10
},

# ------------------------------------------------------------
# 2. PALABRAS CLAVE, TEMAS Y SEMÁNTICA
# ------------------------------------------------------------

{
 "dimension": "Findability",
 "indicator": "Keywords present",
 "metric": "dcat:keyword",
 "weight": 30
},
{
 "dimension": "Findability",
 "indicator": "Theme present",
 "metric": "dcat:theme",
 "weight": 20
},
{
 "dimension": "Interoperability",
 "indicator": "Use of standardized health categories (EHDS Art. 33)",
 "metric": "hcat:healthCategory",
 "weight": 40
},
{
 "dimension": "Interoperability",
 "indicator": "Use of standardized health themes",
 "metric": "hcat:healthTheme",
 "weight": 30
},

# ------------------------------------------------------------
# 3. CODIFICACIÓN (CLINICAL VOCABULARIES / ICD / SNOMED / ETC)
# ------------------------------------------------------------

{
 "dimension": "Interoperability",
 "indicator": "Clinical code values provided",
 "metric": "hcat:codeValue",
 "weight": 40
},
{
 "dimension": "Interoperability",
 "indicator": "Clinical coding system present",
 "metric": "hcat:codingSystem",
 "weight": 35
},
{
 "dimension": "Interoperability",
 "indicator": "Use of controlled vocabularies (format or mediaType)",
 "metric": ["dct:format", "dcat:mediaType"],
 "weight": 20
},

# ------------------------------------------------------------
# 4. ORGANIZACIONES, CONTACTO Y RESPONSABILIDAD
# ------------------------------------------------------------

{
 "dimension": "Reusability",
 "indicator": "Publisher exists",
 "metric": "dct:publisher",
 "weight": 20
},
{
 "dimension": "Reusability",
 "indicator": "Creator exists",
 "metric": "dct:creator",
 "weight": 10
},
{
 "dimension": "Reusability",
 "indicator": "Contact point present",
 "metric": "dcat:contactPoint",
 "weight": 20
},
{
 "dimension": "Governance",
 "indicator": "Trusted Data Holder indicated",
 "metric": "ehds:trustedDataHolder",
 "weight": 25
},
{
 "dimension": "Governance",
 "indicator": "Health Data Access Body (HDAB) present",
 "metric": "ehds:healthDataAccessBody",
 "weight": 30
},

# ------------------------------------------------------------
# 5. FECHAS Y CICLO DE VIDA
# ------------------------------------------------------------

{
 "dimension": "Contextuality",
 "indicator": "Issued date present",
 "metric": "dct:issued",
 "weight": 15
},
{
 "dimension": "Contextuality",
 "indicator": "Modified date present",
 "metric": "dct:modified",
 "weight": 15
},
{
 "dimension": "Contextuality",
 "indicator": "Frequency updated",
 "metric": "dct:accrualPeriodicity",
 "weight": 10
},
{
 "dimension": "Contextuality",
 "indicator": "Provenance declared",
 "metric": "dct:provenance",
 "weight": 20
},

# ------------------------------------------------------------
# 6. COBERTURA TEMPORAL Y ESPACIAL
# ------------------------------------------------------------

{
 "dimension": "Contextuality",
 "indicator": "Temporal coverage",
 "metric": "dct:temporal",
 "weight": 20
},
{
 "dimension": "Contextuality",
 "indicator": "Spatial coverage",
 "metric": "dct:spatial",
 "weight": 20
},

# ------------------------------------------------------------
# 7. DATOS PERSONALES (GDPR / EHDS)
# ------------------------------------------------------------

{
 "dimension": "Privacy",
 "indicator": "Personal data declared",
 "metric": "hcat:personalData",
 "weight": 20
},
{
 "dimension": "Privacy",
 "indicator": "Population coverage declared",
 "metric": "hcat:populationCoverage",
 "weight": 30
},
{
 "dimension": "Privacy",
 "indicator": "Purpose for processing personal data declared",
 "metric": "hcat:purpose",
 "weight": 30
},
{
 "dimension": "Privacy",
 "indicator": "Legal basis declared",
 "metric": "dct:legalBasis",
 "weight": 20
},

# ------------------------------------------------------------
# 8. LEGISLACIÓN, DERECHO Y ACCESO
# ------------------------------------------------------------

{
 "dimension": "Reusability",
 "indicator": "Access rights present",
 "metric": "dct:accessRights",
 "weight": 20
},
{
 "dimension": "Reusability",
 "indicator": "Rights statement present",
 "metric": "dct:rights",
 "weight": 10
},
{
 "dimension": "Reusability",
 "indicator": "Applicable legislation declared",
 "metric": "dct:applicableLegislation",
 "weight": 20
},

# ------------------------------------------------------------
# 9. DISTRIBUCIONES (ACCESS / DOWNLOAD / FORMAT / SIZE / HASH)
# ------------------------------------------------------------

{
 "dimension": "Accessibility",
 "indicator": "Access URL",
 "metric": "dcat:accessURL",
 "weight": 40
},
{
 "dimension": "Accessibility",
 "indicator": "Download URL",
 "metric": "dcat:downloadURL",
 "weight": 40
},
{
 "dimension": "Interoperability",
 "indicator": "Media type present",
 "metric": "dcat:mediaType",
 "weight": 20
},
{
 "dimension": "Interoperability",
 "indicator": "Format declared",
 "metric": "dct:format",
 "weight": 20
},
{
 "dimension": "Contextuality",
 "indicator": "File size declared",
 "metric": "dcat:byteSize",
 "weight": 10
},
{
 "dimension": "Security",
 "indicator": "Hash present",
 "metric": "spdx:checksum",
 "weight": 20
},

# ------------------------------------------------------------
# 10. PROVENENCIA (PROV-O & HEALTHDCAT PROFILES)
# ------------------------------------------------------------

{
 "dimension": "Provenance",
 "indicator": "Qualified attributions",
 "metric": "prov:qualifiedAttribution",
 "weight": 25
},
{
 "dimension": "Provenance",
 "indicator": "Qualified relations",
 "metric": "dcat:qualifiedRelation",
 "weight": 20
},
{
 "dimension": "Provenance",
 "indicator": "Provenance activity declared",
 "metric": "prov:Activity",
 "weight": 30
},

# ------------------------------------------------------------
# 11. ACCESO A SERVICIOS (DataService)
# ------------------------------------------------------------

{
 "dimension": "Accessibility",
 "indicator": "Access services present",
 "metric": "dcat:accessService",
 "weight": 20
},
{
 "dimension": "Governance",
 "indicator": "Access service endpoint",
 "metric": "dcat:endpointURL",
 "weight": 20
},

# ------------------------------------------------------------
# 12. CALIDAD (DQV)
# ------------------------------------------------------------

{
 "dimension": "Quality",
 "indicator": "Quality annotations present",
 "metric": "dqv:QualityAnnotation",
 "weight": 30
},

# ------------------------------------------------------------
# 13. DCAT COMPLIANCE (SHACL)
# ------------------------------------------------------------

{
 "dimension": "Interoperability",
 "indicator": "DCAT/HealthDCAT SHACL compliance",
 "metric": "SHACL",
 "weight": 40
}

]