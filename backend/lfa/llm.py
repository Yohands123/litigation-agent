import json

from openai import BadRequestError, OpenAI

from .config import OPENAI_API_KEY, OPENAI_MODEL

_client = OpenAI(api_key=OPENAI_API_KEY, timeout=60)


def _create(**kwargs):
    # Deterministic output helps evals; some models reject temperature, so fall back.
    try:
        return _client.chat.completions.create(temperature=0, **kwargs)
    except BadRequestError as e:
        if "temperature" in str(e).lower():
            return _client.chat.completions.create(**kwargs)
        raise


def chat_json(system: str, user: str) -> dict:
    resp = _create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return json.loads(resp.choices[0].message.content or "{}")


def chat_text(system: str, user: str) -> str:
    resp = _create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return (resp.choices[0].message.content or "").strip()
