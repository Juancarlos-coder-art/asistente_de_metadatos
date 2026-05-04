# Asistente de Metadatos HealthDCAT-AP-ES

> Asistente conversacional para la generación de metadatos sanitarios conforme al estándar europeo **HealthDCAT-AP-ES**, desarrollado en el marco de la **Estrategia Nacional de Datos de Salud (ENDS)**.

---

## Índice

- [¿Qué hace este proyecto?](#-qué-hace-este-proyecto)
- [Arquitectura](#-arquitectura)
- [Requisitos previos](#-requisitos-previos)
- [Instalación paso a paso](#-instalación-paso-a-paso)
- [Configuración de la API de Groq](#-configuración-de-la-api-de-groq)
- [Estructura del proyecto](#-estructura-del-proyecto)
- [Cómo ejecutarlo](#-cómo-ejecutarlo)
- [Resultado generado](#-resultado-generado)
- [Integración con CKAN](#-integración-con-ckan)
- [Ramas del repositorio](#-ramas-del-repositorio)

---

## ¿Qué hace este proyecto?

Este asistente guía al usuario a través de una serie de preguntas por bloques para recopilar la información necesaria y generar automáticamente un archivo **`metadata_output.json`** conforme al esquema HealthDCAT-AP-ES.

El usuario responde en lenguaje natural y la IA interpreta, estructura y valida los datos según el esquema oficial.

```
Usuario responde en texto libre
        ↓
LLM (Groq) interpreta y extrae campos
        ↓
Validación automática contra el esquema YAML
        ↓
metadata_output.json ← listo para publicar en CKAN
```

---

## 🏗 Arquitectura

```
asistente-metadato/
├── app.py                  # Interfaz web (Streamlit)
├── cli.py                  # Interfaz de línea de comandos
├── schema_loader.py        # Carga y gestiona el esquema YAML
├── health_dcat_ap.yaml     # Esquema HealthDCAT-AP-ES
├── assistant/
│   ├── llm_provider.py     # Conexión con la API de Groq
│   ├── metadata_state.py   # Estado y validación de metadatos
│   └── rag_helper.py       # Sistema de ayuda contextual por campo
└── requirements.txt        # Dependencias Python
```

---

## ✅ Requisitos previos

Antes de instalar, asegúrate de tener:

| Requisito | Versión mínima | Cómo verificar |
|-----------|---------------|----------------|
| Python | 3.10 o superior | `python --version` |
| pip | 23 o superior | `pip --version` |
| Git | cualquier versión | `git --version` |
| Cuenta en Groq | gratuita | [console.groq.com](https://console.groq.com) |

---

## 🚀 Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone https://github.com/Juancarlos-coder-art/asistente_de_metadatos.git
cd asistente_de_metadatos
```

### 2. Crear un entorno virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Si no existe `requirements.txt`, instala manualmente:

```bash
pip install streamlit
pip install pyyaml
pip install groq
pip install python-dotenv
```

---

## 🔑 Configuración de la API de Groq

Este proyecto utiliza **Groq** como proveedor de LLM. Es **gratuito** para desarrollo.

### Paso 1 — Crear una cuenta

Ve a [console.groq.com](https://console.groq.com) y regístrate (no requiere tarjeta de crédito).

### Paso 2 — Obtener tu API Key

1. Dentro de la consola, ve a **API Keys** en el menú lateral
2. Haz clic en **Create API Key**
3. Dale un nombre (por ejemplo: `asistente-metadatos`)
4. **Copia la key** — solo se muestra una vez

### Paso 3 — Crear el archivo `.env`

En la raíz del proyecto, crea un archivo llamado `.env`:

```bash
# .env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **Importante:** El archivo `.env` ya está en el `.gitignore`. Nunca lo subas a GitHub.

### Modelos disponibles (gratuitos)

| Modelo | Uso recomendado |
|--------|----------------|
| `llama-3.3-70b-versatile` | **Recomendado** — mejor calidad |
| `llama-3.1-8b-instant` | Más rápido, respuestas más simples |

El modelo se configura en `assistant/llm_provider.py`.

---

## 📁 Estructura del proyecto

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Interfaz web con Streamlit. Incluye pantalla de bienvenida, navegación por bloques, modo IA y modo manual |
| `cli.py` | Versión de terminal. El usuario responde preguntas una a una |
| `schema_loader.py` | Lee el `health_dcat_ap.yaml` y expone los campos, restricciones y vocabularios controlados |
| `health_dcat_ap.yaml` | Esquema completo HealthDCAT-AP-ES con todos los campos, etiquetas, validaciones y vocabularios |
| `assistant/llm_provider.py` | Llama a la API de Groq y parsea la respuesta JSON |
| `assistant/metadata_state.py` | Mantiene el estado acumulado de los metadatos y valida tipos y campos obligatorios |
| `assistant/rag_helper.py` | Índice en memoria de los campos del esquema. Genera descripciones de ayuda cuando un campo queda vacío |
| `guia_campos_ends.docx` | Guía descargable con la descripción de todos los campos activos |

---

## ▶️ Cómo ejecutarlo

### Opción A — Interfaz web (recomendada)

```bash
streamlit run app.py
```

Se abrirá automáticamente en el navegador en `http://localhost:8501`.

**Flujo de uso:**
1. Pantalla de bienvenida → descargar guía de campos (opcional)
2. Hacer clic en **Comenzar a metadatar**
3. Para cada bloque: describir el dataset en lenguaje natural y pulsar **Autocompletar con IA**
4. Al terminar todos los bloques: **Finalizar y guardar**
5. Se genera `metadata_output.json` en la raíz del proyecto

### Opción B — Terminal (CLI)

```bash
python cli.py
```

El asistente irá preguntando bloque a bloque. Pulsa **Enter dos veces** para confirmar cada respuesta.

---

## 📄 Resultado generado

Al finalizar se crea `metadata_output.json` con esta estructura:

```json
{
  "title": "Casos de viruela del mono en España 2023",
  "name": "casos-viruela-mono-espana-2023",
  "notes": "Dataset con registros de casos confirmados...",
  "identifier": "https://doi.org/10.5281/zenodo.123456",
  "access_rights": "http://publications.europa.eu/resource/authority/access-right/RESTRICTED",
  "hdab": {
    "name": "CSIC",
    "type": "http://13.81.34.152:1101/resource/authority/publisher-type/research-institute-org",
    "email": null,
    "telephone": "639 99 15 67",
    "contact_page": null
  },
  "applicable_legislation": [
    {
      "uri": "http://data.europa.eu/eli/reg/2016/679/oj",
      "label": "GDPR"
    }
  ]
}
```

---

## 🔗 Integración con CKAN

Este proyecto genera el JSON de metadatos. La integración con un portal CKAN es responsabilidad del equipo técnico del portal receptor.

El JSON generado es compatible con el perfil `EuropeanHealthDCATAPProfile` de la extensión `ckanext-dcat`.

**Lo que hace este asistente:** genera `metadata_output.json`

**Lo que hace el equipo CKAN:** importa ese JSON usando el perfil RDF correspondiente

---

## 🌿 Ramas del repositorio

| Rama | Descripción |
|------|-------------|
| `master` | Versión estable con LLM (Groq). Lista para uso en desarrollo |
| `qa_nlp` | Versión en desarrollo sin IA generativa, usando Google Cloud Natural Language API + spaCy para entornos de producción institucional |

---

## 📦 Dependencias principales

```
streamlit          # Interfaz web
pyyaml             # Lectura del esquema YAML
groq               # Cliente oficial de la API de Groq
python-dotenv      # Carga de variables de entorno desde .env
```

---

## ⚠️ Notas importantes

- El campo `applicable_legislation` (GDPR) se inserta **automáticamente** al finalizar. No es necesario introducirlo.
- El campo `name` (URL del dataset en CKAN) se genera automáticamente a partir del título.
- Los campos marcados con 🔴 en la interfaz son **obligatorios** según el esquema HealthDCAT-AP-ES.
- Para uso en **producción institucional**, consultar la rama `qa_nlp` que no depende de IA generativa.

---

## 📬 Contacto

Proyecto desarrollado para la **Estrategia Nacional de Datos de Salud (ENDS)**.
Repositorio: [github.com/Juancarlos-coder-art/asistente_de_metadatos](https://github.com/Juancarlos-coder-art/asistente_de_metadatos)
