#!/usr/bin/env python3
"""Render the 25 unique source documents as scan-style PNGs for the image-extraction condition.

Deterministic given the fixed seed. Reproduces the archived images/*.png byte for byte with
Pillow 12.3.0 and the DejaVu fonts shipped with Debian (fonts-dejavu-core).

Usage: python3 render_images.py --docs prompts/extraction_docs.jsonl --output images
"""
import argparse
import json
import random
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

SEED = 20261004
FONT_DIR = Path('/usr/share/fonts/truetype/dejavu')


def render(items, out_dir: Path) -> int:
    random.seed(SEED)
    serif = ImageFont.truetype(str(FONT_DIR / 'DejaVuSerif.ttf'), 26)
    serif_b = ImageFont.truetype(str(FONT_DIR / 'DejaVuSerif-Bold.ttf'), 30)
    mono = ImageFont.truetype(str(FONT_DIR / 'DejaVuSansMono.ttf'), 24)
    small = ImageFont.truetype(str(FONT_DIR / 'DejaVuSerif.ttf'), 18)
    out_dir.mkdir(parents=True, exist_ok=True)
    for it in items:
        W, H = 1240, 760
        img = Image.new('RGB', (W, H), (252, 251, 247))
        d = ImageDraw.Draw(img)
        if it['kind'] == 'contract':
            d.text((90, 70), 'MERCHANT SERVICES AGREEMENT', font=serif_b, fill=(30, 30, 30))
            d.text((90, 115), 'Schedule 2 — Term and Termination (extract)', font=small, fill=(80, 80, 80))
            d.line((90, 150, W - 90, 150), fill=(120, 120, 120), width=2)
            y = 200
            d.text((90, y), 'Clause 7.', font=serif_b, fill=(30, 30, 30)); y += 50
            for para in it['text'].split('\n'):
                for line in textwrap.wrap(para, width=70):
                    d.text((110, y), line, font=serif, fill=(20, 20, 20)); y += 40
                y += 14
            d.text((90, H - 80), 'Fictional document generated for a synthetic conformance study. Not a real agreement.',
                   font=small, fill=(110, 110, 110))
        else:
            d.text((90, 70), 'DISPUTE SUMMARY', font=serif_b, fill=(30, 30, 30))
            d.text((90, 115), 'Transaction service export (extract)', font=small, fill=(80, 80, 80))
            d.line((90, 150, W - 90, 150), fill=(120, 120, 120), width=2)
            y = 210
            for line in it['text'].split('\n'):
                d.text((110, y), line, font=mono, fill=(20, 20, 20)); y += 48
            d.text((90, H - 80), 'Fictional export generated for a synthetic conformance study. No real transactions.',
                   font=small, fill=(110, 110, 110))
        # scan-like degradation: slight rotation, blur, speckle noise (order and RNG draws are part of the fixture)
        img = img.rotate(random.uniform(-0.6, 0.6), resample=Image.BICUBIC, expand=False, fillcolor=(252, 251, 247))
        img = img.filter(ImageFilter.GaussianBlur(0.6))
        px = img.load()
        for _ in range(9000):
            x, y = random.randrange(W), random.randrange(H)
            v = random.randint(150, 230)
            px[x, y] = (v, v, v)
        img.save(out_dir / f"{it['doc_id']}.png")
    return len(items)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--docs', type=Path, default=Path('prompts/extraction_docs.jsonl'))
    ap.add_argument('--output', type=Path, default=Path('images'))
    args = ap.parse_args()
    items = [json.loads(line) for line in args.docs.read_text(encoding='utf-8').splitlines() if line.strip()]
    print(f'rendered {render(items, args.output)} images to {args.output}')


if __name__ == '__main__':
    main()
