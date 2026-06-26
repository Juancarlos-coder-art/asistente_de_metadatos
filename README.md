# 🏥 Asistente de Metadatos HealthDCAT-AP

> Asistente conversacional para la generación de metadatos sanitarios conforme al estándar europeo **HealthDCAT-AP**, desarrollado en el marco de la **Estrategia Nacional de Datos de Salud (ENDS)**.

---

## 📋 Índice

- [¿Qué hace este proyecto?](#-qué-hace-este-proyecto)
- [Arquitectura](#-arquitectura)
- [Requisitos previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Variables de entorno](#-variables-de-entorno)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Cómo ejecutarlo](#-cómo-ejecutarlo)
- [Despliegue en Google Cloud Run](#-despliegue-en-google-cloud-run)
- [Resultado generado](#-resultado-generado)
- [Integración con CKAN](#-integración-con-ckan)

---

## ¿Qué hace este proyecto?

El asistente guía al usuario a través de bloques temáticos para recopilar la información necesaria y generar metadatos conformes al esquema HealthDCAT-AP. Admite dos modos de entrada por bloque:

- **Modo IA:** el usuario describe el dataset en lenguaje natural y el LLM extrae y estructura los campos automáticamente.
- **Modo manual:** el usuario rellena los campos directamente en el formulario.

También permite subir un documento PDF o un fichero de datos estructurado (CSV, Excel, JSON, Parquet, XML) para pre-rellenar los metadatos automáticamente mediante el módulo `yoda_extractor`.

```
Usuario describe el dataset (texto libre) o sube un fichero
        ↓
LLM (Groq / OpenAI) interpreta y extrae campos
        ↓
Validación automática contra el esquema YAML (HealthDCAT-AP)
        ↓
Previsualización editable → exportación RDF/JSON
```

---

## 🏗 Arquitectura

```
asistente_de_metadatos/
├── api.py                        # Backend FastAPI — endpoints REST + lógica principal
├── cli.py                        # Interfaz de línea de comandos (desarrollo/debug)
├── schema_loader.py              # Carga el YAML y expone restricciones y vocabularios
├── health_dcat_ap.yaml           # Esquema HealthDCAT-AP completo
├── dockerfile                    # Imagen multi-stage (Node → Python)
├── cloudbuild.yaml               # Pipeline CI/CD → Google Cloud Run (europe-west1)
│
├── assistant/
│   ├── llm_provider.py           # Cliente Groq/OpenAI + logging a BigQuery
│   ├── metadata_state.py         # Estado acumulado de metadatos y validación
│   └── rag_helper.py             # Índice de campos con descripciones de ayuda
│
├── frontend/                     # React + Vite
│   └── src/
│       ├── App.jsx               # Enrutamiento y estado global
│       ├── api/client.js         # Llamadas al backend
│       ├── components/
│       │   ├── Sidebar.jsx           # Navegación por bloques y progreso
│       │   ├── MetadataPreview.jsx   # Previsualización editable con tooltips
│       │   ├── DocumentUploadModal.jsx
│       │   └── LegislationSelector.jsx
│       ├── pages/
│       │   ├── Welcome.jsx
│       │   └── BlockForm.jsx     # Formulario por bloque (modo IA + modo manual)
│       └── constants/fieldInfo.js  # Etiquetas, tooltips y ejemplos por campo
│
├── yoda_extractor/               # Extractor automático de metadatos desde ficheros de datos
│   ├── main.py
│   ├── extractors/               # Módulos: estructura, temporal, geoespacial, LLM, vocabulario…
│   ├── readers/                  # CSV, Excel, JSON, Parquet, XML
│   └── utils/
│
└── requirements.txt
```

---

## ✅ Requisitos previos

| Requisito | Versión mínima | Verificar |
|-----------|---------------|-----------|
| Python | 3.11 | `python --version` |
| Node.js | 20 | `node --version` |
| pip | 23 | `pip --version` |
| Cuenta Groq | gratuita | [console.groq.com](https://console.groq.com) |

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/Juancarlos-coder-art/asistente_de_metadatos.git
cd asistente_de_metadatos
```

### 2. Backend — entorno virtual Python

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Frontend — dependencias Node

```bash
cd frontend
npm install
npm run build   # genera frontend/dist/ que sirve FastAPI
cd ..
```

---

## 🔑 Variables de entorno

Crea un archivo `.env` en la raíz del proyecto (ya está en `.gitignore`):

```bash
# LLM — al menos una de las dos
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx   # opcional

# BigQuery — opcional, solo para analytics de uso
BQ_USAGE_TABLE=proyecto.dataset.tabla
GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/credenciales.json
```

El modelo activo se configura en `assistant/llm_provider.py`. Por defecto usa `llama-3.3-70b-versatile` (Groq).

---

## 📁 Estructura del proyecto

| Fichero / carpeta | Descripción |
|---|---|
| `api.py` | Backend FastAPI. Expone los endpoints `/chat`, `/upload-document`, `/export-rdf`, `/session/*`, y sirve el frontend React desde `/` |
| `cli.py` | Versión terminal del asistente. Útil para pruebas y desarrollo sin frontend |
| `schema_loader.py` | Parsea `health_dcat_ap.yaml` y extrae restricciones, vocabularios controlados y reglas de validación |
| `health_dcat_ap.yaml` | Esquema HealthDCAT-AP con todos los campos, etiquetas, validaciones y vocabularios |
| `assistant/llm_provider.py` | Llama a Groq u OpenAI, gestiona límites de tokens por sesión y registra uso en BigQuery |
| `assistant/metadata_state.py` | Mantiene el estado acumulado de metadatos y valida tipos, formatos y campos obligatorios |
| `assistant/rag_helper.py` | Índice estático de campos con descripciones y ejemplos. Genera ayuda contextual cuando un campo queda vacío |
| `yoda_extractor/` | Extrae metadatos automáticamente desde ficheros de datos (CSV, Excel, JSON, Parquet, XML): estructura, temporalidad, cobertura geoespacial, vocabularios controlados |
| `frontend/` | Interfaz React/Vite. Se compila a `frontend/dist/` y es servida estáticamente por FastAPI |
| `dockerfile` | Build multi-stage: compila el frontend con Node 20 y luego monta el backend con Python 3.11 |
| `cloudbuild.yaml` | Pipeline CI/CD para Google Cloud Run en `europe-west1` |

---

## ▶️ Cómo ejecutarlo

### Desarrollo local (recomendado)

En una terminal, arranca el backend:

```bash
uvicorn api:app --reload --port 8080
```

En otra terminal, arranca el frontend en modo dev (con hot reload):

```bash
cd frontend
npm run dev
```

La app estará en `http://localhost:5173` (Vite) con proxy al backend en `:8080`.

### Producción local (frontend compilado)

```bash
cd frontend && npm run build && cd ..
uvicorn api:app --host 0.0.0.0 --port 8080
```

Accede en `http://localhost:8080`.

### CLI (sin frontend)

```bash
python cli.py
```

---

## ☁️ Despliegue en Google Cloud Run

El proyecto incluye un pipeline completo con `cloudbuild.yaml`:

```bash
gcloud builds submit --config cloudbuild.yaml
```

Esto construye la imagen Docker multi-stage, la sube a Artifact Registry y despliega en Cloud Run (`europe-west1`) con:
- Memoria: 1 GiB
- CPU: 1
- Timeout: 300 s
- `GROQ_API_KEY` inyectada desde Secret Manager

---

## 📄 Resultado generado

Al completar todos los bloques se puede exportar el metadata en dos formatos:

**JSON** — compatible con la API de CKAN:

```json
{
  "title": "Casos de viruela del mono en España 2023",
  "name": "casos-viruela-mono-espana-2023",
  "notes": "Dataset con registros de casos confirmados...",
  "identifier": "https://doi.org/10.5281/zenodo.123456",
  "access_rights": "http://publications.europa.eu/resource/authority/access-right/RESTRICTED",
  "hdab": {
    "name": "ISCIII",
    "email": "datos.salud@isciii.es",
    "contact_page": "https://www.isciii.es/contacto"
  },
  "applicable_legislation": [
    { "uri": "http://data.europa.eu/eli/reg/2016/679/oj", "label": "GDPR" }
  ]
}
```

**RDF/Turtle** — exportable desde el endpoint `/export-rdf`, conforme al perfil HealthDCAT-AP.

---

## 🔗 Integración con CKAN

El JSON generado es compatible con el perfil `EuropeanHealthDCATAPProfile` de la extensión `ckanext-dcat`.

**Este asistente:** genera el JSON / RDF de metadatos.

**El equipo CKAN:** importa ese JSON usando la API o el perfil RDF correspondiente.

---

## ⚠️ Notas

- El campo `applicable_legislation` (GDPR) se inserta automáticamente. No hace falta introducirlo manualmente.
- El campo `name` (slug del dataset en CKAN) se genera automáticamente desde el título.
- Los campos marcados con 🔴 en la interfaz son obligatorios según el esquema HealthDCAT-AP.
- Los datasets marcados como `NON_PUBLIC` reciben un identificador predeterminado automáticamente.

---

## 📬 Contacto

Proyecto desarrollado para la **Estrategia Nacional de Datos de Salud (ENDS)**.  
Repositorio: [github.com/Juancarlos-coder-art/asistente_de_metadatos](https://github.com/Juancarlos-coder-art/asistente_de_metadatos)
