#!/usr/bin/env python3
import io
import base64
import numpy as np
from flask import Flask, request, jsonify, send_file, send_from_directory
from PIL import Image
import os

app = Flask(__name__, static_folder=".")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB

# --- Chromakey Logic ---
def remove_chroma_key(img: Image.Image, key_color: tuple, tolerance: int, feather: int) -> Image.Image:
    img = img.convert("RGBA")
    data = np.array(img, dtype=np.float32)
    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    kr, kg, kb = key_color
    dist = np.sqrt((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2)
    alpha = np.clip((dist - tolerance) / max(feather, 1), 0, 1) * 255
    data[:, :, 3] = alpha
    return Image.fromarray(data.astype(np.uint8), "RGBA")

def corridor_key(img: Image.Image, key_color: tuple, gain: float, black_point: float, despill: float) -> Image.Image:
    img = img.convert("RGBA")
    data = np.array(img, dtype=np.float32)
    # kR, kG, kB = key_color # Not strictly needed if we assume Green/Blue based on max channel
    R, G, B = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    
    # Identify primary key channel
    kr, kg, kb = key_color
    if kg > kr and kg > kb:
        diff = G - np.maximum(R, B)
        # Despill
        data[:, :, 1] = np.minimum(G, (R + B) * 0.5 * despill)
    elif kb > kr and kb > kg:
        diff = B - np.maximum(R, G)
        # Despill
        data[:, :, 2] = np.minimum(B, (R + G) * 0.5 * despill)
    else:
        diff = np.abs(G - kg) # Fallback
        
    diff_norm = diff / 255.0
    alpha = 1.0 - (diff_norm * gain)
    alpha = np.clip(alpha + black_point, 0, 1) * 255.0
    
    data[:, :, 3] = alpha
    return Image.fromarray(data.astype(np.uint8), "RGBA")

@app.route("/")
def index():
    return send_file("index.html")

@app.route("/chromakey-remover/")
def chromakey_index():
    return send_file("chromakey-remover/index.html")

@app.route("/preview", methods=["POST"])
def preview():
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "파일 없음"}), 400
    try:
        mode = request.form.get("mode", "standard")
        r = int(request.form.get("r", 0))
        g = int(request.form.get("g", 255))
        b = int(request.form.get("b", 0))
        
        img = Image.open(file.stream)
        
        if mode == "corridorkey":
            gain = float(request.form.get("gain", 1.5))
            black_point = float(request.form.get("black_point", 0.0))
            despill = float(request.form.get("despill", 1.0))
            result = corridor_key(img, (r, g, b), gain, black_point, despill)
        else:
            tolerance = int(request.form.get("tolerance", 60))
            feather = int(request.form.get("feather", 5))
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
    file = request.files.get("image")
    if not file:
        return jsonify({"error": "파일 없음"}), 400
    try:
        mode = request.form.get("mode", "standard")
        r = int(request.form.get("r", 0))
        g = int(request.form.get("g", 255))
        b = int(request.form.get("b", 0))
        
        img = Image.open(file.stream)
        
        if mode == "corridorkey":
            gain = float(request.form.get("gain", 1.5))
            black_point = float(request.form.get("black_point", 0.0))
            despill = float(request.form.get("despill", 1.0))
            result = corridor_key(img, (r, g, b), gain, black_point, despill)
        else:
            tolerance = int(request.form.get("tolerance", 60))
            feather = int(request.form.get("feather", 5))
            result = remove_chroma_key(img, (r, g, b), tolerance, feather)
            
        buf = io.BytesIO()
        result.save(buf, "PNG")
        buf.seek(0)
        original_name = file.filename or "image"
        base = original_name.rsplit(".", 1)[0]
        return send_file(buf, mimetype="image/png", as_attachment=True, download_name=f"{base}_transparent.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Static File Serving ---
@app.route("/sound-editor/<path:path>")
def sound_editor_files(path):
    return send_from_directory("sound-editor", path)

@app.route("/sound-editor/")
def sound_editor_index():
    return send_file("sound-editor/index.html")

@app.route("/<path:path>")
def root_files(path):
    return send_from_directory(".", path)

if __name__ == "__main__":
    print("🚀 Solo Dev Tools Server Started")
    print("   Access at: http://localhost:5000")
    print("   Stop with: Ctrl+C\n")
    app.run(host="127.0.0.1", port=5000, debug=True)
