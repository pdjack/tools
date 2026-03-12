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
    return HTML_PAGE


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


HTML_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>크로마키 제거기</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #1a1a2e; color: #e0e0e0; min-height: 100vh;
    display: flex; flex-direction: column; align-items: center;
  }
  header {
    width: 100%; padding: 20px 32px;
    background: #16213e;
    border-bottom: 1px solid #0f3460;
  }
  header h1 { font-size: 1.4rem; color: #e94560; }
  header p { font-size: 0.82rem; color: #888; margin-top: 2px; }

  .container {
    display: grid;
    grid-template-columns: 320px 1fr;
    gap: 24px;
    padding: 24px 32px;
    width: 100%; max-width: 1400px;
  }

  /* ─── 왼쪽 패널 ─── */
  .panel {
    background: #16213e;
    border-radius: 12px;
    padding: 24px;
    border: 1px solid #0f3460;
    display: flex; flex-direction: column; gap: 20px;
    height: fit-content;
  }
  .panel h2 { font-size: 0.95rem; color: #aaa; text-transform: uppercase; letter-spacing: .05em; }

  /* 드롭존 */
  .dropzone {
    border: 2px dashed #0f3460;
    border-radius: 8px;
    padding: 32px 16px;
    text-align: center;
    cursor: pointer;
    transition: border-color .2s, background .2s;
    position: relative;
  }
  .dropzone:hover, .dropzone.drag { border-color: #e94560; background: #1a1a3e; }
  .dropzone input[type=file] {
    position: absolute; inset: 0; opacity: 0; cursor: pointer;
  }
  .dropzone .icon { font-size: 2.5rem; }
  .dropzone p { font-size: 0.85rem; color: #888; margin-top: 8px; }
  .dropzone .filename { color: #e94560; font-size: 0.85rem; margin-top: 6px; word-break: break-all; }

  /* 색상 선택 */
  .color-section { display: flex; flex-direction: column; gap: 12px; }
  .color-presets { display: flex; gap: 8px; flex-wrap: wrap; }
  .preset-btn {
    width: 36px; height: 36px; border-radius: 50%;
    border: 3px solid transparent; cursor: pointer;
    transition: border-color .15s, transform .15s;
  }
  .preset-btn:hover { transform: scale(1.1); }
  .preset-btn.active { border-color: #fff; }

  .color-picker-row {
    display: flex; align-items: center; gap: 10px;
  }
  .color-preview {
    width: 40px; height: 40px; border-radius: 8px;
    border: 2px solid #0f3460; flex-shrink: 0;
    cursor: pointer; position: relative; overflow: hidden;
  }
  .color-preview input[type=color] {
    position: absolute; inset: -4px; opacity: 0; cursor: pointer; width: 120%; height: 120%;
  }
  .rgb-inputs { display: flex; gap: 6px; flex: 1; }
  .rgb-inputs input {
    width: 100%; padding: 6px; border-radius: 6px;
    border: 1px solid #0f3460; background: #1a1a2e;
    color: #e0e0e0; text-align: center; font-size: 0.82rem;
  }
  .rgb-labels { display: flex; gap: 6px; }
  .rgb-labels span { flex: 1; text-align: center; font-size: 0.7rem; color: #888; }

  /* 슬라이더 */
  .slider-group { display: flex; flex-direction: column; gap: 14px; }
  .slider-item label {
    display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 6px;
  }
  .slider-item label span { color: #e94560; font-weight: 600; }
  input[type=range] {
    width: 100%; accent-color: #e94560; height: 4px;
  }
  .slider-desc { font-size: 0.72rem; color: #666; margin-top: 2px; }

  /* 버튼 */
  .btn-group { display: flex; flex-direction: column; gap: 8px; }
  .btn {
    padding: 12px; border-radius: 8px; border: none;
    font-size: 0.9rem; font-weight: 600; cursor: pointer;
    transition: opacity .15s, transform .1s;
  }
  .btn:active { transform: scale(.97); }
  .btn:disabled { opacity: .4; cursor: not-allowed; }
  .btn-primary { background: #e94560; color: #fff; }
  .btn-secondary { background: #0f3460; color: #e0e0e0; }
  .btn-primary:hover:not(:disabled) { opacity: .85; }
  .btn-secondary:hover:not(:disabled) { opacity: .75; }

  /* ─── 오른쪽 프리뷰 ─── */
  .preview-panel {
    background: #16213e;
    border-radius: 12px;
    border: 1px solid #0f3460;
    display: flex; flex-direction: column;
    min-height: 480px; overflow: hidden;
  }
  .preview-tabs {
    display: flex; border-bottom: 1px solid #0f3460;
  }
  .tab-btn {
    padding: 14px 24px; border: none; background: none;
    color: #888; cursor: pointer; font-size: 0.88rem;
    border-bottom: 2px solid transparent; transition: color .15s;
  }
  .tab-btn.active { color: #e94560; border-bottom-color: #e94560; }
  .tab-btn:hover:not(.active) { color: #ccc; }

  .preview-content {
    flex: 1; display: flex; align-items: center; justify-content: center;
    padding: 24px; position: relative;
  }
  /* 체커보드 배경 (투명도 표시) */
  .checker {
    background-image:
      linear-gradient(45deg, #555 25%, transparent 25%),
      linear-gradient(-45deg, #555 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #555 75%),
      linear-gradient(-45deg, transparent 75%, #555 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    background-color: #333;
  }
  .preview-area {
    width: 100%; height: 100%;
    display: flex; align-items: center; justify-content: center;
    border-radius: 8px; overflow: hidden;
  }
  .preview-area img {
    max-width: 100%; max-height: 480px;
    object-fit: contain; border-radius: 4px;
  }
  .placeholder {
    text-align: center; color: #555;
  }
  .placeholder .icon { font-size: 3rem; }
  .placeholder p { margin-top: 12px; font-size: 0.9rem; }

  .status-bar {
    padding: 10px 20px;
    border-top: 1px solid #0f3460;
    font-size: 0.78rem; color: #666;
    display: flex; justify-content: space-between;
  }
  .status-bar .status-text { }
  .spinner {
    display: inline-block; width: 14px; height: 14px;
    border: 2px solid #444; border-top-color: #e94560;
    border-radius: 50%; animation: spin .7s linear infinite;
    vertical-align: middle; margin-right: 6px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<header>
  <h1>크로마키 제거기</h1>
  <p>PNG 이미지에서 특정 색상을 제거해 투명하게 만듭니다</p>
</header>

<div class="container">
  <!-- 왼쪽 패널 -->
  <div class="panel">
    <h2>이미지 선택</h2>
    <div class="dropzone" id="dropzone">
      <input type="file" id="fileInput" accept="image/*">
      <div class="icon">🖼️</div>
      <p>클릭하거나 파일을 드래그하세요</p>
      <div class="filename" id="filename"></div>
    </div>

    <h2>크로마키 색상</h2>
    <div class="color-section">
      <div class="color-presets">
        <button class="preset-btn active" style="background:#00ff00" data-rgb="0,255,0" title="초록"></button>
        <button class="preset-btn" style="background:#0000ff" data-rgb="0,0,255" title="파랑"></button>
        <button class="preset-btn" style="background:#ff0000" data-rgb="255,0,0" title="빨강"></button>
        <button class="preset-btn" style="background:#ffffff;border-color:#555" data-rgb="255,255,255" title="흰색"></button>
        <button class="preset-btn" style="background:#000000" data-rgb="0,0,0" title="검정"></button>
      </div>
      <div class="color-picker-row">
        <div class="color-preview" id="colorPreview" style="background:#00ff00">
          <input type="color" id="colorPicker" value="#00ff00">
        </div>
        <div style="flex:1">
          <div class="rgb-inputs">
            <input type="number" id="rVal" min="0" max="255" value="0">
            <input type="number" id="gVal" min="0" max="255" value="255">
            <input type="number" id="bVal" min="0" max="255" value="0">
          </div>
          <div class="rgb-labels">
            <span>R</span><span>G</span><span>B</span>
          </div>
        </div>
      </div>
    </div>

    <h2>설정</h2>
    <div class="slider-group">
      <div class="slider-item">
        <label>허용 범위 <span id="tolVal">60</span></label>
        <input type="range" id="tolerance" min="0" max="200" value="60">
        <div class="slider-desc">높을수록 더 넓은 색상 범위를 제거합니다</div>
      </div>
      <div class="slider-item">
        <label>경계 부드럽게 <span id="featherVal">5</span></label>
        <input type="range" id="feather" min="0" max="80" value="5">
        <div class="slider-desc">높을수록 가장자리가 자연스럽게 처리됩니다</div>
      </div>
    </div>

    <div class="btn-group">
      <button class="btn btn-primary" id="previewBtn" disabled>미리보기 생성</button>
      <button class="btn btn-secondary" id="downloadBtn" disabled>PNG 다운로드</button>
    </div>
  </div>

  <!-- 오른쪽 프리뷰 -->
  <div class="preview-panel">
    <div class="preview-tabs">
      <button class="tab-btn active" data-tab="result">결과</button>
      <button class="tab-btn" data-tab="original">원본</button>
    </div>
    <div class="preview-content checker" id="previewContent">
      <div class="preview-area">
        <div class="placeholder" id="placeholder">
          <div class="icon">🎨</div>
          <p>이미지를 업로드하면<br>미리보기가 여기에 표시됩니다</p>
        </div>
        <img id="previewImg" style="display:none">
      </div>
    </div>
    <div class="status-bar">
      <span class="status-text" id="statusText">대기 중</span>
      <span id="imgInfo"></span>
    </div>
  </div>
</div>

<script>
  let currentFile = null;
  let originalSrc = null;
  let currentTab = 'result';

  const fileInput = document.getElementById('fileInput');
  const dropzone = document.getElementById('dropzone');
  const filename = document.getElementById('filename');
  const previewBtn = document.getElementById('previewBtn');
  const downloadBtn = document.getElementById('downloadBtn');
  const previewImg = document.getElementById('previewImg');
  const placeholder = document.getElementById('placeholder');
  const statusText = document.getElementById('statusText');
  const imgInfo = document.getElementById('imgInfo');
  const colorPicker = document.getElementById('colorPicker');
  const colorPreview = document.getElementById('colorPreview');
  const rVal = document.getElementById('rVal');
  const gVal = document.getElementById('gVal');
  const bVal = document.getElementById('bVal');
  const tolerance = document.getElementById('tolerance');
  const feather = document.getElementById('feather');

  // 드래그앤드롭
  dropzone.addEventListener('dragover', e => { e.preventDefault(); dropzone.classList.add('drag'); });
  dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag'));
  dropzone.addEventListener('drop', e => {
    e.preventDefault(); dropzone.classList.remove('drag');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) handleFile(fileInput.files[0]);
  });

  function handleFile(file) {
    currentFile = file;
    filename.textContent = file.name;
    previewBtn.disabled = false;

    const reader = new FileReader();
    reader.onload = e => {
      originalSrc = e.target.result;
      if (currentTab === 'original') showOriginal();
      else showPlaceholder();
    };
    reader.readAsDataURL(file);
    statusText.textContent = '파일 로드됨: ' + file.name;
    imgInfo.textContent = (file.size / 1024).toFixed(1) + ' KB';
  }

  // 색상 동기화
  function updateColorFromRGB() {
    const r = parseInt(rVal.value) || 0;
    const g = parseInt(gVal.value) || 0;
    const b = parseInt(bVal.value) || 0;
    const hex = '#' + [r, g, b].map(v => Math.min(255, Math.max(0, v)).toString(16).padStart(2, '0')).join('');
    colorPicker.value = hex;
    colorPreview.style.background = hex;
    document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
  }

  function updateColorFromHex(hex) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    rVal.value = r; gVal.value = g; bVal.value = b;
    colorPreview.style.background = hex;
  }

  [rVal, gVal, bVal].forEach(el => el.addEventListener('input', updateColorFromRGB));
  colorPicker.addEventListener('input', e => {
    updateColorFromHex(e.target.value);
    document.querySelectorAll('.preset-btn').forEach(btn => btn.classList.remove('active'));
  });

  document.querySelectorAll('.preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const [r, g, b] = btn.dataset.rgb.split(',').map(Number);
      rVal.value = r; gVal.value = g; bVal.value = b;
      updateColorFromRGB();
      btn.classList.add('active');
      colorPicker.value = colorPreview.style.background;
    });
  });

  // 슬라이더
  tolerance.addEventListener('input', () => document.getElementById('tolVal').textContent = tolerance.value);
  feather.addEventListener('input', () => document.getElementById('featherVal').textContent = feather.value);

  // 탭 전환
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentTab = btn.dataset.tab;
      if (currentTab === 'original') showOriginal();
      else if (previewImg.dataset.result) showResult();
      else showPlaceholder();
    });
  });

  function showOriginal() {
    if (!originalSrc) return;
    previewImg.src = originalSrc;
    previewImg.style.display = '';
    placeholder.style.display = 'none';
  }
  function showResult() {
    previewImg.src = previewImg.dataset.result;
    previewImg.style.display = '';
    placeholder.style.display = 'none';
  }
  function showPlaceholder() {
    previewImg.style.display = 'none';
    placeholder.style.display = '';
  }

  // 미리보기
  previewBtn.addEventListener('click', async () => {
    if (!currentFile) return;
    setLoading(true, '처리 중...');
    const form = buildFormData();
    try {
      const res = await fetch('/preview', { method: 'POST', body: form });
      const data = await res.json();
      if (data.error) { statusText.textContent = '오류: ' + data.error; return; }
      previewImg.dataset.result = data.image;
      if (currentTab === 'result') showResult();
      downloadBtn.disabled = false;
      statusText.textContent = '미리보기 완료';
    } catch (e) {
      statusText.textContent = '오류: ' + e.message;
    } finally {
      setLoading(false);
    }
  });

  // 다운로드
  downloadBtn.addEventListener('click', async () => {
    if (!currentFile) return;
    setLoading(true, '다운로드 준비 중...');
    const form = buildFormData();
    try {
      const res = await fetch('/download', { method: 'POST', body: form });
      if (!res.ok) { statusText.textContent = '다운로드 오류'; return; }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const base = currentFile.name.replace(/\.[^.]+$/, '');
      a.href = url; a.download = base + '_transparent.png';
      a.click(); URL.revokeObjectURL(url);
      statusText.textContent = '다운로드 완료';
    } catch (e) {
      statusText.textContent = '오류: ' + e.message;
    } finally {
      setLoading(false);
    }
  });

  function buildFormData() {
    const form = new FormData();
    form.append('image', currentFile);
    form.append('r', rVal.value);
    form.append('g', gVal.value);
    form.append('b', bVal.value);
    form.append('tolerance', tolerance.value);
    form.append('feather', feather.value);
    return form;
  }

  function setLoading(on, msg = '') {
    previewBtn.disabled = on;
    statusText.innerHTML = on ? `<span class="spinner"></span>${msg}` : statusText.textContent;
    if (!on) previewBtn.disabled = !currentFile;
  }
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print("🎨 크로마키 제거 웹앱 시작")
    print("   접속: http://localhost:5000")
    print("   종료: Ctrl+C\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
