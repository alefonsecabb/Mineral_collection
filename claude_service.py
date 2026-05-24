import os
import json
import base64
from io import BytesIO
from PIL import Image
import anthropic
from mineral_database import find_mineral, generic_mineral

SYSTEM_PROMPT = """Você é um mineralogista especialista escrevendo para um catálogo pessoal de coleção de minerais.
Sempre responda em português brasileiro.
Responda SOMENTE com um objeto JSON válido contendo exatamente estas chaves:
  name, description, curiosity, main_use, chemical_formula, hardness, crystal_system

- name: nome canônico do mineral em português
- description: 2 a 3 parágrafos cobrindo formação, aparência e contexto geológico (separados por \\n\\n)
- curiosity: uma curiosidade histórica ou científica interessante
- main_use: principal aplicação industrial, tecnológica ou ornamental
- chemical_formula: use subscritos Unicode onde possível (ex: SiO₂, Fe₃O₄)
- hardness: número float na escala de Mohs de 1.0 a 10.0; null se desconhecido
- crystal_system: ex: "Trigonal", "Cúbico", "Monoclínico"; null se amorfo ou desconhecido

Não inclua nenhum texto fora do JSON. Não use blocos de código markdown."""


def _parse_response(text: str) -> dict:
    text = text.strip()
    if "```" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        text = text[start:end]
    return json.loads(text)


def _resize_image(image_path: str) -> tuple[bytes, str]:
    ext = os.path.splitext(image_path)[1].lower()
    media_types = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    media_type = media_types.get(ext, "image/jpeg")

    with Image.open(image_path) as img:
        img.thumbnail((1024, 1024))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = BytesIO()
        fmt = "PNG" if media_type == "image/png" else "JPEG"
        img.save(buf, format=fmt, quality=85)
        return buf.getvalue(), media_type


def generate_from_name(name: str) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Gere as informações mineralógicas para o mineral: {name}"}],
    )
    return _parse_response(response.content[0].text)


def identify_from_image(image_path: str, name_hint: str = None) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    img_bytes, media_type = _resize_image(image_path)
    b64 = base64.b64encode(img_bytes).decode("utf-8")

    text = "Identifique o mineral nesta imagem e gere suas informações mineralógicas completas."
    if name_hint:
        text += f" O nome fornecido pelo usuário é: {name_hint}"

    content = [
        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
        {"type": "text", "text": text},
    ]
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    return _parse_response(response.content[0].text)


def get_mineral_info(name: str = None, image_path: str = None, name_hint: str = None) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    if api_key:
        if image_path:
            return identify_from_image(image_path, name_hint=name or name_hint)
        return generate_from_name(name)

    if name:
        result = find_mineral(name)
        if result:
            return result
        return generic_mineral(name)

    if name_hint:
        result = find_mineral(name_hint)
        if result:
            return result
        return generic_mineral(name_hint)

    return generic_mineral("Mineral desconhecido")
