#!/usr/bin/env python3
"""
Parse Zalando / Nike order-confirmation emails (raw Gmail thread JSON) into a
structured wardrobe catalog, and download each product's packshot image.

Input : wardrobe/data/raw/<threadId>.json   (Gmail get_thread FULL_CONTENT)
Output: wardrobe/data/wardrobe.json
        wardrobe/images/<id>.jpg
"""
import json, re, os, sys, html, glob, subprocess, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # wardrobe/
RAW_DIR = os.path.join(ROOT, "data", "raw")
IMG_DIR = os.path.join(ROOT, "images")
OUT = os.path.join(ROOT, "data", "wardrobe.json")
os.makedirs(IMG_DIR, exist_ok=True)

# order numbers known to have been (at least partially) returned, from return emails
RETURNED_ORDERS = {
    "10913133187815", "10913130211188", "10904074393777", "10904074867412",
    "10904074236437", "10904071622750", "10904068902699", "10904069836185",
    "10904069752260", "10904065470453", "10904055085402", "10904054587602",
}
CANCELLED_ORDERS = {"10904066526519"}

# ---------- helpers ----------
def clean(s):
    if s is None:
        return ""
    s = html.unescape(s)
    for ch in (" ", "‌", "​", "﻿"):
        s = s.replace(ch, " " if ch == " " else "")
    return re.sub(r"\s+", " ", s).strip()

def unescape_url(u):
    return html.unescape(u).replace("&amp;", "&")

CATEGORY_RULES = [
    ("shoes",     r"(buty|sneaker|trampki|obuwie|p[oó]?[łl]but|botki|sanda[łl]|klapki|japonki|trzewiki|t[eę]nis[oó]wki|mokasyny|kozaki|adidasy|air\s|cortez|gazelle|samba|jordan)"),
    ("outerwear", r"(kurtka|p[łl]aszcz|parka|kamizelka|puchow|wiatr[oó]wka|jacket|coat|softshell)"),
    ("knitwear",  r"(sweter|sweterek|kardigan|golf|bluza|hoodie|sweatshirt)"),
    ("tops",      r"(koszulka|koszula|t[\s-]?shirt|tshirt|\btop\b|polo|podkoszul|bluzka|\btee\b|longsleeve)"),
    ("bottoms",   r"(spodnie|szorty|spodenki|jeansy|d[zż]insy|legginsy|chinos|joggery|trousers|shorts|sp[oó]dnic|bermud)"),
    ("accessory", r"(czapka|czapk|\bszal\b|szalik|r[eę]kawicz|pasek|portfel|torba|plecak|nerka|opaska|skarpet|okulary|zegarek|cap\b|beanie|\bbag\b|belt|duffel|m[uü]tze|gymsack|worek)"),
    ("underwear", r"(bokserki|majtki|biustonosz|stringi|\bfigi\b|\bpanty\b|brief)"),
]
def categorize(*texts):
    t = " ".join(x for x in texts if x).lower()
    for cat, pat in CATEGORY_RULES:
        if re.search(pat, t):
            return cat
    return "other"

def parse_sku_from_url(url):
    m = re.search(r"/(?:reco/)?([^/?]+?)\.html", url)
    if not m:
        return None, None
    seg = m.group(1)
    sku_m = re.search(r"-?([a-z0-9]{6,9}(?:-[a-z0-9]{2,4}){1,2})$", seg)
    sku = sku_m.group(1).upper() if sku_m else None
    if "/reco/" in url and not sku and re.fullmatch(r"[A-Za-z0-9-]{8,}", seg):
        sku = seg.upper()
    return seg, sku

def price_to_pln(s):
    m = re.search(r"([\d][\d\s.]*),(\d{2})", s.replace(" ", " "))
    if not m:
        m2 = re.search(r"([\d][\d\s.]*)\s*(?:z[łl]|ZŁ|PLN)", s)
        if m2:
            return float(re.sub(r"[^\d]", "", m2.group(1)))
        return None
    whole = re.sub(r"[^\d]", "", m.group(1))
    return float(f"{whole}.{m.group(2)}")

def download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return True
    try:
        subprocess.run(["curl", "-sS", "-L", "-A", "Mozilla/5.0", "--max-time", "40",
                        "-o", dest, url], capture_output=True, timeout=60)
        if os.path.exists(dest) and os.path.getsize(dest) > 1000:
            return True
    except Exception as e:
        sys.stderr.write(f"  dl error {url}: {e}\n")
    return False

# ---------- Zalando ----------
ZAL_IMG_ANCHOR = re.compile(
    r'<a\b[^>]*href="(?P<href>https://www\.zalando\.pl/[^"]*?cd084=img_item[^"]*)"[^>]*>\s*'
    r'<img\b[^>]*src="(?P<img>https://[^"]*ztat\.net/article/[^"]+)"',
    re.I | re.S)

def zal_html_items(htmlb):
    out = []
    for mm in ZAL_IMG_ANCHOR.finditer(htmlb):
        href = unescape_url(mm.group("href")).split("?")[0]
        img = unescape_url(mm.group("img"))
        img = re.sub(r"\?.*$", "", img) + "?imwidth=1200"
        slug, sku = parse_sku_from_url(href)
        out.append({"product_url": href, "image_url": img, "sku": sku})
    return out

PRICE_RE = re.compile(r"^\s*[\d][\d\s. ]*,\d{2}\s*(?:z[łl]|ZŁ|PLN)\s*$", re.I)
URLLINE_RE = re.compile(r"^\s*<?https?://")
SKIP_LINE = re.compile(r"^\s*(\[.*\]|Stw[oó]rz zestaw|Przesy[łl]ka|.*\bdostaw|>?\S*&\S*)\s*$", re.I)

def zal_text_items(text):
    raw = text.split("\n")
    lines = [clean(l) for l in raw]
    items = []
    n = len(lines)
    for i, l in enumerate(lines):
        m = re.match(r"Rozmiar:?\s*(.+)$", l)
        if not m:
            continue
        size = m.group(1).strip()
        # qty
        qty = 1
        for j in range(i + 1, min(i + 4, n)):
            qm = re.match(r"Ilo[sś][cć]:?\s*(\d+)", lines[j])
            if qm:
                qty = int(qm.group(1)); break
        # price (forward, first price-looking line)
        price = ""
        for j in range(i + 1, min(i + 8, n)):
            if PRICE_RE.match(raw[j].strip()) or PRICE_RE.match(lines[j]):
                price = lines[j]; break
        # name + brand: nearest two meaningful lines above Rozmiar
        prev = []
        sku = None
        for j in range(i - 1, max(i - 8, -1), -1):
            lj = lines[j]
            if not lj:
                continue
            if URLLINE_RE.match(raw[j].strip()) or "zalando.pl/" in lj or lj.endswith(">"):
                if sku is None:
                    s2, sk = parse_sku_from_url(unescape_url(raw[j]))
                    sku = sk
                continue
            if re.match(r"^\[", lj) or lj.lower().startswith("stw"):
                continue
            prev.append(lj)
            if len(prev) >= 2:
                break
        name = prev[0] if prev else ""
        brand = prev[1] if len(prev) > 1 else ""
        items.append({"brand": brand, "name": name, "size": size, "qty": qty,
                      "price": price, "sku": sku})
    return items

def order_meta(text):
    order_no = None
    m = re.search(r"Numer zam[oó]wienia[\s:]*\n?\s*<?\s*(\d{10,})", text)
    if not m:
        m = re.search(r"\b(109\d{11})\b", text)
    if m:
        order_no = m.group(1)
    return order_no

def parse_zalando(msg):
    htmlb = msg.get("htmlBody", "") or ""
    text = msg.get("plaintextBody", "") or ""
    order_no = order_meta(text)
    himg = zal_html_items(htmlb)
    titems = zal_text_items(text)
    items = []
    used = set()
    for idx, t in enumerate(titems):
        img = None
        # join by sku
        if t["sku"]:
            for k, h in enumerate(himg):
                if k in used: continue
                if h["sku"] and h["sku"] == t["sku"]:
                    img = h; used.add(k); break
        if img is None and idx < len(himg) and idx not in used:
            img = himg[idx]; used.add(idx)
        items.append({**t,
                      "image_url": (img or {}).get("image_url"),
                      "product_url": (img or {}).get("product_url"),
                      "sku": t["sku"] or (img or {}).get("sku")})
    return items, order_no

# ---------- Nike ----------
def parse_nike(msg):
    text = msg.get("plaintextBody", "") or ""
    subj = msg.get("subject", "")
    om = re.search(r"#(C\d{6,})", subj)
    order_no = om.group(1) if om else None
    lines = [clean(l) for l in text.split("\n")]
    items = []
    for i, l in enumerate(lines):
        sm = re.match(r"Rozmiar\s+(.+)$", l)
        if not sm:
            continue
        size = sm.group(1).strip()
        name = ""
        for j in range(i - 1, max(i - 4, -1), -1):
            if lines[j] and not lines[j].lower().startswith("rozmiar"):
                name = lines[j]; break
        if name:
            items.append({"brand": "Nike", "name": name, "size": size, "qty": 1,
                          "price": "", "sku": None, "image_url": None,
                          "product_url": None})
    return items, order_no

# ---------- main ----------
def main():
    catalog, seen = [], {}
    files = sorted(glob.glob(os.path.join(RAW_DIR, "*.json")))
    print(f"Found {len(files)} raw thread files")
    for f in files:
        tid = os.path.splitext(os.path.basename(f))[0]
        try:
            data = json.load(open(f))
        except Exception as e:
            print(f"  !! {tid}: bad json {e}"); continue
        for msg in data.get("messages", []):
            sender = msg.get("sender", "")
            date = (msg.get("date", "") or "")[:10]
            if "zalando" in sender:
                items, order_no = parse_zalando(msg)
                retailer = "Zalando"
            elif "nike" in sender:
                items, order_no = parse_nike(msg)
                retailer = "Nike"
            else:
                continue
            if not items or (order_no in CANCELLED_ORDERS):
                continue
            key = (retailer, order_no or msg.get("id"))
            if key in seen:
                continue
            seen[key] = True
            for idx, it in enumerate(items):
                cat = categorize(it.get("name"), it.get("brand"))
                catalog.append({
                    "id": f"{retailer.lower()}-{order_no or tid}-{idx}",
                    "retailer": retailer,
                    "order_no": order_no,
                    "order_date": date,
                    "year": date[:4],
                    "brand": it.get("brand", ""),
                    "name": it.get("name", ""),
                    "size": it.get("size", ""),
                    "qty": it.get("qty", 1),
                    "price": it.get("price", ""),
                    "price_pln": price_to_pln(it.get("price", "")),
                    "category": cat,
                    "sku": it.get("sku"),
                    "product_url": it.get("product_url"),
                    "image_url": it.get("image_url"),
                    "image_file": None,
                    "returned_order": (order_no in RETURNED_ORDERS),
                    "thread_id": tid,
                })
    print(f"Parsed {len(catalog)} items; downloading images...")
    ok = 0
    for rec in catalog:
        if not rec["image_url"]:
            continue
        fn = rec["id"] + ".jpg"
        dest = os.path.join(IMG_DIR, fn)
        if download(rec["image_url"], dest):
            rec["image_file"] = "images/" + fn; ok += 1
    print(f"Downloaded {ok} images")
    json.dump(catalog, open(OUT, "w"), ensure_ascii=False, indent=2)
    print(f"Wrote {OUT} ({len(catalog)} items)")

if __name__ == "__main__":
    main()
