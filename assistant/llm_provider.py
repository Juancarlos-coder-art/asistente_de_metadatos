import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

USE_OPENAI = os.getenv("USE_OPENAI", "false").lower() == "true"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None

if USE_OPENAI and OPENAI_API_KEY:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = None

if GROQ_API_KEY:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)

def groq_llm(prompt: str) -> dict:
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # modelo gratis
        messages=[
            {"role": "system", "content": "Devuelve SOLO JSON válido."},
            {"role": "user", "content": prompt}
        ]
    )
    raw = response.choices[0].message.content
    return extract_json_from_text(raw)


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
    Modo local sin OpenAI.
    Intenta rellenar los campos del contrato con reglas básicas.
    """
    result = {}

    for field_name in contract.keys():
        result[field_name] = parse_simple_field(field_name, user_input)

    return result


def openai_llm(prompt: str) -> dict:
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


def call_llm(prompt: str, contract: dict, user_input: str) -> dict:
    if USE_OPENAI and client is not None:
        return openai_llm(prompt)

    if groq_client is not None:
        return groq_llm(prompt)

    return mock_llm(prompt, contract, user_input)

def llm_available() -> bool:
    return groq_client is not None or (USE_OPENAI and client is not None)