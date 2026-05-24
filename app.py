import os
import uuid
import ssl
import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, send_from_directory
)
from werkzeug.utils import secure_filename

load_dotenv()

import db
from claude_service import get_mineral_info

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "minerais-secret-2024")

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.template_filter("format_date")
def format_date(value):
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%d/%m/%Y às %H:%M")
    return str(value)[:16].replace("T", " ")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def save_uploaded_file(file_obj):
    if not file_obj or file_obj.filename == "":
        return None
    if not allowed_file(file_obj.filename):
        return None
    ext = file_obj.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    safe_name = secure_filename(filename)
    file_obj.save(os.path.join(UPLOAD_FOLDER, safe_name))
    return f"uploads/{safe_name}"


def download_image_from_url(image_url):
    try:
        req = urllib.request.Request(image_url, headers={"User-Agent": "MineralCollection/1.0"})
        with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "jpg"}
            ext = ext_map.get(content_type.split(";")[0].strip(), "jpg")
            filename = f"{uuid.uuid4().hex}.{ext}"
            dest = os.path.join(UPLOAD_FOLDER, filename)
            with open(dest, "wb") as f:
                f.write(resp.read())
            return f"uploads/{filename}"
    except Exception:
        return None


@app.route("/")
def gallery():
    minerals = db.find_all()
    return render_template("index.html", minerals=minerals)


@app.route("/adicionar", methods=["GET"])
def add_form():
    has_api_key = bool(os.getenv("ANTHROPIC_API_KEY", "").strip())
    return render_template("add.html", has_api_key=has_api_key)


@app.route("/buscar-imagem")
def buscar_imagem():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    try:
        query = urllib.parse.quote(q + " mineral")
        search_url = (
            "https://commons.wikimedia.org/w/api.php"
            f"?action=query&list=search&srsearch={query}"
            "&srnamespace=6&format=json&srlimit=12"
        )
        req = urllib.request.Request(search_url, headers={"User-Agent": "MineralCollection/1.0"})
        with urllib.request.urlopen(req, context=_ssl_ctx(), timeout=10) as r:
            data = json.load(r)

        titles = [item["title"] for item in data.get("query", {}).get("search", [])]
        if not titles:
            return jsonify([])

        titles_param = urllib.parse.quote("|".join(titles[:10]))
        thumb_url = (
            "https://commons.wikimedia.org/w/api.php"
            f"?action=query&titles={titles_param}"
            "&prop=imageinfo&iiprop=url|thumburl&iiurlwidth=320&format=json"
        )
        req2 = urllib.request.Request(thumb_url, headers={"User-Agent": "MineralCollection/1.0"})
        with urllib.request.urlopen(req2, context=_ssl_ctx(), timeout=10) as r:
            thumb_data = json.load(r)

        results = []
        for page in thumb_data.get("query", {}).get("pages", {}).values():
            if "imageinfo" in page:
                info = page["imageinfo"][0]
                thumb = info.get("thumburl", "")
                url = info.get("url", "")
                if thumb and url:
                    results.append({
                        "title": page["title"].replace("File:", ""),
                        "thumb": thumb,
                        "url": url,
                    })
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/adicionar", methods=["POST"])
def add_mineral():
    name = request.form.get("name", "").strip()
    photo = request.files.get("photo")
    image_url = request.form.get("image_url", "").strip()

    if not name and (not photo or photo.filename == "") and not image_url:
        flash("Informe o nome do mineral, envie uma foto ou selecione uma imagem da internet.")
        return redirect(url_for("add_form"))

    # Resolve image: uploaded file takes priority, then web URL
    image_path = save_uploaded_file(photo)
    if not image_path and image_url:
        image_path = download_image_from_url(image_url)

    full_image_path = os.path.join(UPLOAD_FOLDER, os.path.basename(image_path)) if image_path else None

    try:
        info = get_mineral_info(
            name=name if name else None,
            image_path=full_image_path,
            name_hint=name if name and image_path else None,
        )
    except Exception as e:
        if image_path and full_image_path and os.path.exists(full_image_path):
            os.remove(full_image_path)
        flash(f"Erro ao obter informações do mineral: {e}")
        return redirect(url_for("add_form"))

    doc = {
        "name": info.get("name") or (name.title() if name else "Mineral"),
        "description": info.get("description", ""),
        "curiosity": info.get("curiosity", ""),
        "main_use": info.get("main_use", ""),
        "chemical_formula": info.get("chemical_formula"),
        "hardness": _safe_float(info.get("hardness")),
        "crystal_system": info.get("crystal_system"),
        "image_path": image_path,
        "created_at": datetime.now(timezone.utc),
    }
    mineral_id = db.insert_mineral(doc)
    return redirect(url_for("mineral_detail", mineral_id=mineral_id))


@app.route("/mineral/<mineral_id>")
def mineral_detail(mineral_id):
    mineral = db.find_by_id(mineral_id)
    if not mineral:
        flash("Mineral não encontrado.")
        return redirect(url_for("gallery"))
    return render_template("detail.html", mineral=mineral)


@app.route("/mineral/<mineral_id>/editar", methods=["GET"])
def edit_form(mineral_id):
    mineral = db.find_by_id(mineral_id)
    if not mineral:
        flash("Mineral não encontrado.")
        return redirect(url_for("gallery"))
    return render_template("edit.html", mineral=mineral)


@app.route("/mineral/<mineral_id>/editar", methods=["POST"])
def edit_mineral(mineral_id):
    mineral = db.find_by_id(mineral_id)
    if not mineral:
        flash("Mineral não encontrado.")
        return redirect(url_for("gallery"))

    photo = request.files.get("photo")
    image_url = request.form.get("image_url", "").strip()
    image_path = mineral.get("image_path")

    new_path = None
    if photo and photo.filename != "":
        new_path = save_uploaded_file(photo)
    elif image_url:
        new_path = download_image_from_url(image_url)

    if new_path:
        if image_path:
            old_full = os.path.join(app.root_path, "static", image_path)
            if os.path.exists(old_full):
                os.remove(old_full)
        image_path = new_path

    updates = {
        "name": request.form.get("name", mineral["name"]).strip(),
        "description": request.form.get("description", mineral.get("description", "")).strip(),
        "curiosity": request.form.get("curiosity", mineral.get("curiosity", "")).strip(),
        "main_use": request.form.get("main_use", mineral.get("main_use", "")).strip(),
        "chemical_formula": request.form.get("chemical_formula", "").strip() or None,
        "hardness": _safe_float(request.form.get("hardness", "")),
        "crystal_system": request.form.get("crystal_system", "").strip() or None,
        "image_path": image_path,
    }
    db.update_mineral(mineral_id, updates)
    return redirect(url_for("mineral_detail", mineral_id=mineral_id))


@app.route("/mineral/<mineral_id>", methods=["DELETE"])
def delete_mineral(mineral_id):
    mineral = db.find_by_id(mineral_id)
    if not mineral:
        return jsonify({"success": False, "error": "Não encontrado"}), 404

    image_path = mineral.get("image_path")
    if image_path:
        full_path = os.path.join(app.root_path, "static", image_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    db.delete_mineral(mineral_id)
    return jsonify({"success": True, "redirect": url_for("gallery")})


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    app.run(debug=True)
