#!/usr/bin/env python3
"""Build a self-contained index.html wardrobe gallery from wardrobe.json."""
import json, os, html, datetime, base64, mimetypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "data", "wardrobe.json")))

# STANDALONE mode: inline every image as a base64 data URI so the single
# HTML file renders with no images/ folder. Triggered by env WARDROBE_EMBED=1.
EMBED = os.environ.get("WARDROBE_EMBED") == "1"
OUT_NAME = "wardrobe_standalone.html" if EMBED else "index.html"
if EMBED:
    for r in data:
        f = r.get("image_file")
        p = os.path.join(ROOT, f) if f else None
        if p and os.path.exists(p):
            mime = mimetypes.guess_type(p)[0] or "image/jpeg"
            b64 = base64.b64encode(open(p, "rb").read()).decode()
            r["image_file"] = f"data:{mime};base64,{b64}"

# sort newest first
data.sort(key=lambda r: (r.get("order_date") or "", r.get("id")), reverse=True)

total = len(data)
with_img = sum(1 for r in data if r.get("image_file"))
spend = sum(r["price_pln"] for r in data if r.get("price_pln"))
years = sorted({r["year"] for r in data if r.get("year")})
brands = sorted({r["brand"] for r in data if r.get("brand")}, key=str.lower)
cats = sorted({r["category"] for r in data if r.get("category")})
date_min = min((r["order_date"] for r in data if r.get("order_date")), default="")
date_max = max((r["order_date"] for r in data if r.get("order_date")), default="")

CAT_LABEL = {"tops": "Tops", "bottoms": "Bottoms", "shoes": "Shoes",
             "outerwear": "Outerwear", "knitwear": "Knitwear",
             "accessory": "Accessories", "underwear": "Underwear", "other": "Other"}
CAT_ICON = {"tops": "👕", "bottoms": "👖", "shoes": "👟", "outerwear": "🧥",
            "knitwear": "🧶", "accessory": "🧢", "underwear": "🩲", "other": "🧺"}

doc = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your Digital Wardrobe</title>
<style>
  :root {
    --bg:#0f1115; --card:#1a1d24; --card2:#21252e; --txt:#e8eaed; --muted:#9aa0aa;
    --accent:#6c8cff; --line:#2a2f3a; --returned:#e0a04b;
  }
  * { box-sizing:border-box; }
  body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         background:var(--bg); color:var(--txt); }
  header { padding:28px 24px 12px; border-bottom:1px solid var(--line);
           background:linear-gradient(180deg,#161922,#0f1115); position:sticky; top:0; z-index:10; }
  h1 { margin:0 0 6px; font-size:24px; letter-spacing:.3px; }
  h1 span { color:var(--accent); }
  .stats { color:var(--muted); font-size:13px; display:flex; gap:18px; flex-wrap:wrap; }
  .stats b { color:var(--txt); }
  .controls { display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-top:14px; }
  .controls input, .controls select {
    background:var(--card2); color:var(--txt); border:1px solid var(--line);
    border-radius:8px; padding:8px 10px; font-size:13px; }
  .controls input[type=search] { min-width:200px; }
  .chips { display:flex; gap:6px; flex-wrap:wrap; margin-top:12px; }
  .chip { cursor:pointer; user-select:none; padding:6px 12px; border-radius:999px;
          background:var(--card2); border:1px solid var(--line); color:var(--muted); font-size:13px; }
  .chip.active { background:var(--accent); color:#fff; border-color:var(--accent); }
  label.toggle { color:var(--muted); font-size:13px; display:flex; gap:6px; align-items:center; cursor:pointer; }
  main { padding:20px 24px 60px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:16px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden;
          display:flex; flex-direction:column; transition:transform .12s, border-color .12s; }
  .card:hover { transform:translateY(-3px); border-color:var(--accent); }
  .thumb { aspect-ratio:3/4; background:#fff; display:flex; align-items:center; justify-content:center; position:relative; }
  .thumb img { width:100%; height:100%; object-fit:contain; }
  .thumb .noimg { color:#888; font-size:42px; }
  .badge { position:absolute; top:8px; font-size:11px; padding:3px 8px; border-radius:999px; color:#fff; }
  .badge.cat { left:8px; background:rgba(0,0,0,.6); }
  .badge.ret { right:8px; background:var(--returned); color:#241a08; font-weight:600; }
  .badge.web { bottom:8px; left:8px; background:rgba(108,140,255,.92); font-size:10px; }
  .body { padding:10px 12px 12px; display:flex; flex-direction:column; gap:3px; }
  .brand { font-size:12px; color:var(--accent); font-weight:600; letter-spacing:.2px; }
  .name { font-size:13.5px; line-height:1.3; min-height:35px; }
  .meta { font-size:11.5px; color:var(--muted); display:flex; justify-content:space-between; margin-top:4px; }
  .price { color:var(--txt); font-weight:600; }
  a.card-link { text-decoration:none; color:inherit; }
  .empty { color:var(--muted); text-align:center; padding:60px; }
  footer { color:var(--muted); font-size:12px; padding:0 24px 40px; }
</style>
</head>
<body>
<header>
  <h1>👔 Your Digital <span>Wardrobe</span></h1>
  <div class="stats">
    <span><b id="shown">%(total)d</b> items shown</span>
    <span><b>%(total)d</b> total &middot; <b>%(with_img)d</b> with photos</span>
    <span>tracked spend <b>%(spend)s zł</b></span>
    <span>%(date_min)s &rarr; %(date_max)s</span>
    <span><b>%(nbrands)d</b> brands</span>
  </div>
  <div class="controls">
    <input type="search" id="q" placeholder="Search brand, item, colour…">
    <select id="brand"><option value="">All brands</option>%(brand_opts)s</select>
    <select id="year"><option value="">All years</option>%(year_opts)s</select>
    <select id="retailer"><option value="">All shops</option><option>Zalando</option><option>Nike</option></select>
    <label class="toggle"><input type="checkbox" id="hideRet"> Hide items from returned orders</label>
  </div>
  <div class="chips" id="catChips">
    <span class="chip active" data-cat="">All</span>%(cat_chips)s
  </div>
</header>
<main>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none">No items match these filters.</div>
</main>
<footer>
  Built from Gmail order confirmations (Zalando &amp; Nike), %(date_min)s–%(date_max)s.
  &ldquo;Returned&rdquo; is order-level: the order included at least one returned article, so some flagged items may still be owned.
  Nike items carry no packshot in their emails, so their photos were reverse-searched from retailer
  sites by product name (marked &ldquo;↗ web img&rdquo;); the exact colourway may differ.
</footer>
<script>
const DATA = %(data_json)s;
const CAT_ICON = %(cat_icon)s;
const grid = document.getElementById('grid');
const empty = document.getElementById('empty');
const shown = document.getElementById('shown');
let cat = "";
function esc(s){ return (s||"").replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }
function card(r){
  const img = r.image_file
    ? `<img loading="lazy" src="${esc(r.image_file)}" alt="${esc(r.name)}">`
    : `<div class="noimg">${CAT_ICON[r.category]||'👕'}</div>`;
  const ret = r.returned_order ? `<span class="badge ret" title="This order included a return">↩ returned?</span>` : "";
  const web = r.image_origin==='reverse-search' ? `<span class="badge web" title="Image reverse-searched from ${esc(r.image_credit||'the web')} — colourway may differ">↗ web img</span>` : "";
  const price = r.price ? `<span class="price">${esc(r.price)}</span>` : `<span class="price">—</span>`;
  const open = r.product_url ? ` href="${esc(r.product_url)}" target="_blank" rel="noopener"` : "";
  return `<a class="card-link"${open}><div class="card">
    <div class="thumb">${img}<span class="badge cat">${CAT_ICON[r.category]||''} ${esc(r.category)}</span>${ret}${web}</div>
    <div class="body">
      <div class="brand">${esc(r.brand)||'&nbsp;'}</div>
      <div class="name">${esc(r.name)}</div>
      <div class="meta"><span>${esc(r.size)?('size '+esc(r.size)):''}</span>${price}</div>
      <div class="meta"><span>${esc(r.retailer)}</span><span>${esc(r.order_date)}</span></div>
    </div></div></a>`;
}
function render(){
  const q = document.getElementById('q').value.toLowerCase().trim();
  const b = document.getElementById('brand').value;
  const y = document.getElementById('year').value;
  const ret = document.getElementById('retailer').value;
  const hideRet = document.getElementById('hideRet').checked;
  const out = DATA.filter(r=>{
    if(cat && r.category!==cat) return false;
    if(b && r.brand!==b) return false;
    if(y && r.year!==y) return false;
    if(ret && r.retailer!==ret) return false;
    if(hideRet && r.returned_order) return false;
    if(q){ const hay=(r.brand+' '+r.name+' '+r.category+' '+r.retailer).toLowerCase(); if(!hay.includes(q)) return false; }
    return true;
  });
  grid.innerHTML = out.map(card).join('');
  shown.textContent = out.length;
  empty.style.display = out.length? 'none':'block';
}
document.getElementById('catChips').addEventListener('click', e=>{
  if(!e.target.classList.contains('chip')) return;
  document.querySelectorAll('#catChips .chip').forEach(c=>c.classList.remove('active'));
  e.target.classList.add('active'); cat = e.target.dataset.cat; render();
});
['q','brand','year','retailer','hideRet'].forEach(id=>{
  document.getElementById(id).addEventListener('input', render);
});
render();
</script>
</body>
</html>"""

brand_opts = "".join(f"<option>{html.escape(b)}</option>" for b in brands)
year_opts = "".join(f"<option>{y}</option>" for y in reversed(years))
cat_counts = {}
for r in data:
    cat_counts[r["category"]] = cat_counts.get(r["category"], 0) + 1
cat_chips = "".join(
    f'<span class="chip" data-cat="{c}">{CAT_ICON.get(c,"")} {CAT_LABEL.get(c,c)} ({cat_counts[c]})</span>'
    for c in sorted(cats, key=lambda c: -cat_counts[c]))

repl = {
    "%(total)d": str(total), "%(with_img)d": str(with_img),
    "%(spend)s": f"{spend:,.0f}".replace(",", " "),
    "%(date_min)s": date_min, "%(date_max)s": date_max, "%(nbrands)d": str(len(brands)),
    "%(brand_opts)s": brand_opts, "%(year_opts)s": year_opts, "%(cat_chips)s": cat_chips,
    "%(data_json)s": json.dumps(data, ensure_ascii=False),
    "%(cat_icon)s": json.dumps(CAT_ICON, ensure_ascii=False),
}
out = doc
for k, v in repl.items():
    out = out.replace(k, v)
open(os.path.join(ROOT, OUT_NAME), "w").write(out)
print(f"Wrote {OUT_NAME} — {total} items, {with_img} photos, {len(brands)} brands, spend {spend:.0f} zł")
