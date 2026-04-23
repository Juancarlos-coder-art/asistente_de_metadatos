import os
import json
import re

# =====================================================
# Helpers para configuración (runtime, no import-time!)
# =====================================================


def get_use_openai() -> bool:
    """
    Indica si debe usarse OpenAI según la variable de entorno USE_OPENAI.

    Se considera True solo si USE_OPENAI es exactamente "true"
    (ignorando mayúsculas/minúsculas).
    """

    use_openai_env = os.getenv("USE_OPENAI", "false")
    use_openai_env = use_openai_env.lower()

    return use_openai_env == "true"



def get_openai_client():
    """
    Devuelve un cliente de OpenAI si existe la variable de entorno
    OPENAI_API_KEY. Si no existe, devuelve None.
    """

    # Leer la API key desde las variables de entorno
    api_key = os.getenv("OPENAI_API_KEY")

    # Si no hay API key, no se puede crear el cliente
    if api_key is None or api_key == "":
        return None

    # Importamos aquí para evitar dependencias si no se usa OpenAI
    from openai import OpenAI

    # Creamos y devolvemos el cliente
    return OpenAI(api_key=api_key)


def get_groq_client():
    """
    Devuelve un cliente de Groq si existe la variable de entorno
    GROQ_API_KEY. Si no existe, devuelve None.
    """

    # Leer la API key desde las variables de entorno
    api_key = os.getenv("GROQ_API_KEY")

    # Si no hay API key, no se puede crear el cliente
    if api_key is None or api_key == "":
        return None

    # Importamos aquí para evitar dependencias si no se usa Groq
    from groq import Groq

    # Creamos y devolvemos el cliente
    return Groq(api_key=api_key)


# =====================================================
# LLM implementations
# =====================================================


def groq_llm(
    prompt: str,
    temperature: float = 0.0,
    top_p: float = 1.0,
    top_k: int | None = None,
    max_tokens: int = 2000
) -> dict:
    """
    Envía un prompt a Groq y devuelve la respuesta en formato JSON.

    Lanza un error si no existe la variable de entorno GROQ_API_KEY.
    """

    # 1. Obtener el cliente de Groq de la función anterior.
    client = get_groq_client()

    # 2. Si no hay cliente, no podemos continuar
    if client is None:
        raise RuntimeError("GROQ_API_KEY no definida")

    # 3. Enviar el prompt al modelo
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Devuelve SOLO JSON válido."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # 4. Extraer el texto devuelto por el modelo
    raw_text = response.choices[0].message.content

    # 5. Convertir el texto a JSON y devolverlo
    return extract_json_from_text(raw_text)


def openai_llm(prompt: str) -> dict:
    client = get_openai_client()
    if not client:
        raise RuntimeError("OPENAI_API_KEY no definida")

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente experto en HealthDCAT-AP. Devuelve siempre JSON válido."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content
    return extract_json_from_text(raw)


# =====================================================
# Utils
# =====================================================

def extract_json_from_text(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"{.*}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}
    return {}


def parse_simple_field(field_name: str, user_input: str):
    user_input = user_input.strip()

    if not user_input:
        return None

    if field_name in ["tag_string", "applicable_legislation", "language"]:
        return [v.strip() for v in user_input.split(",") if v.strip()]

    if field_name == "contact":
        contactos = []
        bloques = [b.strip() for b in user_input.split(",") if b.strip()]
        for b in bloques:
            partes = [p.strip() for p in b.split("|")]
            contacto = {}
            if len(partes) > 0:
                contacto["name"] = partes[0]
            if len(partes) > 1:
                contacto["email"] = partes[1]
            if len(partes) > 2:
                contacto["role"] = partes[2]
            contactos.append(contacto)
        return contactos if contactos else None

    return user_input


def mock_llm(prompt: str, contract: dict, user_input: str) -> dict:
    """
    Modo fallback sin LLM real.
    """
    result = {}

    for field_name in contract.keys():
        result[field_name] = parse_simple_field(field_name, user_input)

    return result


# =====================================================
# Public API usada por Streamlit
# =====================================================

def call_llm(prompt: str, contract: dict, user_input: str) -> dict:
    if get_use_openai():
        client = get_openai_client()
        if client:
            return openai_llm(prompt)

    client = get_groq_client()
    if client:
        return groq_llm(prompt)

    # Fallback seguro
    return mock_llm(prompt, contract, user_input)


def llm_available() -> bool:
    return bool(
        get_groq_client() or
        (get_use_openai() and get_openai_client())
    )
