#!/usr/bin/env python3
"""
크로마키 제거 프로그램
PNG 파일에서 특정 색상(기본: 초록색)을 투명하게 변환합니다.
"""

import sys
import os
import argparse
import numpy as np
from PIL import Image


def remove_chroma_key(
    input_path: str,
    output_path: str,
    key_color: tuple[int, int, int] = (0, 255, 0),
    tolerance: int = 60,
    feather: int = 5,
):
    """
    이미지에서 크로마키 색상을 제거하여 투명하게 만듭니다.

    Args:
        input_path: 입력 이미지 경로
        output_path: 출력 이미지 경로 (PNG)
        key_color: 제거할 색상 (R, G, B)
        tolerance: 색상 허용 범위 (0~255, 높을수록 더 넓은 범위 제거)
        feather: 경계 부드럽게 처리 (0=없음, 높을수록 부드러움)
    """
    img = Image.open(input_path).convert("RGBA")
    data = np.array(img, dtype=np.float32)

    r, g, b = data[:, :, 0], data[:, :, 1], data[:, :, 2]
    kr, kg, kb = key_color

    # 각 채널의 거리 계산
    dist = np.sqrt((r - kr) ** 2 + (g - kg) ** 2 + (b - kb) ** 2)

    # tolerance 기준으로 알파 마스크 생성
    alpha = np.clip((dist - tolerance) / max(feather, 1), 0, 1) * 255
    data[:, :, 3] = alpha

    result = Image.fromarray(data.astype(np.uint8), "RGBA")
    result.save(output_path, "PNG")
    print(f"저장 완료: {output_path}")


def parse_color(color_str: str) -> tuple[int, int, int]:
    """'R,G,B' 또는 '#RRGGBB' 형식 파싱"""
    color_str = color_str.strip()
    if color_str.startswith("#"):
        hex_color = color_str.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    parts = [int(x.strip()) for x in color_str.split(",")]
    if len(parts) != 3:
        raise ValueError(f"색상 형식 오류: '{color_str}' → 예: '0,255,0' 또는 '#00FF00'")
    return tuple(parts)


def main():
    parser = argparse.ArgumentParser(
        description="PNG 파일 크로마키 제거 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python chromakey_remover.py input.png
  python chromakey_remover.py input.png -o output.png
  python chromakey_remover.py input.png -c "0,255,0" -t 80
  python chromakey_remover.py input.png -c "#00FF00" -t 60 -f 10
  python chromakey_remover.py input.png -c blue   (파란색 제거)
  python chromakey_remover.py *.png               (여러 파일 처리)

지정 색상 이름: green(기본), blue, red, white, black
        """,
    )
    parser.add_argument("input", nargs="+", help="입력 PNG 파일 (여러 개 가능)")
    parser.add_argument("-o", "--output", help="출력 파일 경로 (단일 파일 처리 시)")
    parser.add_argument(
        "-c",
        "--color",
        default="green",
        help="크로마키 색상: 이름(green/blue/red/white/black) 또는 'R,G,B' 또는 '#RRGGBB' (기본: green)",
    )
    parser.add_argument(
        "-t",
        "--tolerance",
        type=int,
        default=60,
        help="색상 허용 범위 0~255 (기본: 60)",
    )
    parser.add_argument(
        "-f",
        "--feather",
        type=int,
        default=5,
        help="경계 페더링 강도 0~50 (기본: 5)",
    )

    args = parser.parse_args()

    # 색상 이름 → RGB 변환
    color_presets = {
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "red": (255, 0, 0),
        "white": (255, 255, 255),
        "black": (0, 0, 0),
    }

    color_input = args.color.lower()
    if color_input in color_presets:
        key_color = color_presets[color_input]
    else:
        try:
            key_color = parse_color(args.color)
        except ValueError as e:
            print(f"오류: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"크로마키 색상: RGB{key_color}, 허용범위: {args.tolerance}, 페더링: {args.feather}")

    files = args.input
    if len(files) == 1:
        input_path = files[0]
        if not os.path.exists(input_path):
            print(f"오류: 파일을 찾을 수 없습니다 → {input_path}", file=sys.stderr)
            sys.exit(1)
        if args.output:
            output_path = args.output
        else:
            base, _ = os.path.splitext(input_path)
            output_path = base + "_transparent.png"
        remove_chroma_key(input_path, output_path, key_color, args.tolerance, args.feather)
    else:
        # 여러 파일 처리
        for input_path in files:
            if not os.path.exists(input_path):
                print(f"건너뜀 (파일 없음): {input_path}", file=sys.stderr)
                continue
            base, _ = os.path.splitext(input_path)
            output_path = base + "_transparent.png"
            try:
                remove_chroma_key(input_path, output_path, key_color, args.tolerance, args.feather)
            except Exception as e:
                print(f"오류 ({input_path}): {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
