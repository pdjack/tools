# Tools

다양한 미디어 편집 도구 모음입니다.

---

## 1. 크로마키 제거기 (CLI)

PNG 이미지에서 특정 색상을 제거하여 투명하게 만드는 커맨드라인 도구입니다.

### 필수 패키지

```bash
pip install numpy pillow
```

### 사용법

```bash
cd chromakey-remover

# 기본 사용 (초록색 제거)
python chromakey_remover.py input.png

# 출력 파일 지정
python chromakey_remover.py input.png -o output.png

# 색상 지정 (이름, RGB, HEX)
python chromakey_remover.py input.png -c blue
python chromakey_remover.py input.png -c "0,255,0"
python chromakey_remover.py input.png -c "#00FF00"

# 허용 범위 및 페더링 조절
python chromakey_remover.py input.png -t 80 -f 10

# 여러 파일 일괄 처리
python chromakey_remover.py *.png
```

### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-o, --output` | 출력 파일 경로 | `{파일명}_transparent.png` |
| `-c, --color` | 제거할 색상 (`green`, `blue`, `red`, `white`, `black`, `R,G,B`, `#RRGGBB`) | `green` |
| `-t, --tolerance` | 색상 허용 범위 (0~255) | `60` |
| `-f, --feather` | 경계 페더링 강도 (0~50) | `5` |

---

## 2. 크로마키 제거기 (웹앱)

브라우저에서 크로마키를 제거할 수 있는 Flask 웹앱입니다.

### 필수 패키지

```bash
pip install flask numpy pillow
```

### 실행

```bash
cd chromakey-remover
python chromakey_webapp.py
```

브라우저에서 **http://localhost:5000** 접속

### 기능

- 이미지 업로드 (드래그 앤 드롭 지원)
- 크로마키 색상 선택 (프리셋 / 컬러피커 / RGB 직접 입력)
- 허용 범위 및 경계 부드럽게 조절
- 실시간 미리보기
- 투명 배경 PNG 다운로드

---

## 3. Sound Editor (웹)

브라우저에서 사운드 파일을 편집할 수 있는 웹 도구입니다.

### 실행

별도 설치 없이 로컬 HTTP 서버로 실행합니다.

```bash
cd sound-editor
python -m http.server 8080
```

> PowerShell에서는 `cd sound-editor; python -m http.server 8080`

브라우저에서 **http://localhost:8080** 접속

### 기능

- 오디오 파일 업로드 (드래그 앤 드롭 지원)
- 파형(waveform) 시각화
- 구간 선택 및 잘라내기 (트리밍)
- WAV 파일로 내보내기
