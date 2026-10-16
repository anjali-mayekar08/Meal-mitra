"""Photo helper for beginners.   Run:  python photo_tool.py

1. Download your real photos (see README) and copy them into  static/images/incoming/
   Name each file after the photo it should become, e.g.  biryani.jpg, rice.png, hero.jpg, community.jpeg
2. Run this script. It resizes/crops each one, saves an optimised JPG in the right folder
   and prints a checklist of what is still missing.
"""
import os
import sys

from PIL import Image, ImageOps

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
sys.path.insert(0, BASE)
from services.photos import REQUIRED  # noqa: E402

INCOMING = os.path.join(STATIC, "images", "incoming")
SIZES = {"hero": (1600, 900), "community": (1200, 800)}  # everything else: 1200x800
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def target_for(stem):
    for rel in REQUIRED:
        if os.path.splitext(os.path.basename(rel))[0] == stem:
            return rel
    return None


def convert_incoming():
    os.makedirs(INCOMING, exist_ok=True)
    for name in sorted(os.listdir(INCOMING)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in EXTS:
            continue
        rel = target_for(stem.lower())
        if not rel:
            print(f"  skipped  {name}  (name must be one of: "
                  f"{', '.join(os.path.splitext(os.path.basename(r))[0] for r in REQUIRED)})")
            continue
        with Image.open(os.path.join(INCOMING, name)) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            size = SIZES.get(stem.lower(), (1200, 800))
            img = ImageOps.fit(img, size, Image.LANCZOS)      # centre-crop to the right shape
            dest = os.path.join(STATIC, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            img.save(dest, "JPEG", quality=85, optimize=True)
        print(f"  saved    {name}  ->  static/{rel}")


def report():
    print("\nPhoto checklist")
    missing = 0
    for rel, what in REQUIRED.items():
        ok = os.path.isfile(os.path.join(STATIC, rel))
        missing += not ok
        print(f"  [{'x' if ok else ' '}] static/{rel:<28} {what}")
    print(f"\n{len(REQUIRED) - missing}/{len(REQUIRED)} photos in place.")


if __name__ == "__main__":
    convert_incoming()
    report()
