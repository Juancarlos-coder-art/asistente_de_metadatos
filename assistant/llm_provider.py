import os
import json
import re
from datetime import datetime
from google.cloud import bigquery



# =====================================================
# Logging usage en BigQuery
# =====================================================

def log_usage(provider, model, usage, endpoint=None, session_id=None, extra_json=None):
    table = os.getenv("BQ_USAGE_TABLE")

    if not table:
        print("❌ BQ_USAGE_TABLE vacía")
        return

    try:
        client = bigquery.Client()

        prompt_tokens = getattr(usage, "prompt_tokens", 0)
        completion_tokens = getattr(usage, "completion_tokens", 0)
        total_tokens = getattr(usage, "total_tokens", 0)

        PRICE_INPUT = float(os.getenv("GROQ_INPUT_PRICE_PER_M", "0.35"))
        PRICE_OUTPUT = float(os.getenv("GROQ_OUTPUT_PRICE_PER_M", "0.62"))

        cost = (
            (prompt_tokens / 1_000_000) * PRICE_INPUT +
            (completion_tokens / 1_000_000) * PRICE_OUTPUT
        )


        row = {
            "ts": datetime.utcnow().isoformat(),
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost,
            "endpoint": endpoint,
            "session_id": session_id,
            "extra_json": json.dumps(extra_json, ensure_ascii=False) if extra_json is not None else None
        }

        print("✅ insertando en:", table)
        errors = client.insert_rows_json(table, [row])

        if errors:
            print("❌ errores BigQuery:", errors)
        else:
            print("✅ fila insertada")

    except Exception as e:
        print("❌ Error logging usage:", e)


# =====================================================
# Helpers para configuración
# =====================================================

def get_use_openai() -> bool:
    return os.getenv("USE_OPENAI", "false").lower() == "true"


def get_use_gemini() -> bool:
    return os.getenv("USE_GEMINI", "false").lower() == "true"


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


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    from google import genai
    return genai.Client(api_key=api_key)


# LLM implementations

def groq_llm(prompt: str, endpoint=None, session_id=None, extra_json=None) -> dict:
    client = get_groq_client()
    if not client:
        raise RuntimeError("GROQ_API_KEY no definida")

    model = "llama-3.3-70b-versatile"

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un experto en metadatos sanitarios HealthDCAT-AP. "
                    "Extrae campos del texto del usuario y devuelve SOLO un objeto JSON válido, "
                    "sin explicaciones, sin markdown, sin texto adicional. "
                    "Si un campo no está en el texto, devuelve null para ese campo."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=4096,
    )

    usage = getattr(response, "usage", None)
    print("🔥 USAGE RAW:", usage)

    if usage is None:
        print("⚠️ usage es None — usando estimación manual")

        prompt_tokens = len(prompt) // 4
        completion_text = response.choices[0].message.content
        completion_tokens = len(completion_text) // 4

        class FakeUsage:
            def __init__(self, pt, ct):
                self.prompt_tokens = pt
                self.completion_tokens = ct
                self.total_tokens = pt + ct


        fake_usage = FakeUsage(prompt_tokens, completion_tokens)

        log_usage(
            provider="groq",
            model=model,
            usage=fake_usage,
            endpoint=endpoint,
            session_id=session_id,
            extra_json=extra_json
        )


    else:
        print("✅ usage detectado")
        print("🔥 tokens:", usage.prompt_tokens, usage.completion_tokens)

        log_usage(
                    provider="groq",
                    model=model,
                    usage=usage,
                    endpoint=endpoint,
                    session_id=session_id,
                    extra_json=extra_json
                )

    raw = response.choices[0].message.content
    return extract_json_from_text(raw)


def openai_llm(prompt: str, endpoint=None, session_id=None, extra_json=None) -> dict:
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



def gemini_llm(prompt: str, endpoint=None, session_id=None, extra_json=None) -> dict:
    client = get_gemini_client()
    if not client:
        raise RuntimeError("GEMINI_API_KEY no definida")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(
        model=model,
        contents=(
            "Eres un experto en metadatos sanitarios HealthDCAT-AP. "
            "Extrae campos del texto del usuario y devuelve SOLO un objeto JSON válido, "
            "sin explicaciones, sin markdown, sin texto adicional. "
            "Si un campo no está en el texto, devuelve null para ese campo.\n\n"
            + prompt
        ),
    )
    raw = response.text or ""
    return extract_json_from_text(raw)



# Utils


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
    result = {}
    for field_name in contract.keys():
        result[field_name] = parse_simple_field(field_name, user_input)
    return result


# Public API

def call_llm(prompt: str, contract: dict, user_input: str, endpoint=None, session_id=None, extra_json=None) -> dict:
    if get_use_openai():
        client = get_openai_client()
        if client:
            return openai_llm(prompt, endpoint=endpoint, session_id=session_id, extra_json=extra_json)

    if get_use_gemini():
        client = get_gemini_client()
        if client:
            return gemini_llm(prompt, endpoint=endpoint, session_id=session_id, extra_json=extra_json)

    client = get_groq_client()
    if client:
        return groq_llm(prompt, endpoint=endpoint, session_id=session_id, extra_json=extra_json)

    return mock_llm(prompt, contract, user_input)

def llm_available() -> bool:
    return bool(
        get_groq_client() or
        (get_use_openai() and get_openai_client()) or
        (get_use_gemini() and get_gemini_client())
    )
