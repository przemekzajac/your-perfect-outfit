#!/usr/bin/env python3
"""Attach reverse-searched product images to the image-less Nike items and
record provenance on every catalog item."""
import json, re, os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, "images")
CAT = os.path.join(ROOT, "data", "wardrobe.json")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# name-pattern  ->  (image url, credit/source page)
NIKE_IMAGES = [
    (r"koszulka polo.*Slam",
     "https://www.e-tennis.com/media/catalog/product/cache/e3f192febd5085c1042f4a34b66cbefd/s/i/sinner-yannick.jpg",
     "e-tennis.com (DN1818-410)"),
    (r"spodenki tenisowe.*Slam",
     "https://www.tennisnuts.com/images/product/main/DN1825-410_A.jpg",
     "tennisnuts.com (DN1825-410)"),
    (r"skarpety.*Multiplier",
     "https://www.e-tennis.com/media/catalog/product/cache/e3f192febd5085c1042f4a34b66cbefd/n/i/nikecourt_multiplier_cushioned_tennis_crew_socks_2_pairs_-sk0118-100.jpg",
     "e-tennis.com (SK0118-100)"),
    (r"Libero",
     "https://www.tradeinn.com/f/13856/138569250/nike-f.c.-libero-dri-fit-short-sleeve-t-shirt.webp",
     "tradeinn.com (DQ5055)"),
    (r"Academy",
     "https://www.tradeinn.com/f/13856/138568781/nike-dri-fit-academy-knit-shorts.webp",
     "tradeinn.com"),
]

def fetch(url, dest_base):
    """Download url; choose extension from content-type. Returns image_file rel path or None."""
    head = subprocess.run(["curl", "-sSL", "-A", UA, "--max-time", "40", "-o", "/dev/null",
                           "-w", "%{content_type}", url], capture_output=True, text=True, timeout=60)
    ctype = (head.stdout or "").strip()
    ext = ".webp" if "webp" in ctype else ".png" if "png" in ctype else ".jpg"
    dest = dest_base + ext
    subprocess.run(["curl", "-sSL", "-A", UA, "--max-time", "40", "-o", dest, url],
                   capture_output=True, timeout=60)
    # validate magic bytes
    with open(dest, "rb") as f:
        sig = f.read(12)
    ok = sig[:2] == b"\xff\xd8" or sig[:8] == b"\x89PNG\r\n\x1a\n" or (sig[:4] == b"RIFF" and sig[8:12] == b"WEBP")
    if ok and os.path.getsize(dest) > 1500:
        return "images/" + os.path.basename(dest)
    if os.path.exists(dest):
        os.remove(dest)
    return None

data = json.load(open(CAT))
cache = {}
attached = 0
for rec in data:
    # provenance for everything
    if rec.get("image_origin") is None:
        rec["image_origin"] = "email" if rec.get("image_file") else None
    if rec["retailer"] != "Nike" or rec.get("image_file"):
        continue
    for pat, url, credit in NIKE_IMAGES:
        if re.search(pat, rec["name"], re.I):
            if url not in cache:
                cache[url] = fetch(url, os.path.join(IMG_DIR, rec["id"]))
            # If two items share a product, download once then copy per-id
            src = cache[url]
            if src:
                ext = os.path.splitext(src)[1]
                rel = "images/" + rec["id"] + ext
                dst = os.path.join(ROOT, rel)
                if not os.path.exists(dst):
                    subprocess.run(["cp", os.path.join(ROOT, src), dst])
                rec["image_file"] = rel
                rec["image_origin"] = "reverse-search"
                rec["image_credit"] = credit
                attached += 1
            break

json.dump(data, open(CAT, "w"), ensure_ascii=False, indent=2)
print(f"Attached {attached} Nike images")
print("Nike items now:")
for r in data:
    if r["retailer"] == "Nike":
        print(f"  {r['size']:>5}  {r['name'][:45]:45}  -> {r.get('image_file')}  [{r.get('image_credit','')}]")
