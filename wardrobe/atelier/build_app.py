#!/usr/bin/env python3
"""Build the combined 'Your Wardrobe' app: top nav with two tabs —
Digital Wardrobe (moodboard of the women's demo wardrobe) and Atelier
(personal-stylist flow: intake wizard -> Style Profile -> mood -> weather ->
3 outfits). Offline 'sample stylist' works with no setup; a local Max bridge
upgrades it to real Opus. All state in localStorage.

WARDROBE_EMBED=1 inlines images as base64 -> single openable file.
"""
import json, os, base64, mimetypes

HERE = os.path.dirname(os.path.abspath(__file__))          # .../wardrobe/atelier
ROOT = os.path.dirname(HERE)                               # .../wardrobe
DEMO = os.path.join(HERE, "demo200")
raw = json.load(open(os.path.join(DEMO, "wardrobe_women.json")))
items = raw["items"]

EMBED = os.environ.get("WARDROBE_EMBED") == "1"
OUT = os.path.join(HERE, "atelier_app_standalone.html" if EMBED else "atelier_app.html")

# resolve an image file per item (jpg/webp/png), set image_file (relative or data-uri)
for it in items:
    found = None
    for ext in (".jpg", ".webp", ".png", ".jpeg"):
        p = os.path.join(DEMO, "images", it["id"] + ext)
        if os.path.exists(p) and os.path.getsize(p) > 1500:
            found = p; break
    if not found:
        it["image_file"] = None
        continue
    if EMBED:
        mime = mimetypes.guess_type(found)[0] or "image/jpeg"
        b64 = base64.b64encode(open(found, "rb").read()).decode()
        it["image_file"] = f"data:{mime};base64,{b64}"
    else:
        it["image_file"] = "demo200/images/" + os.path.basename(found)

CAT_ICON = {"tops": "👕", "bottoms": "👖", "shoes": "👟", "outerwear": "🧥",
            "knitwear": "🧶", "accessory": "👜", "dresses": "👗", "underwear": "🩲"}

# ---- colour-swatch placeholder tiles (so every item looks intentional even
#      when a real product photo couldn't be sourced) ----
import urllib.parse
COLOR_HEX = {
    "cream": "#F1E7D2", "white": "#FBFBF8", "black": "#222020", "grey": "#9C9892",
    "gray": "#9C9892", "navy": "#2B3653", "beige": "#D9C6A6", "tan": "#C7A06A",
    "denim": "#3E5C84", "indigo": "#33486E", "light blue": "#AFC8E2", "ecru": "#E8E0CE",
    "oatmeal": "#D8CCB6", "camel": "#C19A6B", "sand": "#D7C19A", "nude": "#E3C9B6",
    "khaki": "#8C8765", "silver": "#C7CBD0", "red": "#B23B3B", "gold": "#C9A227",
    "floral": "#C98BA8", "blue stripe": "#6E8FB8", "olive": "#6B6B3A", "brown": "#6B4A33",
}
EMOJI = {"tops": "👚", "bottoms": "👖", "shoes": "👠", "outerwear": "🧥",
         "knitwear": "🧶", "accessory": "👜", "dresses": "👗", "underwear": "🩲"}

def _hex_to_rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def _mix(h, other, t):
    a, b = _hex_to_rgb(h), _hex_to_rgb(other)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i]-a[i])*t) for i in range(3))
def _lum(h):
    r, g, b = _hex_to_rgb(h); return (0.299*r + 0.587*g + 0.114*b) / 255

def svg_tile(it):
    base = COLOR_HEX.get((it.get("color") or "").lower(), "#B9B4AC")
    bg = _mix(base, "#FFFFFF", 0.55)           # soft tint background
    swatch = base
    ink = "#1f1d1a" if _lum(bg) > 0.6 else "#ffffff"
    sub = _mix(ink, bg, 0.35)
    emoji = EMOJI.get(it["category"], "👗")
    name = (it.get("name_en") or it.get("name") or "").replace("&", "&amp;")
    brand = (it.get("brand") or "").replace("&", "&amp;")
    sw_stroke = "#00000022" if _lum(swatch) > 0.85 else "none"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 400">'
        f'<rect width="300" height="400" fill="{bg}"/>'
        f'<circle cx="150" cy="158" r="74" fill="{swatch}" stroke="{sw_stroke}" stroke-width="1.5"/>'
        f'<text x="150" y="180" font-size="64" text-anchor="middle">{emoji}</text>'
        f'<text x="150" y="300" font-family="Georgia,serif" font-size="15" fill="{ink}" '
        f'text-anchor="middle" font-weight="600">{brand}</text>'
        f'<text x="150" y="324" font-family="-apple-system,Helvetica,Arial" font-size="12.5" '
        f'fill="{sub}" text-anchor="middle">{name}</text>'
        f'<text x="150" y="364" font-family="-apple-system,Helvetica,Arial" font-size="10.5" '
        f'fill="{sub}" text-anchor="middle" letter-spacing="1.5">{(it.get("color") or "").upper()}</text>'
        f'</svg>'
    )
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)

for it in items:
    if not it.get("image_file"):
        it["image_file"] = svg_tile(it)
        it["placeholder"] = True


DOC = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your Wardrobe · Atelier</title>
<style>
:root{
  --bg:#F7F4ED; --surface:#FFFFFF; --surface-2:#F2EEE4; --text:#23211C; --muted:#6E6A60;
  --faint:#9A958A; --border:#E7E1D4; --border-strong:#D8D0BF; --accent:#C2603F; --accent-ink:#fff;
  --accent-soft:#F3E3DB; --returned:#B5791C; --returned-soft:#F6EBD5; --good:#3E7A52; --good-soft:#E4EFE6;
  --shadow:0 1px 2px rgba(40,30,15,.04),0 6px 22px rgba(40,30,15,.07); --radius:16px; --thumb:#FFFFFF;
  --serif:ui-serif,Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
html[data-theme="dark"]{
  --bg:#1B1A18; --surface:#262320; --surface-2:#2F2B26; --text:#ECE8E0; --muted:#A9A299; --faint:#7B756B;
  --border:#39342E; --border-strong:#48423a; --accent:#D97757; --accent-ink:#1B1A18; --accent-soft:#3A2A22;
  --returned:#E0A04B; --returned-soft:#352a18; --good:#7FB68F; --good-soft:#23302a;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 26px rgba(0,0,0,.38); --thumb:#F4F2EC;
}
*{box-sizing:border-box} html,body{margin:0}
body{background:var(--bg);color:var(--text);font-family:var(--sans);-webkit-font-smoothing:antialiased;line-height:1.45}
a{color:inherit} svg{width:1em;height:1em;display:block}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
.hidden{display:none!important}

/* top nav */
header{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--bg) 88%,transparent);
  backdrop-filter:saturate(140%) blur(10px);border-bottom:1px solid var(--border)}
.nav{display:flex;align-items:center;gap:22px;padding:16px 0}
.brandmark{font-family:var(--serif);font-size:22px;display:flex;align-items:center;gap:9px;white-space:nowrap}
.brandmark .dot{color:var(--accent)}
.navtabs{display:flex;gap:4px;margin-left:6px}
.navtab{appearance:none;border:0;background:none;font:inherit;cursor:pointer;color:var(--muted);font-size:15px;
  padding:8px 14px;border-radius:999px;transition:.15s}
.navtab:hover{color:var(--text)}
.navtab.active{background:var(--accent-soft);color:var(--accent);font-weight:600}
.nav-spacer{flex:1}
.icon-btn{appearance:none;border:1px solid var(--border-strong);background:var(--surface);color:var(--text);
  width:38px;height:38px;border-radius:10px;display:grid;place-items:center;cursor:pointer;transition:.15s}
.icon-btn:hover{border-color:var(--accent);color:var(--accent)}

/* ===== shared bits ===== */
.section-pad{padding:26px 0 80px}
.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint)}
h1.title{font-family:var(--serif);font-weight:500;font-size:30px;margin:6px 0 4px}
.lead{color:var(--muted);font-size:15px;max-width:60ch}
.btn{appearance:none;font:inherit;font-size:14px;cursor:pointer;border-radius:11px;padding:11px 18px;border:1px solid var(--border-strong);
  background:var(--surface);color:var(--text);transition:.14s;display:inline-flex;align-items:center;gap:8px;text-decoration:none}
.btn:hover{background:var(--surface-2)} .btn svg{width:16px;height:16px}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
.btn.primary:hover{filter:brightness(1.05)} .btn.ghost{background:none}
.btn:disabled{opacity:.5;cursor:not-allowed}

/* ===== wardrobe tab ===== */
.wb-head{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:14px}
.stats{display:flex;gap:20px;flex-wrap:wrap;color:var(--muted);font-size:13px}
.stats b{color:var(--text)}
.subtabs{display:flex;gap:4px;margin:6px 0 0}
.subtab{appearance:none;border:0;background:none;font:inherit;cursor:pointer;color:var(--muted);padding:8px 12px;
  border-bottom:2px solid transparent;font-size:14px;display:flex;gap:7px;align-items:center}
.subtab .count{background:var(--surface-2);border-radius:999px;font-size:11px;padding:1px 8px;font-weight:600}
.subtab.active{color:var(--text);border-bottom-color:var(--accent)}
.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:16px 0 4px}
.field{position:relative;display:flex;align-items:center}
.field svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--faint);width:16px;height:16px;pointer-events:none}
input[type=search],select{font:inherit;font-size:13.5px;color:var(--text);background:var(--surface);border:1px solid var(--border-strong);border-radius:10px;padding:9px 12px}
input[type=search]{padding-left:35px;min-width:220px}
.chips{display:flex;gap:7px;flex-wrap:wrap;padding:14px 0 20px}
.chip{cursor:pointer;user-select:none;padding:6px 13px;border-radius:999px;background:var(--surface);border:1px solid var(--border-strong);color:var(--muted);font-size:13px;transition:.14s;display:flex;gap:6px;align-items:center}
.chip:hover{border-color:var(--accent)} .chip.active{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.chip .n{opacity:.7;font-size:11px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(196px,1fr));gap:18px}
.card{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;aspect-ratio:3/4;box-shadow:var(--shadow);transition:transform .16s,box-shadow .16s,opacity .34s}
.card:hover{transform:translateY(-3px);box-shadow:0 2px 4px rgba(40,30,15,.06),0 14px 34px rgba(40,30,15,.12)}
.card.leaving{opacity:0;transform:scale(.94);pointer-events:none}
.photo{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:var(--thumb);cursor:pointer}
.photo img{width:100%;height:100%;object-fit:contain}
.photo .noimg{font-size:40px;opacity:.45}
.card.past .photo img{filter:grayscale(.55) opacity(.82)}
.cbtn{position:absolute;width:32px;height:32px;border-radius:50%;border:0;cursor:pointer;display:grid;place-items:center;font-size:15px;
  background:color-mix(in srgb,var(--surface) 82%,transparent);color:var(--text);backdrop-filter:blur(6px);box-shadow:0 1px 5px rgba(0,0,0,.16);transition:transform .14s,color .14s;opacity:.94;z-index:2}
.cbtn:hover{opacity:1;color:var(--accent);transform:scale(1.1)} .cbtn:active{transform:scale(1.16)}
.cbtn.tl{top:8px;left:8px}.cbtn.tr{top:8px;right:8px}.cbtn.br{bottom:8px;right:8px}
.cat-tag{position:absolute;bottom:8px;left:8px;font-size:11px;color:var(--muted);background:color-mix(in srgb,var(--surface) 84%,transparent);padding:3px 9px;border-radius:999px;backdrop-filter:blur(4px);opacity:0;transition:.15s}
.card:hover .cat-tag{opacity:1}
.past-foot{position:absolute;left:0;right:0;bottom:0;background:color-mix(in srgb,var(--surface) 88%,transparent);backdrop-filter:blur(6px);
  display:flex;align-items:center;justify-content:space-between;padding:8px 10px;font-size:11.5px;color:var(--muted)}
.past-foot .pill{background:var(--surface-2);border-radius:999px;padding:2px 8px;font-weight:600;color:var(--text)}
.empty{text-align:center;color:var(--muted);padding:70px 20px}
.empty .big{font-size:38px;opacity:.5;margin-bottom:10px}
.empty h3{margin:0 0 6px;font-family:var(--serif);font-weight:500;color:var(--text);font-size:20px}

/* ===== Atelier ===== */
.atelier{max-width:920px;margin:0 auto}
.center{max-width:680px;margin:0 auto;text-align:center}
.hero-emoji{font-size:46px}
.wizard{max-width:620px;margin:22px auto 0}
.progress{height:6px;background:var(--surface-2);border-radius:999px;overflow:hidden;margin-bottom:22px}
.progress > i{display:block;height:100%;background:var(--accent);border-radius:999px;transition:width .3s}
.q-eyebrow{font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);font-weight:600}
.q-title{font-family:var(--serif);font-weight:500;font-size:24px;margin:6px 0 4px}
.q-hint{color:var(--muted);font-size:13.5px;margin-bottom:18px}
.opts{display:grid;gap:10px}
.opt{appearance:none;text-align:left;font:inherit;font-size:15px;cursor:pointer;border:1.5px solid var(--border-strong);background:var(--surface);
  color:var(--text);border-radius:13px;padding:15px 16px;transition:.14s;display:flex;align-items:center;gap:12px}
.opt:hover{border-color:var(--accent);background:var(--surface-2)}
.opt.sel{border-color:var(--accent);background:var(--accent-soft)}
.opt .tick{width:20px;height:20px;border-radius:50%;border:1.5px solid var(--border-strong);flex:0 0 auto;display:grid;place-items:center;color:#fff}
.opt.sel .tick{background:var(--accent);border-color:var(--accent)}
.wizard-nav{display:flex;justify-content:space-between;align-items:center;margin-top:22px}
.wizard-nav .step{color:var(--faint);font-size:13px}

.moods{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin-top:8px}
.mood{appearance:none;text-align:left;font:inherit;cursor:pointer;border:1.5px solid var(--border-strong);background:var(--surface);
  color:var(--text);border-radius:16px;padding:18px;transition:.15s}
.mood:hover{border-color:var(--accent);transform:translateY(-2px);box-shadow:var(--shadow)}
.mood .emoji{font-size:26px}
.mood h3{margin:8px 0 4px;font-size:16px}
.mood p{margin:0;color:var(--muted);font-size:13px}

.weatherbar{display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid var(--border);border-radius:14px;
  padding:12px 16px;margin:14px 0 6px;font-size:14px}
.weatherbar .wx{font-size:24px}
.weatherbar .muted{color:var(--muted)}

.looks{display:grid;gap:18px;margin-top:10px}
.look{background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:18px;box-shadow:var(--shadow)}
.look-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.look-name{font-family:var(--serif);font-size:21px}
.look-pieces{display:flex;gap:12px;flex-wrap:wrap;margin:14px 0}
.piece{width:120px}
.piece .pimg{width:120px;height:150px;border-radius:12px;background:var(--thumb);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;overflow:hidden}
.piece .pimg img{width:100%;height:100%;object-fit:contain}
.piece .pimg .noimg{font-size:30px;opacity:.45}
.piece .pcap{font-size:11.5px;color:var(--muted);margin-top:5px;line-height:1.3}
.piece .pcap b{color:var(--text);font-weight:600;display:block}
.look-why{color:var(--text);font-size:14px;line-height:1.55;background:var(--surface-2);border-radius:11px;padding:11px 13px}
.look-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.tag{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;color:var(--muted);border:1px solid var(--border);border-radius:999px;padding:3px 10px}
.spin{width:18px;height:18px;border:2px solid var(--border-strong);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}

/* modal + toast (shared) */
.backdrop{position:fixed;inset:0;background:rgba(20,15,8,.46);backdrop-filter:blur(2px);z-index:60;display:none;align-items:center;justify-content:center;padding:20px}
.backdrop.open{display:flex;animation:fade .15s}@keyframes fade{from{opacity:0}to{opacity:1}}
.modal{background:var(--surface);border:1px solid var(--border-strong);border-radius:18px;max-width:440px;width:100%;padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.3);animation:rise .18s ease-out}
@keyframes rise{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}
.modal.detail{max-width:720px;padding:0;overflow:hidden}
.modal .mi{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;font-size:22px;margin-bottom:14px;background:var(--accent-soft);color:var(--accent)}
.modal h2{margin:0 0 8px;font-family:var(--serif);font-weight:500;font-size:20px}
.modal p{margin:0 0 18px;color:var(--muted);font-size:14px;line-height:1.5}.modal p b{color:var(--text)}
.modal .row{display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap}
.modal label.lbl{display:block;font-size:13px;color:var(--muted);margin:12px 0 6px}
.modal input[type=text]{width:100%;font:inherit;font-size:14px;padding:10px 12px;border:1px solid var(--border-strong);border-radius:10px;background:var(--surface);color:var(--text)}
.dt{display:grid;grid-template-columns:260px 1fr}
.dt-img{background:var(--thumb);display:grid;place-items:center;padding:18px;min-height:240px}.dt-img img{max-width:100%;max-height:380px;object-fit:contain}.dt-img .noimg{font-size:60px;opacity:.4}
.dt-info{padding:24px}.dt-close{position:absolute;top:14px;right:14px;width:32px;height:32px;border-radius:9px;border:1px solid var(--border);background:var(--surface);color:var(--muted);display:grid;place-items:center;cursor:pointer}
.dt-brand{color:var(--accent);font-weight:600;font-size:13.5px}.dt-name{font-family:var(--serif);font-size:21px;margin:2px 0 16px}
.dt-grid{display:grid;grid-template-columns:auto 1fr;gap:10px 18px;font-size:13.5px}.dt-grid dt{color:var(--muted)}.dt-grid dd{margin:0;font-weight:500;text-align:right}
@media(max-width:620px){.dt{grid-template-columns:1fr}}
.toasts{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);z-index:70;display:flex;flex-direction:column;gap:10px;align-items:center}
.toast{background:var(--text);color:var(--bg);border-radius:12px;padding:12px 16px;font-size:13.5px;display:flex;gap:14px;align-items:center;box-shadow:0 10px 30px rgba(0,0,0,.3);animation:rise .2s}
.toast button{border:0;background:none;color:var(--bg);font:inherit;font-weight:700;cursor:pointer;text-decoration:underline}
.toast.out{opacity:0;transform:translateY(8px);transition:.3s}
</style>
</head>
<body>
<header><div class="wrap"><div class="nav">
  <div class="brandmark"><span class="dot">●</span> Your Wardrobe</div>
  <div class="navtabs">
    <button class="navtab active" data-tab="wardrobe">Digital Wardrobe</button>
    <button class="navtab" data-tab="atelier">Atelier</button>
  </div>
  <div class="nav-spacer"></div>
  <button class="icon-btn" id="settingsBtn" title="Atelier settings" aria-label="Settings"></button>
  <button class="icon-btn" id="themeToggle" title="Toggle light / dark" aria-label="Theme"></button>
</div></div></header>

<!-- ===== WARDROBE TAB ===== -->
<main class="wrap section-pad" id="tab-wardrobe">
  <div class="wb-head">
    <div>
      <div class="eyebrow">Your closet</div>
      <h1 class="title">Digital Wardrobe</h1>
    </div>
    <div class="stats" id="wb-stats"></div>
  </div>
  <div class="subtabs">
    <button class="subtab active" data-view="active" id="wb-tabActive">In my closet <span class="count" id="wb-cActive">0</span></button>
    <button class="subtab" data-view="past" id="wb-tabPast">My bin <span class="count" id="wb-cPast">0</span></button>
  </div>
  <div class="controls">
    <div class="field"><span id="wb-searchIcon"></span><input type="search" id="wb-q" placeholder="Search…"></div>
    <select id="wb-brand"><option value="">All brands</option></select>
  </div>
  <div class="chips" id="wb-chips"></div>
  <div class="grid" id="wb-grid"></div>
  <div class="empty hidden" id="wb-empty"></div>
</main>

<!-- ===== ATELIER TAB ===== -->
<main class="wrap section-pad hidden" id="tab-atelier"><div class="atelier" id="atelier-root"></div></main>

<div class="backdrop" id="backdrop"><div class="modal" id="modal" role="dialog" aria-modal="true"></div></div>
<div class="toasts" id="toasts"></div>

<script>
const WARDROBE = %(data_json)s;
const CAT_ICON = %(cat_icon)s;
const CAT_LABEL = {tops:'Tops',bottoms:'Bottoms',shoes:'Shoes',outerwear:'Outerwear',knitwear:'Knitwear',accessory:'Accessories',dresses:'Dresses',underwear:'Underwear'};
const S = p=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;
const SVG={
  info:S('<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><circle cx="12" cy="7.6" r=".7" fill="currentColor" stroke="none"/>'),
  trash:S('<path d="M4 7h16"/><path d="M9.5 7V5.4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1V7"/><path d="M6.2 7l.9 12.1a1.6 1.6 0 0 0 1.6 1.4h6.6a1.6 1.6 0 0 0 1.6-1.4L17.8 7"/><path d="M10 11v6M14 11v6"/>'),
  ret:S('<path d="M6.5 8H20"/><path d="M16.5 4.5 20 8l-3.5 3.5"/><path d="M17.5 16H4"/><path d="M7.5 12.5 4 16l3.5 3.5"/>'),
  restore:S('<path d="M3.5 12a8.5 8.5 0 1 0 2.7-6.2"/><path d="M3 4.5v4h4"/>'),
  sun:S('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
  moon:S('<path d="M20.5 13.2A8.3 8.3 0 1 1 10.8 3.5 6.5 6.5 0 0 0 20.5 13.2z"/>'),
  gear:S('<circle cx="12" cy="12" r="3.2"/><path d="M19 12a7 7 0 0 0-.1-1.2l2-1.5-2-3.4-2.3 1a7 7 0 0 0-2-1.2l-.3-2.5H9.7l-.3 2.5a7 7 0 0 0-2 1.2l-2.3-1-2 3.4 2 1.5A7 7 0 0 0 5 12a7 7 0 0 0 .1 1.2l-2 1.5 2 3.4 2.3-1a7 7 0 0 0 2 1.2l.3 2.5h4.6l.3-2.5a7 7 0 0 0 2-1.2l2.3 1 2-3.4-2-1.5A7 7 0 0 0 19 12z"/>'),
  search:S('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>'),
  close:S('<path d="M6 6l12 12M18 6 6 18"/>'),
  check:S('<path d="M4 12.5l5 5L20 6"/>'),
  sparkle:S('<path d="M12 3l1.8 4.7L18.5 9l-4.7 1.8L12 15l-1.8-4.2L5.5 9l4.7-1.3L12 3z"/><path d="M19 14l.7 1.8L21.5 16l-1.8.7L19 18l-.7-1.3L16.5 16l1.8-.2L19 14z"/>'),
  refresh:S('<path d="M3 12a9 9 0 0 1 15.5-6.3M21 12a9 9 0 0 1-15.5 6.3"/><path d="M18 3v4h-4M6 21v-4h4"/>'),
  pin:S('<path d="M12 21s7-5.5 7-11a7 7 0 1 0-14 0c0 5.5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>'),
};
const gid=id=>document.getElementById(id);
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const cssEsc=s=>(window.CSS&&CSS.escape)?CSS.escape(s):s;

/* ---------- persistent state ---------- */
const LS='atelier.app.v1', LS_THEME='wardrobe.theme.v1';
let DB={items:{},profile:null,settings:{bridgeUrl:'',location:''},weatherCache:null};
try{DB=Object.assign(DB,JSON.parse(localStorage.getItem(LS)||'{}'));}catch(e){}
DB.items=DB.items||{}; DB.settings=DB.settings||{bridgeUrl:'',location:''};
const save=()=>{try{localStorage.setItem(LS,JSON.stringify(DB));}catch(e){}};
const istate=id=>DB.items[id]||(DB.items[id]={});
const isArchived=r=>!!(DB.items[r.id]&&DB.items[r.id].archived);
const byId=id=>WARDROBE.find(r=>r.id===id);
// items available to the stylist: not archived, not returned, not underwear
const stylable=()=>WARDROBE.filter(r=>!isArchived(r)&&!r.returned_order&&r.category!=='underwear');

/* ---------- theme ---------- */
function applyTheme(t){document.documentElement.setAttribute('data-theme',t);try{localStorage.setItem(LS_THEME,t);}catch(e){}
  gid('themeToggle').innerHTML=(t==='dark'?SVG.sun:SVG.moon);}
applyTheme((()=>{try{return localStorage.getItem(LS_THEME);}catch(e){return null}})()||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
gid('themeToggle').onclick=()=>applyTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark');
gid('settingsBtn').innerHTML=SVG.gear; gid('wb-searchIcon').innerHTML=SVG.search;

/* ---------- top nav ---------- */
let tab='wardrobe';
function setTab(t){tab=t;
  document.querySelectorAll('.navtab').forEach(b=>b.classList.toggle('active',b.dataset.tab===t));
  gid('tab-wardrobe').classList.toggle('hidden',t!=='wardrobe');
  gid('tab-atelier').classList.toggle('hidden',t!=='atelier');
  if(t==='wardrobe')renderWardrobe(); else renderAtelier();
}
document.querySelectorAll('.navtab').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));

/* ===================================================================== */
/*  DIGITAL WARDROBE TAB                                                  */
/* ===================================================================== */
let wbView='active', wbCat='';
function wbCard(r){
  const archived=isArchived(r),s=DB.items[r.id]||{};
  const img=r.image_file?`<img loading="lazy" src="${esc(r.image_file)}" alt="">`:`<div class="noimg">${CAT_ICON[r.category]||'👕'}</div>`;
  let icons=`<button class="cbtn tl" data-act="detail" title="Details">${SVG.info}</button>`;
  if(archived){icons+=`<button class="cbtn tr" data-act="restore" title="Restore">${SVG.restore}</button>`;}
  else{icons+=`<button class="cbtn tr" data-act="trash" title="Remove">${SVG.trash}</button>`;
    if(r.returned_order)icons+=`<button class="cbtn br" data-act="returnq" title="Did you return this?">${SVG.ret}</button>`;}
  let foot=archived?`<div class="past-foot"><span class="pill">${s.reason==='returned'?'Returned':'No longer owned'}</span>
    <button class="cbtn" style="position:static;width:auto;height:auto;padding:4px 8px;border-radius:8px" data-act="restore">${SVG.restore}</button></div>`:'';
  return `<div class="card ${archived?'past':''}" data-id="${esc(r.id)}">
    <div class="photo" data-act="detail">${img}</div>${icons}
    <span class="cat-tag">${CAT_ICON[r.category]||''} ${CAT_LABEL[r.category]||r.category}</span>${foot}</div>`;
}
function renderWardrobe(){
  const active=WARDROBE.filter(r=>!isArchived(r)), past=WARDROBE.filter(isArchived);
  gid('wb-cActive').textContent=active.length; gid('wb-cPast').textContent=past.length;
  gid('wb-tabActive').classList.toggle('active',wbView==='active');
  gid('wb-tabPast').classList.toggle('active',wbView==='past');
  // brand options
  const bsel=gid('wb-brand');
  if(bsel.options.length<=1){[...new Set(WARDROBE.map(r=>r.brand))].sort().forEach(b=>{const o=document.createElement('option');o.textContent=b;bsel.appendChild(o);});}
  // stats
  gid('wb-stats').innerHTML=`<span><b>${active.length}</b> pieces</span><span><b>${new Set(active.map(r=>r.brand)).size}</b> brands</span><span><b>${stylable().length}</b> stylable</span>`;
  // chips
  const counts={};active.forEach(r=>counts[r.category]=(counts[r.category]||0)+1);
  const cats=Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
  gid('wb-chips').innerHTML=`<span class="chip ${wbCat===''?'active':''}" data-cat="">All <span class="n">${active.length}</span></span>`+
    cats.map(c=>`<span class="chip ${wbCat===c?'active':''}" data-cat="${c}">${CAT_ICON[c]||''} ${CAT_LABEL[c]||c} <span class="n">${counts[c]}</span></span>`).join('');
  // grid
  const q=gid('wb-q').value.toLowerCase().trim(), b=gid('wb-brand').value;
  const list=(wbView==='active'?active:past).filter(r=>{
    if(wbCat&&r.category!==wbCat)return false;
    if(b&&r.brand!==b)return false;
    if(q){const h=(r.brand+' '+r.name+' '+(r.name_en||'')+' '+r.category).toLowerCase();if(!h.includes(q))return false;}
    return true;});
  gid('wb-grid').innerHTML=list.map(wbCard).join('');
  const e=gid('wb-empty');
  if(list.length){e.classList.add('hidden');}
  else{e.classList.remove('hidden');e.innerHTML=wbView==='past'
    ?`<div class="big">🗑️</div><h3>Your bin is empty</h3><div>Items you remove land here — restore anytime.</div>`
    :`<div class="big">🔍</div><h3>Nothing matches</h3>`;}
}
gid('wb-grid').addEventListener('click',e=>{
  const cardEl=e.target.closest('.card'); if(!cardEl)return; const id=cardEl.dataset.id;
  const a=e.target.closest('[data-act]'); if(!a)return;
  const act=a.dataset.act;
  if(act==='detail')wbDetail(id);
  else if(act==='trash')confirmModal({icon:SVG.trash,title:'Remove from your closet?',body:'We’ll move it to <b>My bin</b>. You can restore it anytime.',confirm:'Move to bin',onOk:()=>archiveItem(id,'no_longer_owned')});
  else if(act==='returnq')returnModal(id);
  else if(act==='restore')restoreItem(id);
});
['wb-q','wb-brand'].forEach(id=>gid(id).addEventListener('input',renderWardrobe));
gid('wb-chips').addEventListener('click',e=>{const c=e.target.closest('.chip');if(!c)return;wbCat=c.dataset.cat;renderWardrobe();});
gid('wb-tabActive').onclick=()=>{wbView='active';wbCat='';renderWardrobe();};
gid('wb-tabPast').onclick=()=>{wbView='past';wbCat='';renderWardrobe();};
function wbDetail(id){const r=byId(id);const m=gid('modal');m.className='modal detail';
  const img=r.image_file?`<img src="${esc(r.image_file)}">`:`<div class="noimg">${CAT_ICON[r.category]||'👗'}</div>`;
  const rows=[['Item',esc(r.name_en||r.name)],['Category',`${CAT_ICON[r.category]||''} ${CAT_LABEL[r.category]||r.category}`],['Colour',esc(r.color||'—')]];
  m.innerHTML=`<button class="dt-close" data-x>${SVG.close}</button><div class="dt"><div class="dt-img">${img}</div>
    <div class="dt-info"><div class="dt-brand">${esc(r.brand)}</div><div class="dt-name">${esc(r.name)}</div>
    <dl class="dt-grid">${rows.map(([k,v])=>`<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl></div></div>`;
  openBackdrop();}
function archiveItem(id,reason){const s=istate(id);s.archived=true;s.reason=reason;s.archivedAt=Date.now();delete s.kept;save();
  const c=document.querySelector(`#wb-grid .card[data-id="${cssEsc(id)}"]`);
  const done=()=>{renderWardrobe();toast('Moved to My bin','Undo',()=>{const x=DB.items[id];delete x.archived;delete x.reason;save();renderWardrobe();});};
  if(c){c.classList.add('leaving');setTimeout(done,360);}else done();}
function restoreItem(id){const s=DB.items[id]||{};delete s.archived;delete s.reason;delete s.archivedAt;save();renderWardrobe();toast('Back in your closet');}
function returnModal(id){confirmModal({icon:SVG.ret,title:'Did you return this item?',body:'If you sent it back, we’ll move it to your bin. If you kept it, we’ll clear the flag.',
  twoChoice:['I kept it','I returned it'],onChoice:(i)=>{ if(i===0){istate(id).kept=true; byId(id).returned_order=false; save(); renderWardrobe(); toast('Kept in your closet');} else archiveItem(id,'returned'); }});}

/* ===================================================================== */
/*  ATELIER TAB                                                          */
/* ===================================================================== */
const MOODS=[
  {key:'confident',emoji:'🔥',label:'Confident / Bold',desc:'Statement pieces, stronger colour, a sharper silhouette. Be seen.'},
  {key:'elegant',emoji:'🕊️',label:'Elegant / Polished',desc:'Refined, tailored, minimal. Cohesive and expensive-looking.'},
  {key:'effortless',emoji:'☕',label:'Effortless / Casual',desc:'Relaxed, comfortable, easy daytime. Good without trying.'},
  {key:'cozy',emoji:'🧸',label:'Cozy / Quiet',desc:'Soft, layered, low-key. Tonal and gentle, comfort first.'},
  {key:'playful',emoji:'🎈',label:'Playful / Fun',desc:'Colour, pattern, unexpected mixing. A little joy.'},
  {key:'sleek',emoji:'🌙',label:'Sleek / Night-out',desc:'Evening energy — more drama, more polish, going-out ready.'},
];
const INTAKE=[
  {sec:'Your days',key:'days',title:'Which best describes most of your days?',hint:'Pick one.',multi:false,opts:['Office / professional setting','Studying / campus','Working from home','On my feet / hands-on work','Caring for kids or family','Between things — it really varies']},
  {sec:'Your days',key:'dressUp',title:'How often do you dress up for evenings out or events?',hint:'Pick one.',multi:false,opts:['Several times a week','About once a week','A couple of times a month','Rarely — special occasions only']},
  {sec:'Your days',key:'dressCode',title:'Any dress code you have to respect?',hint:'Pick all that apply.',multi:true,opts:['Corporate / formal','Smart-casual expected','Casual, anything goes','A uniform or specific requirement','No rules at all']},
  {sec:'Fit & body',key:'feature',title:'When you feel great, what is an outfit usually doing for you?',hint:'Pick all that apply.',multi:true,opts:['Showing off my legs','Defining my waist','Highlighting my arms / shoulders','Flattering my neckline','Skimming comfortably, not clinging','Not sure — that’s why I’m here']},
  {sec:'Fit & body',key:'fits',title:'Which fits make you feel most like yourself?',hint:'Pick all that apply.',multi:true,opts:['Fitted and tailored','Loose and relaxed','A defined waist with flow below','Structured on top, easy on the bottom','A mix depending on the day']},
  {sec:'Fit & body',key:'skin',title:'How do you feel about showing skin?',hint:'Pick one.',multi:false,opts:['Love it — short, sleeveless, low-cut welcome','Selectively — one feature at a time','I prefer more covered','Depends entirely on the occasion']},
  {sec:'Taste',key:'colours',title:'Which colours do you gravitate to?',hint:'Pick all that apply.',multi:true,opts:['Neutrals — black, white, beige, grey, navy','Earthy — olive, rust, brown, cream','Soft pastels','Rich jewel tones','Bright, bold colour','Black, almost always']},
  {sec:'Taste',key:'prints',title:'How do you feel about prints and patterns?',hint:'Pick one.',multi:false,opts:['Love them — all of it','A little, as an accent','Mostly solids, the occasional print','Keep me in solids']},
  {sec:'Taste',key:'identity',title:'How do you want to come across?',hint:'Pick up to two.',multi:true,max:2,opts:['Polished and put-together','Effortless and cool','Soft and feminine','Edgy and bold','Classic and timeless','Creative and unexpected']},
  {sec:'Taste',key:'dressesSeparates',title:'Dresses or separates?',hint:'Pick one.',multi:false,opts:['Dresses whenever I can','Mostly separates','Equally happy with both']},
  {sec:'Practical',key:'effort',title:'How much energy do you want to spend getting dressed?',hint:'Pick one.',multi:false,opts:['Throw it on and go','A little thought, nothing fussy','I enjoy the ritual of putting a look together']},
  {sec:'Practical',key:'heels',title:'How do you feel about heels?',hint:'Pick one.',multi:false,opts:['Love them, wear them often','A low or block heel is my limit','Flats and sneakers, almost always','Depends on the occasion']},
  {sec:'Practical',key:'feel',title:'What do you most want to feel when you get dressed?',hint:'Pick up to two.',multi:true,max:2,opts:['Confident and powerful','Comfortable and at ease','Attractive and noticed','Calm and low-key','Creative and expressive']},
  {sec:'Practical',key:'noGos',title:'Anything that’s an automatic no?',hint:'Pick all that apply.',multi:true,opts:['Nothing too tight','Nothing too short','No bright colours','No fussy / high-maintenance fabrics','Nothing too revealing','No hard rules — surprise me']},
];

let atState={step:0,answers:{},mood:null};
function renderAtelier(){
  const root=gid('atelier-root');
  if(!DB.profile){ renderIntakeIntro(root); return; }
  renderToday(root);
}
function renderIntakeIntro(root){
  if(atState.step>0){ renderWizard(root); return; }
  root.innerHTML=`<div class="center" style="padding-top:18px">
    <div class="hero-emoji">✨</div>
    <div class="eyebrow" style="margin-top:8px">Atelier · your personal stylist</div>
    <h1 class="title">Let’s learn your style</h1>
    <p class="lead" style="margin:8px auto 22px">Fourteen quick taps and I’ll know how to dress you — your days, your fit, your taste, your no-gos. We only do this once.</p>
    <button class="btn primary" id="startIntake">${SVG.sparkle} Start</button>
  </div>`;
  gid('startIntake').onclick=()=>{atState.step=1;renderWizard(root);};
}
function renderWizard(root){
  const i=atState.step-1, q=INTAKE[i];
  const cur=atState.answers[q.key]|| (q.multi?[]:null);
  const pct=Math.round((i)/INTAKE.length*100);
  const optHtml=q.opts.map((o,idx)=>{
    const selected=q.multi?cur.includes(o):cur===o;
    return `<button class="opt ${selected?'sel':''}" data-o="${idx}">
      <span class="tick">${selected?SVG.check:''}</span><span>${esc(o)}</span></button>`;}).join('');
  root.innerHTML=`<div class="wizard">
    <div class="progress"><i style="width:${pct}%"></i></div>
    <div class="q-eyebrow">${esc(q.sec)} · ${i+1} of ${INTAKE.length}</div>
    <div class="q-title">${esc(q.title)}</div>
    <div class="q-hint">${esc(q.hint)}${q.max?` (max ${q.max})`:''}</div>
    <div class="opts" id="opts">${optHtml}</div>
    <div class="wizard-nav">
      <button class="btn ghost" id="backBtn" ${i===0?'disabled':''}>Back</button>
      <span class="step">${i+1} / ${INTAKE.length}</span>
      <button class="btn primary" id="nextBtn">${i===INTAKE.length-1?'Finish':'Next'}</button>
    </div></div>`;
  gid('opts').addEventListener('click',e=>{
    const b=e.target.closest('.opt'); if(!b)return; const o=q.opts[+b.dataset.o];
    if(q.multi){ let arr=atState.answers[q.key]||[]; if(arr.includes(o))arr=arr.filter(x=>x!==o);
      else{ if(q.max&&arr.length>=q.max)arr=arr.slice(1); arr=[...arr,o]; } atState.answers[q.key]=arr; renderWizard(root);
    } else { atState.answers[q.key]=o; // advance immediately on single-select
      setTimeout(()=>nextStep(root),120); }
  });
  gid('backBtn').onclick=()=>{ if(atState.step>1){atState.step--;renderWizard(root);} else {atState.step=0;renderAtelier();} };
  gid('nextBtn').onclick=()=>nextStep(root);
}
function nextStep(root){
  const q=INTAKE[atState.step-1];
  if(q.multi && (!atState.answers[q.key]||!atState.answers[q.key].length)){ toast('Tap at least one — or pick the closest.'); return; }
  if(!q.multi && !atState.answers[q.key]){ toast('Pick one to continue.'); return; }
  if(atState.step>=INTAKE.length){ DB.profile=atState.answers; save(); atState.step=0; toast('Style Profile saved ✨'); renderToday(root); return; }
  atState.step++; renderWizard(root);
}

/* ---------- today: mood -> weather -> outfits ---------- */
function renderToday(root){
  const moodCards=MOODS.map(m=>`<button class="mood" data-mood="${m.key}">
    <div class="emoji">${m.emoji}</div><h3>${m.label}</h3><p>${m.desc}</p></button>`).join('');
  root.innerHTML=`<div>
    <div class="wb-head"><div><div class="eyebrow">Atelier</div><h1 class="title">Outfit for today</h1>
      <p class="lead">How do you want to feel today? Pick a mood and I’ll style three looks from your closet for the weather outside.</p></div>
      <button class="btn ghost" id="editProfile">Edit style profile</button></div>
    <div class="moods" style="margin-top:14px">${moodCards}</div>
    <div id="today-result" style="margin-top:18px"></div></div>`;
  root.querySelectorAll('.mood').forEach(b=>b.onclick=()=>pickMood(b.dataset.mood));
  gid('editProfile').onclick=()=>{ atState.answers={...DB.profile}; atState.step=1; DB.profile=DB.profile; renderWizard(root); };
}
async function pickMood(mood){
  atState.mood=mood;
  const out=gid('today-result');
  out.innerHTML=`<div class="weatherbar"><span class="spin"></span><span class="muted">Checking today’s weather…</span></div>`;
  const wx=await getWeather();
  out.innerHTML=`<div class="weatherbar"><span class="wx">${wx.emoji}</span>
    <div><b>${esc(wx.summary)}</b> · ${wx.tempC}°C in ${esc(wx.place)}<div class="muted" style="font-size:12.5px">Styling for ${MOODS.find(m=>m.key===mood).label.toLowerCase()} · weather always wins on comfort</div></div></div>
    <div id="looks-wrap" style="margin-top:12px"><div class="weatherbar"><span class="spin"></span><span class="muted">Atelier is putting looks together…</span></div></div>`;
  let res;
  try{ res=await getOutfits(mood,wx); }
  catch(err){ res={intro:'',outfits:sampleOutfits(DB.profile,mood,wx),engine:'sample',error:String(err&&err.message||err)}; }
  renderLooks(gid('looks-wrap'),res,mood,wx);
}
function renderLooks(wrap,res,mood,wx){
  if(!res.outfits||!res.outfits.length){ wrap.innerHTML=`<div class="empty"><div class="big">🧺</div><h3>Not enough pieces yet</h3><div>Add more to your closet and I’ll style you.</div></div>`; return; }
  const badge=res.engine==='max-opus-text'?`<span class="tag">${SVG.sparkle} Styled by Atelier on Max</span>`
    :`<span class="tag">${SVG.sparkle} Sample stylist — connect Max in Settings for the real thing</span>`;
  const looks=res.outfits.map((o,idx)=>{
    const pieces=o.itemIds.map(id=>{const r=byId(id);if(!r)return'';
      const img=r.image_file?`<img src="${esc(r.image_file)}">`:`<div class="noimg">${CAT_ICON[r.category]||'👗'}</div>`;
      return `<div class="piece"><div class="pimg">${img}</div><div class="pcap"><b>${esc(r.brand)}</b>${esc(r.name_en||r.name)}</div></div>`;}).join('');
    return `<div class="look"><div class="look-head"><div class="look-name">${esc(o.name)}</div>
      <span class="tag">Look ${idx+1}</span></div>
      <div class="look-pieces">${pieces}</div>
      <div class="look-why">${esc(o.why)}</div>
      <div class="look-actions">
        <button class="btn ghost" data-refine="bolder" data-i="${idx}">Bolder</button>
        <button class="btn ghost" data-refine="cozier" data-i="${idx}">Cozier</button>
        <button class="btn ghost" data-refine="swap-shoes" data-i="${idx}">Swap shoes</button>
      </div></div>`;}).join('');
  wrap.innerHTML=`<div style="margin:2px 0 10px">${res.intro?`<p class="lead">${esc(res.intro)}</p>`:''}${badge}</div>
    <div class="looks">${looks}</div>
    <div style="margin-top:16px;text-align:center"><button class="btn" id="reroll">${SVG.refresh} Show me three more</button></div>`;
  gid('reroll').onclick=()=>pickMood(mood);
  wrap.querySelectorAll('[data-refine]').forEach(b=>b.onclick=()=>{ // re-run with a nudge (sample varies; bridge gets hint)
    pickMood(mood); });
}

/* ---------- weather (Open-Meteo + geolocation) ---------- */
const WCODE={0:['Clear','☀️'],1:['Mainly clear','🌤️'],2:['Partly cloudy','⛅'],3:['Overcast','☁️'],45:['Fog','🌫️'],48:['Fog','🌫️'],
 51:['Light drizzle','🌦️'],53:['Drizzle','🌦️'],55:['Drizzle','🌦️'],61:['Light rain','🌧️'],63:['Rain','🌧️'],65:['Heavy rain','🌧️'],
 71:['Light snow','🌨️'],73:['Snow','🌨️'],75:['Heavy snow','❄️'],77:['Snow','❄️'],80:['Showers','🌦️'],81:['Showers','🌧️'],82:['Heavy showers','🌧️'],
 85:['Snow showers','🌨️'],86:['Snow showers','❄️'],95:['Thunderstorm','⛈️'],96:['Thunderstorm','⛈️'],99:['Thunderstorm','⛈️']};
async function getWeather(){
  const today=new Date().toISOString().slice(0,10);
  if(DB.weatherCache&&DB.weatherCache.date===today&&!DB.settings.location){ return DB.weatherCache.wx; }
  let lat=52.23,lon=21.01,place='Warsaw';
  // explicit city override?
  if(DB.settings.location){ try{const g=await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(DB.settings.location)}&count=1`).then(r=>r.json());
    if(g.results&&g.results[0]){lat=g.results[0].latitude;lon=g.results[0].longitude;place=g.results[0].name;}}catch(e){} }
  else if(navigator.geolocation){ try{ const pos=await new Promise((res,rej)=>navigator.geolocation.getCurrentPosition(res,rej,{timeout:6000,maximumAge:6e5}));
    lat=pos.coords.latitude;lon=pos.coords.longitude;
    try{const rg=await fetch(`https://geocoding-api.open-meteo.com/v1/search?name=&latitude=${lat}&longitude=${lon}&count=1`).then(r=>r.json());}catch(e){}
    place='your location'; }catch(e){ /* denied -> Warsaw default */ } }
  let wx={tempC:14,condition:'Partly cloudy',emoji:'⛅',summary:'Partly cloudy',place};
  try{ const d=await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code,wind_speed_10m`).then(r=>r.json());
    const c=d.current; const wc=WCODE[c.weather_code]||['Mixed','🌥️'];
    wx={tempC:Math.round(c.temperature_2m),condition:wc[0],emoji:wc[1],summary:wc[0],windKph:Math.round(c.wind_speed_10m),place}; }catch(e){}
  DB.weatherCache={date:today,wx}; save();
  return wx;
}

/* ---------- engine: bridge (Max) or offline sample ---------- */
async function getOutfits(mood,wx){
  const url=DB.settings.bridgeUrl;
  if(url){ try{
    const ctrl=new AbortController(); const t=setTimeout(()=>ctrl.abort(),45000);
    const r=await fetch(url.replace(/\/$/,'')+'/atelier/outfits',{method:'POST',headers:{'Content-Type':'application/json'},signal:ctrl.signal,
      body:JSON.stringify({profile:DB.profile,mood,weather:wx,location:wx.place,wardrobe:stylable()})});
    clearTimeout(t);
    if(r.ok){const j=await r.json(); if(j.outfits&&j.outfits.length) return j; }
  }catch(e){ /* fall through to sample */ } }
  return {intro:'',outfits:sampleOutfits(DB.profile,mood,wx),engine:'sample'};
}

/* ---------- offline sample stylist (heuristic) ---------- */
const NEUTRAL=new Set(['black','white','cream','grey','gray','navy','beige','tan','denim','indigo','ecru','oatmeal','camel','sand','nude','khaki','light blue']);
function isNeutral(c){return NEUTRAL.has((c||'').toLowerCase());}
function isHeel(it){return /czó|heel|pump|obcas/i.test(it.name+' '+(it.name_en||''));}
function isSneaker(it){return /sneak|samba|trampki|veja|adidas/i.test(it.brand+' '+it.name+' '+(it.name_en||''));}
function isSandal(it){return /sanda|birken|japonki|klap/i.test(it.name+' '+(it.name_en||''));}
function isBoot(it){return /bot|boot|trzewik|kozak/i.test(it.name+' '+(it.name_en||''));}
const MOODCFG={
 confident:{form:[3,5],palette:'statement',hero:['dresses','outerwear','shoes']},
 elegant:{form:[3,5],palette:'tonal',hero:['outerwear','dresses','bottoms']},
 effortless:{form:[1,3],palette:'neutral',hero:['bottoms','tops','shoes']},
 cozy:{form:[1,3],palette:'tonal',hero:['knitwear','outerwear','bottoms']},
 playful:{form:[2,4],palette:'colour',hero:['dresses','tops','accessory']},
 sleek:{form:[3,5],palette:'dark',hero:['dresses','outerwear','shoes']},
};
function sampleOutfits(profile,mood,wx){
  profile=profile||{};
  const cfg=MOODCFG[mood]||MOODCFG.effortless;
  const cold=wx.tempC<12, chilly=wx.tempC<18, wet=/rain|snow|drizzle|shower|thunder/i.test(wx.condition||'');
  const flatsOnly=(profile.heels||'').startsWith('Flats');
  const noBright=(profile.noGos||[]).includes('No bright colours')||(profile.colours||[]).includes('Black, almost always');
  const covered=(profile.skin||'').startsWith('I prefer more covered')||(profile.noGos||[]).includes('Nothing too revealing');
  const items=stylable();
  const ofCat=c=>items.filter(i=>i.category===c);
  const colourOk=i=>!noBright||isNeutral(i.color);
  const seasonOk=i=> i.season==='all' || (cold? i.season==='cold' : !cold) || (!chilly? i.season!=='cold':true);
  const score=i=>{ let s=0; const [lo,hi]=cfg.form; if(i.formality>=lo&&i.formality<=hi)s+=2; if(isNeutral(i.color))s+= (cfg.palette==='neutral'||cfg.palette==='tonal'||cfg.palette==='dark')?1.2:0.2; if(!isNeutral(i.color)&&(cfg.palette==='colour'||cfg.palette==='statement'))s+=1.4; if(i.color==='black'&&cfg.palette==='dark')s+=1.2; if(cold&&i.season==='cold')s+=1; if(!cold&&i.season==='warm')s+=0.6; if(!colourOk(i))s-=4; return s; };
  const pick=(pool,used)=>{ const cand=pool.filter(i=>!used.has(i.id)&&colourOk(i)); if(!cand.length)return null; cand.sort((a,b)=>score(b)-score(a)+ (Math.random()-0.5)*0.6); return cand[0]; };
  const shoesPool=()=>ofCat('shoes').filter(s=>{ if(flatsOnly&&isHeel(s))return false; if(wet&&isSandal(s))return false; if(cold&&isSandal(s))return false; if(cold&&isSneaker(s)&&false)return false; return true; });
  const outerPool=()=>ofCat('outerwear');
  const accPool=()=>ofCat('accessory');
  const looksWanted=3;
  const wantsDresses=(profile.dressesSeparates||'').startsWith('Dresses');
  const strategies=[];
  // strategy ordering by mood + preference
  const dressFirst=wantsDresses||['playful','sleek','confident','elegant'].includes(mood);
  strategies.push(dressFirst?'dress':'separates','separates', dressFirst?'separates':'dress');
  const usedHeroes=new Set();
  const outfits=[];
  for(let n=0;n<looksWanted;n++){
    const used=new Set();
    let strat=strategies[n%strategies.length];
    const dresses=ofCat('dresses').filter(d=>!usedHeroes.has(d.id));
    if(strat==='dress'&&!dresses.length)strat='separates';
    const out=[];
    if(strat==='dress'){
      const d=pick(dresses,used)||pick(ofCat('dresses'),used); if(d){used.add(d.id);usedHeroes.add(d.id);out.push(d);}
    } else {
      const top = pick(ofCat('tops'),used) || pick(ofCat('knitwear'),used);
      const bottom = pick(ofCat('bottoms'),used);
      if(top){used.add(top.id);out.push(top);} if(bottom){used.add(bottom.id);usedHeroes.add(bottom.id);out.push(bottom);}
      // cozy/cold: add knit if top wasn't a knit
      if((cold||mood==='cozy')&&top&&top.category!=='knitwear'){const k=pick(ofCat('knitwear'),used);if(k){used.add(k.id);out.push(k);}}
    }
    // outerwear if cold/chilly/wet or elegant/confident wants a layer
    if(cold||wet||((chilly)&&['elegant','confident','sleek'].includes(mood))){ const o=pick(outerPool(),used); if(o){used.add(o.id);out.push(o);} }
    // shoes
    const sh=pick(shoesPool(),used)||pick(ofCat('shoes'),used); if(sh){used.add(sh.id);out.push(sh);}
    // accessory finish (1, or 2 if she enjoys the ritual)
    const wantTwo=(profile.effort||'').startsWith('I enjoy');
    const a1=pick(accPool(),used); if(a1){used.add(a1.id);out.push(a1);}
    if(wantTwo){const a2=pick(accPool(),used); if(a2){used.add(a2.id);out.push(a2);}}
    if(out.length>=3) outfits.push({name:lookName(mood,out,n),itemIds:out.map(i=>i.id),why:lookWhy(mood,out,wx,profile)});
  }
  return outfits.slice(0,3);
}
const NAMES={
 confident:['Bold Statement','Take the Room','Sharp & Sure'],
 elegant:['Quiet Luxury','Polished Hour','The Clean Line'],
 effortless:['Easy Does It','Off-Duty Ease','No-Effort Cool'],
 cozy:['Soft Landing','Quiet Comfort','Wrapped Up Right'],
 playful:['A Little Joy','Colour Play','Unexpected Mix'],
 sleek:['After Dark','Night Polish','City Lights'],
};
function lookName(mood,out,n){ const base=(NAMES[mood]||NAMES.effortless)[n%3]; return base; }
function lookWhy(mood,out,wx,profile){
  const hero=out[0]; const shoes=out.find(isShoe); const color=(hero.color||'').toLowerCase();
  const moodWord={confident:'commands attention',elegant:'reads quietly expensive',effortless:'looks easy and right',cozy:'feels soft and calm',playful:'brings a little joy',sleek:'turns on the evening polish'}[mood]||'works';
  const layer=out.find(i=>i.category==='outerwear');
  const bits=[];
  bits.push(`${hero.name_en||hero.name} leads and the look ${moodWord}.`);
  if(layer) bits.push(`${layer.name_en||layer.name} keeps you right for ${wx.tempC}°C.`);
  else bits.push(`Light enough for ${wx.tempC}°C and today’s ${(wx.condition||'weather').toLowerCase()}.`);
  if(shoes) bits.push(`${shoes.name_en||shoes.name} finish it off.`);
  return bits.join(' ');
}
function isShoe(i){return i.category==='shoes';}

/* ===================================================================== */
/*  shared modal / toast / settings                                      */
/* ===================================================================== */
function openBackdrop(){const bd=gid('backdrop');bd.classList.add('open');
  bd.onclick=ev=>{if(ev.target===bd)closeBackdrop();};
  document.onkeydown=ev=>{if(ev.key==='Escape')closeBackdrop();};
  const x=gid('modal').querySelector('[data-x]');if(x)x.onclick=closeBackdrop;}
function closeBackdrop(){gid('backdrop').classList.remove('open');gid('modal').className='modal';}
function confirmModal({icon,title,body,confirm,onOk,twoChoice,onChoice}){
  const m=gid('modal');m.className='modal';
  const btns= twoChoice
    ? `<button class="btn" data-c="0">${esc(twoChoice[0])}</button><button class="btn primary" data-c="1">${esc(twoChoice[1])}</button>`
    : `<button class="btn" data-x>Cancel</button><button class="btn primary" data-ok>${esc(confirm)}</button>`;
  m.innerHTML=`<div class="mi">${icon}</div><h2>${title}</h2><p>${body}</p><div class="row">${btns}</div>`;
  openBackdrop();
  if(twoChoice){ m.querySelectorAll('[data-c]').forEach(b=>b.onclick=()=>{closeBackdrop();onChoice&&onChoice(+b.dataset.c);}); }
  else { m.querySelector('[data-ok]').onclick=()=>{closeBackdrop();onOk&&onOk();}; }
}
function toast(msg,actionLabel,onAction){
  const wrap=gid('toasts'),t=document.createElement('div');t.className='toast';
  t.innerHTML=`<span>${msg}</span>`+(actionLabel?`<button>${actionLabel}</button>`:'');
  if(actionLabel)t.querySelector('button').onclick=()=>{onAction();dismiss();};
  wrap.appendChild(t);let killed=false;const dismiss=()=>{if(killed)return;killed=true;t.classList.add('out');setTimeout(()=>t.remove(),320);};
  setTimeout(dismiss,4500);
}
gid('settingsBtn').onclick=()=>{
  const m=gid('modal');m.className='modal';
  m.innerHTML=`<div class="mi">${SVG.gear}</div><h2>Atelier settings</h2>
    <p>Connect a local Atelier bridge to style with Claude on your Max plan. Leave blank to use the built-in sample stylist.</p>
    <label class="lbl">Local Atelier bridge URL</label>
    <input type="text" id="set-bridge" placeholder="http://localhost:8787" value="${esc(DB.settings.bridgeUrl||'')}">
    <label class="lbl">Weather city (optional — blank uses your location)</label>
    <input type="text" id="set-city" placeholder="Warsaw" value="${esc(DB.settings.location||'')}">
    <div class="row" style="margin-top:18px">
      <button class="btn" data-x>Close</button>
      <button class="btn ghost" id="set-reset">Reset profile</button>
      <button class="btn primary" id="set-save">Save</button></div>
    <div id="set-status" style="margin-top:10px;font-size:12.5px;color:var(--muted)"></div>`;
  openBackdrop();
  gid('set-save').onclick=async()=>{ DB.settings.bridgeUrl=gid('set-bridge').value.trim(); DB.settings.location=gid('set-city').value.trim(); DB.weatherCache=null; save();
    const st=gid('set-status');
    if(DB.settings.bridgeUrl){ st.innerHTML='Pinging bridge…';
      try{const h=await fetch(DB.settings.bridgeUrl.replace(/\/$/,'')+'/health').then(r=>r.json());
        st.innerHTML=h.ok?`✓ Connected — ${esc(h.model)}${h.usingApiKey?' ⚠ API key set (would bill API)':' · Max'}`:'Could not reach bridge.';}
      catch(e){ st.innerHTML='✗ Could not reach the bridge — using sample stylist.'; } }
    else st.innerHTML='Saved. Using the built-in sample stylist.';
    toast('Settings saved'); };
  gid('set-reset').onclick=()=>{ confirmModal({icon:SVG.refresh,title:'Reset your Style Profile?',body:'This clears your intake answers so you can redo them.',confirm:'Reset',onOk:()=>{DB.profile=null;atState={step:0,answers:{},mood:null};save();toast('Profile reset');setTab('atelier');}}); };
};

/* ---------- boot ---------- */
setTab('wardrobe');
</script>
</body>
</html>"""

out = DOC.replace("%(data_json)s", json.dumps(items, ensure_ascii=False))
out = out.replace("%(cat_icon)s", json.dumps(CAT_ICON, ensure_ascii=False))
open(OUT, "w").write(out)
print(f"Wrote {os.path.basename(OUT)} — {len(items)} items, {sum(1 for i in items if i['image_file'])} with photos")
