#!/usr/bin/env python3
"""Static, NO-JAVASCRIPT gallery of the 200-item dataset — renders in any
viewer (incl. mobile in-app file previews). Embeds 256px thumbnails."""
import os, json, io, base64, urllib.parse
from PIL import Image, ImageOps
HERE=os.path.dirname(os.path.abspath(__file__)); DEMO=os.path.join(HERE,"demo200")
items=json.load(open(os.path.join(DEMO,"wardrobe_women.json")))["items"]
CAT_ICON={"tops":"👕","bottoms":"👖","shoes":"👟","outerwear":"🧥","knitwear":"🧶","accessory":"👜","dresses":"👗","underwear":"🩲"}
CAT_LABEL={"tops":"Tops","bottoms":"Bottoms","shoes":"Shoes","outerwear":"Outerwear","knitwear":"Knitwear","accessory":"Accessories","dresses":"Dresses","underwear":"Underwear"}
COLOR_HEX={"black":"#222","white":"#eee","grey":"#9a9a9a","charcoal":"#46484c","navy":"#26345a","blue":"#3c5fa5","light blue":"#aac8e2","denim":"#3e5c84","red":"#b23434","burgundy":"#70202e","pink":"#de96ac","blush":"#e8c8c8","green":"#487048","olive":"#70703e","khaki":"#968c64","beige":"#d6c6a8","cream":"#f0e8d4","brown":"#6e4c36","camel":"#c19a6b","tan":"#c8a070","yellow":"#deBe54","mustard":"#be9632","orange":"#d2823c","purple":"#70468c","lilac":"#c4b2d8","teal":"#287880","nude":"#e3c9b6"}
def thumb(iid):
    for ext in (".jpg",".webp",".png"):
        p=os.path.join(DEMO,"images",iid+ext)
        if os.path.exists(p):
            im=ImageOps.exif_transpose(Image.open(p)).convert("RGB"); im.thumbnail((256,256),Image.LANCZOS)
            b=io.BytesIO(); im.save(b,"JPEG",quality=72,optimize=True)
            return "data:image/jpeg;base64,"+base64.b64encode(b.getvalue()).decode()
    return None
def tile(it):
    c=COLOR_HEX.get(it["color"],"#bbb")
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 256"><rect width="200" height="256" fill="#f2eee4"/><circle cx="100" cy="110" r="52" fill="{c}"/><text x="100" y="124" font-size="42" text-anchor="middle">{CAT_ICON.get(it["category"],"👗")}</text></svg>'
    return "data:image/svg+xml;utf8,"+urllib.parse.quote(svg)
order=["dresses","tops","knitwear","bottoms","outerwear","shoes","accessory","underwear"]
items_by={c:[i for i in items if i["category"]==c] for c in order}
cards=[]
sections=[]
for c in order:
    its=items_by[c]
    if not its: continue
    cs=[]
    for it in its:
        src=thumb(it["id"]) or tile(it)
        ret='<span class="badge ret">↩ returned</span>' if it.get("returned_order") else ''
        cs.append(f'''<figure class="card">{ret}<img loading="lazy" src="{src}" alt="">
        <figcaption><b>{it["brand"]}</b>{it["name"]}<span class="meta">{it.get("color","")} · form {it.get("formality","?")} · {it.get("season","")} · {it.get("price","")}</span></figcaption></figure>''')
    sections.append(f'<h2>{CAT_ICON[c]} {CAT_LABEL[c]} <span class="n">{len(its)}</span></h2><div class="grid">{"".join(cs)}</div>')
html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Wardrobe findings — 200 items</title>
<style>
:root{{--bg:#F7F4ED;--surface:#fff;--text:#23211C;--muted:#6E6A60;--faint:#9A958A;--border:#E7E1D4;--accent:#C2603F;--serif:ui-serif,Georgia,"Times New Roman",serif}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.4}}
header{{padding:26px 20px 8px}}h1{{font-family:var(--serif);font-weight:500;font-size:26px;margin:0}}.sub{{color:var(--muted);font-size:14px;margin-top:6px}}
main{{padding:8px 16px 60px;max-width:1200px;margin:0 auto}}
h2{{font-family:var(--serif);font-weight:500;font-size:20px;margin:30px 0 12px;display:flex;align-items:center;gap:10px}}
h2 .n{{font-size:12px;color:var(--accent);background:#F3E3DB;border-radius:999px;padding:2px 9px;font-weight:600}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:14px}}
.card{{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:14px;overflow:hidden;box-shadow:0 1px 2px rgba(40,30,15,.04),0 6px 18px rgba(40,30,15,.06)}}
.card img{{width:100%;aspect-ratio:3/4;object-fit:contain;background:#fff;display:block}}
figcaption{{padding:9px 10px 11px;font-size:12px;color:var(--muted)}}figcaption b{{display:block;color:var(--accent);font-size:12px;font-weight:600}}
.card figcaption{{color:var(--text)}}.meta{{display:block;color:var(--faint);font-size:10.5px;margin-top:3px}}
.badge.ret{{position:absolute;top:8px;right:8px;background:#A9701A;color:#fff;font-size:10px;padding:3px 8px;border-radius:999px;z-index:1}}
</style></head><body>
<header><h1>👗 Wardrobe findings</h1><div class="sub">{len(items)} curated women's items · real photos + computed colours + synthesized metadata. This is a static gallery (no JavaScript) so it opens anywhere.</div></header>
<main>{"".join(sections)}</main></body></html>'''
out=os.path.join(HERE,"findings.html"); open(out,"w").write(html)
print("wrote findings.html:", round(len(html)/1e6,1),"MB,", len(items),"items")
