import os
import json
import re

# =====================================================
# Helpers para configuración (runtime, no import-time!)
# =====================================================

def get_use_openai() -> bool:
    return os.getenv("USE_OPENAI", "false").lower() == "true"


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    from openai import OpenAI
    return OpenAI(api_key=api_key)


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    from groq import Groq
    return Groq(api_key=api_key)


# =====================================================
# LLM implementations
# =====================================================

def groq_llm(prompt: str) -> dict:
    client = get_groq_client()
    if not client:
        raise RuntimeError("GROQ_API_KEY no definida")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un experto en metadatos sanitarios HealthDCAT-AP-ES. "
                    "Extrae campos del texto del usuario y devuelve SOLO un objeto JSON válido, "
                    "sin explicaciones, sin markdown, sin texto adicional. "
                    "Si un campo no está en el texto, devuelve null para ese campo."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content
    return extract_json_from_text(raw)

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
