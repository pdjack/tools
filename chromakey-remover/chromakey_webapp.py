#!/usr/bin/env python3
"""
크로마키 제거 웹앱 (Flask)
실행: python3 chromakey_webapp.py
접속: http://localhost:5000
"""

import io
import base64
import numpy as np
from flask import Flask, request, jsonify, send_file
from PIL import Image

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB


def remove_chroma_key(img: Image.Image, key_color: tuple, tolerance: int, feather: int) -> Image.Image:
    img = img.convert("RGBA")
    data = np.array(img, dtype=np.float32)
    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    kr, kg, kb = key_color
    dist = np.sqrt((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2)
    alpha = np.clip((dist - tolerance) / max(feather, 1), 0, 1) * 255
    data[:, :, 3] = alpha
    return Image.fromarray(data.astype(np.uint8), "RGBA")


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/preview", methods=["POST"])
def preview():
    """미리보기: base64로 반환"""
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "파일 없음"}), 400
    try:
        r = int(request.form.get("r", 0))
        g = int(request.form.get("g", 255))
        b = int(request.form.get("b", 0))
        tolerance = int(request.form.get("tolerance", 60))
        feather = int(request.form.get("feather", 5))

        img = Image.open(file.stream)
        result = remove_chroma_key(img, (r, g, b), tolerance, feather)

        buf = io.BytesIO()
        result.save(buf, "PNG")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        return jsonify({"image": f"data:image/png;base64,{encoded}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download", methods=["POST"])
def download():
    """다운로드: PNG 파일 반환"""
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "파일 없음"}), 400
    try:
        r = int(request.form.get("r", 0))
        g = int(request.form.get("g", 255))
        b = int(request.form.get("b", 0))
        tolerance = int(request.form.get("tolerance", 60))
        feather = int(request.form.get("feather", 5))

        img = Image.open(file.stream)
        result = remove_chroma_key(img, (r, g, b), tolerance, feather)

        buf = io.BytesIO()
        result.save(buf, "PNG")
        buf.seek(0)

        original_name = file.filename or "image"
        base = original_name.rsplit(".", 1)[0]
        return send_file(buf, mimetype="image/png", as_attachment=True, download_name=f"{base}_transparent.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("🎨 크로마키 제거 웹앱 시작")
    print("   접속: http://localhost:5000")
    print("   종료: Ctrl+C\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
