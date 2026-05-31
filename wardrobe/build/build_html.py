#!/usr/bin/env python3
"""Build the interactive wardrobe app from wardrobe.json.

UX: Claude-inspired warm light theme (+ dark toggle). Privacy-first cards —
the FRONT shows only the photo plus status & actions (reverse-searched marker,
'Possibly returned' with 'I returned it'/'I have it', and 'I no longer have it').
The PRIVATE purchase details (brand, product name, price, shop, size, date,
order #) live behind an (i) detail popup. Removals archive to 'Past items'
(reversible, with Undo). All state persists in the browser (localStorage).

EMBED mode (WARDROBE_EMBED=1) inlines every image as base64 -> single file.
"""
import json, os, base64, mimetypes

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(ROOT, "data", "wardrobe.json")))
data.sort(key=lambda r: (r.get("order_date") or "", r.get("id")), reverse=True)

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

CAT_ICON = {"tops": "👕", "bottoms": "👖", "shoes": "👟", "outerwear": "🧥",
            "knitwear": "🧶", "accessory": "🧢", "underwear": "🩲", "other": "🧺"}

DOC = r"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Your Wardrobe</title>
<style>
:root{
  --bg:#F7F4ED; --surface:#FFFFFF; --surface-2:#F2EEE4; --text:#23211C;
  --muted:#6E6A60; --faint:#9A958A; --border:#E7E1D4; --border-strong:#D8D0BF;
  --accent:#C2603F; --accent-ink:#fff; --accent-soft:#F3E3DB;
  --returned:#A9701A; --returned-soft:#F6EBD5;
  --good:#3E7A52; --good-soft:#E4EFE6;
  --shadow:0 1px 2px rgba(40,30,15,.04),0 6px 22px rgba(40,30,15,.07);
  --radius:16px; --thumb:#FFFFFF;
  --serif:ui-serif,Georgia,"Iowan Old Style","Times New Roman",serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
html[data-theme="dark"]{
  --bg:#1B1A18; --surface:#262320; --surface-2:#2F2B26; --text:#ECE8E0;
  --muted:#A9A299; --faint:#7B756B; --border:#39342E; --border-strong:#48423a;
  --accent:#D97757; --accent-ink:#1B1A18; --accent-soft:#3A2A22;
  --returned:#E0A04B; --returned-soft:#352a18;
  --good:#7FB68F; --good-soft:#23302a;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 26px rgba(0,0,0,.38); --thumb:#F4F2EC;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--bg);color:var(--text);font-family:var(--sans);-webkit-font-smoothing:antialiased;line-height:1.45}
a{color:inherit}
svg{width:1em;height:1em;display:block}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}

header{position:sticky;top:0;z-index:30;background:color-mix(in srgb,var(--bg) 86%,transparent);
  backdrop-filter:saturate(140%) blur(10px);border-bottom:1px solid var(--border)}
.head-top{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:22px 0 6px}
.brandmark{font-family:var(--serif);font-size:26px;letter-spacing:.2px;display:flex;align-items:center;gap:10px}
.brandmark .dot{color:var(--accent)}
.tagline{color:var(--muted);font-size:13px;margin-top:2px;font-style:italic}
.icon-btn{appearance:none;border:1px solid var(--border-strong);background:var(--surface);color:var(--text);
  width:38px;height:38px;border-radius:10px;font-size:18px;display:grid;place-items:center;cursor:pointer;transition:.15s}
.icon-btn:hover{border-color:var(--accent);color:var(--accent)}
.stats{display:flex;gap:22px;flex-wrap:wrap;color:var(--muted);font-size:13px;padding:2px 0 14px}
.stats b{color:var(--text);font-weight:600}
.tabs{display:flex;gap:4px}
.tab{appearance:none;border:0;background:none;font:inherit;cursor:pointer;color:var(--muted);padding:10px 14px;
  border-bottom:2px solid transparent;font-size:14px;display:flex;gap:8px;align-items:center}
.tab .count{background:var(--surface-2);color:var(--muted);border-radius:999px;font-size:11.5px;padding:1px 8px;font-weight:600}
.tab.active{color:var(--text);border-bottom-color:var(--accent)}
.tab.active .count{background:var(--accent-soft);color:var(--accent)}

.controls{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:18px 0 6px}
.field{position:relative;display:flex;align-items:center}
.field svg{position:absolute;left:11px;color:var(--faint);font-size:16px;pointer-events:none}
input[type=search],select{font:inherit;font-size:13.5px;color:var(--text);background:var(--surface);
  border:1px solid var(--border-strong);border-radius:10px;padding:9px 12px}
input[type=search]{padding-left:34px;min-width:230px}
select{cursor:pointer}
.toggle{display:flex;align-items:center;gap:8px;color:var(--muted);font-size:13px;cursor:pointer;user-select:none}
.switch{position:relative;width:38px;height:22px;background:var(--surface-2);border:1px solid var(--border-strong);border-radius:999px;transition:.18s}
.switch::after{content:"";position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:var(--faint);transition:.18s}
.toggle input{display:none}
.toggle input:checked + .switch{background:var(--accent-soft);border-color:var(--accent)}
.toggle input:checked + .switch::after{left:18px;background:var(--accent)}
.chips{display:flex;gap:7px;flex-wrap:wrap;padding:14px 0 22px}
.chip{cursor:pointer;user-select:none;padding:6px 13px;border-radius:999px;background:var(--surface);border:1px solid var(--border-strong);
  color:var(--muted);font-size:13px;transition:.14s;display:flex;gap:6px;align-items:center}
.chip:hover{border-color:var(--accent)}
.chip.active{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.chip .n{opacity:.7;font-size:11.5px}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:18px;padding-bottom:80px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;display:flex;
  flex-direction:column;box-shadow:var(--shadow);transition:transform .16s,box-shadow .16s,opacity .34s}
.card:hover{transform:translateY(-3px);box-shadow:0 2px 4px rgba(40,30,15,.06),0 14px 34px rgba(40,30,15,.12)}
.card.leaving{opacity:0;transform:scale(.94) translateY(6px);pointer-events:none}
.thumb{position:relative;aspect-ratio:3/4;background:var(--thumb)}
.thumb .photo{display:flex;width:100%;height:100%;align-items:center;justify-content:center;cursor:pointer}
.thumb img{width:100%;height:100%;object-fit:contain}
.thumb .noimg{font-size:46px;opacity:.5}
.card.past .thumb img{filter:grayscale(.55) opacity(.82)}
.info-btn{position:absolute;top:8px;right:8px;width:30px;height:30px;border-radius:50%;border:0;cursor:pointer;
  background:color-mix(in srgb,var(--surface) 80%,transparent);color:var(--text);display:grid;place-items:center;font-size:16px;
  backdrop-filter:blur(4px);box-shadow:0 1px 3px rgba(0,0,0,.12);transition:.15s}
.info-btn:hover{color:var(--accent);transform:scale(1.06)}
.rev-glyph{position:absolute;top:8px;left:8px;width:26px;height:26px;border-radius:8px;color:var(--returned);
  background:color-mix(in srgb,var(--surface) 82%,transparent);display:grid;place-items:center;font-size:15px;backdrop-filter:blur(4px);
  box-shadow:0 1px 3px rgba(0,0,0,.1)}

.body{padding:12px 13px 13px;display:flex;flex-direction:column;gap:10px;flex:1}
.srow{display:flex;flex-direction:column;gap:7px}
.sline{display:flex;align-items:center;gap:7px;font-size:12px;color:var(--muted)}
.sline svg{font-size:15px;flex:0 0 auto}
.srow.rev .sline svg{color:var(--returned)}
.srow.ret .sline svg{color:var(--accent)}
.sline .lab b{font-weight:600;color:var(--text)}
.info{position:relative;color:var(--faint);cursor:help;display:inline-flex;margin-left:auto}
.info svg{font-size:14px}
.info .tip{position:absolute;bottom:150%;right:-6px;width:215px;background:var(--text);color:var(--bg);font-size:11.5px;
  line-height:1.4;padding:9px 11px;border-radius:9px;opacity:0;visibility:hidden;transition:.14s;z-index:40;box-shadow:0 6px 20px rgba(0,0,0,.25)}
.info .tip::after{content:"";position:absolute;top:100%;right:10px;border:6px solid transparent;border-top-color:var(--text)}
.info:hover .tip{opacity:1;visibility:visible}
.ctas{display:flex;gap:7px}
.cta{appearance:none;font:inherit;font-size:12px;cursor:pointer;border-radius:8px;padding:6px 11px;border:1px solid var(--border-strong);
  background:var(--surface);color:var(--text);transition:.14s;flex:1}
.cta:hover{border-color:var(--accent)}
.cta.primary{background:var(--returned-soft);border-color:transparent;color:var(--returned);font-weight:600}
.cta.primary:hover{background:var(--returned);color:#fff}
.cta.ghost:hover{background:var(--good-soft);border-color:var(--good);color:var(--good)}
.hr{height:0;border-top:1px dashed var(--border-strong);margin:1px 0}
.nolonger{appearance:none;width:100%;background:none;border:0;font:inherit;font-size:12.5px;color:var(--muted);cursor:pointer;
  display:flex;align-items:center;gap:7px;justify-content:center;padding:5px;border-radius:8px;transition:.14s}
.nolonger:hover{color:var(--accent);background:var(--surface-2)}
.nolonger svg{font-size:15px}

.past-foot{display:flex;align-items:center;justify-content:space-between;gap:8px}
.reason{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--muted)}
.reason .pill{background:var(--surface-2);border-radius:999px;padding:2px 9px;font-weight:600;font-size:11px;color:var(--text)}
.restore{appearance:none;font:inherit;font-size:12px;cursor:pointer;border:1px solid var(--border-strong);background:var(--surface);
  color:var(--text);border-radius:8px;padding:6px 11px;display:flex;align-items:center;gap:6px;transition:.14s}
.restore:hover{border-color:var(--accent);color:var(--accent)}

.empty{text-align:center;color:var(--muted);padding:80px 20px}
.empty .big{font-size:40px;opacity:.5;margin-bottom:12px}
.empty h3{margin:0 0 6px;font-family:var(--serif);font-weight:500;color:var(--text);font-size:20px}
.legend{color:var(--faint);font-size:12px;padding:0 0 60px;display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.legend span{display:flex;align-items:center;gap:6px}

.backdrop{position:fixed;inset:0;background:rgba(20,15,8,.46);backdrop-filter:blur(2px);z-index:60;display:none;
  align-items:center;justify-content:center;padding:20px}
.backdrop.open{display:flex;animation:fade .15s}
@keyframes fade{from{opacity:0}to{opacity:1}}
.modal{background:var(--surface);border:1px solid var(--border-strong);border-radius:18px;max-width:404px;width:100%;
  padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.3);animation:rise .18s ease-out}
@keyframes rise{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}
.modal .mi{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;font-size:22px;margin-bottom:14px;background:var(--accent-soft);color:var(--accent)}
.modal h2{margin:0 0 8px;font-family:var(--serif);font-weight:500;font-size:20px}
.modal p{margin:0 0 20px;color:var(--muted);font-size:14px;line-height:1.5}
.modal p b{color:var(--text)}
.modal .row{display:flex;gap:10px;justify-content:flex-end}
.btn{appearance:none;font:inherit;font-size:14px;cursor:pointer;border-radius:10px;padding:10px 16px;border:1px solid var(--border-strong);
  background:var(--surface);color:var(--text);transition:.14s;display:inline-flex;align-items:center;gap:8px;text-decoration:none}
.btn:hover{background:var(--surface-2)}
.btn svg{font-size:16px}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
.btn.primary:hover{filter:brightness(1.05)}

/* detail popup (private info) */
.modal.detail{max-width:760px;padding:0;overflow:hidden}
.dt{display:grid;grid-template-columns:300px 1fr}
.dt-img{background:var(--thumb);display:grid;place-items:center;padding:18px;min-height:260px}
.dt-img img{max-width:100%;max-height:430px;object-fit:contain}
.dt-img .noimg{font-size:64px;opacity:.4}
.dt-info{padding:26px 26px 24px;position:relative}
.dt-close{position:absolute;top:14px;right:14px;width:32px;height:32px;border-radius:9px;border:1px solid var(--border);
  background:var(--surface);color:var(--muted);display:grid;place-items:center;cursor:pointer;font-size:16px}
.dt-close:hover{color:var(--accent);border-color:var(--accent)}
.dt-eyebrow{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin-bottom:12px;display:flex;align-items:center;gap:6px}
.dt-brand{color:var(--accent);font-weight:600;font-size:13.5px}
.dt-name{font-family:var(--serif);font-size:22px;line-height:1.25;margin:2px 0 18px}
.dt-grid{display:grid;grid-template-columns:auto 1fr;gap:11px 20px;margin:0 0 18px;font-size:13.5px}
.dt-grid dt{color:var(--muted)}
.dt-grid dd{margin:0;color:var(--text);font-weight:500;text-align:right}
.dt-grid dd.price{font-size:15px}
@media(max-width:620px){.dt{grid-template-columns:1fr}.dt-img{max-height:300px;min-height:0}}

.toasts{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);z-index:70;display:flex;flex-direction:column;gap:10px;align-items:center}
.toast{background:var(--text);color:var(--bg);border-radius:12px;padding:12px 14px 12px 16px;font-size:13.5px;display:flex;
  align-items:center;gap:14px;box-shadow:0 10px 30px rgba(0,0,0,.3);animation:rise .2s ease-out}
.toast button{appearance:none;border:0;background:none;color:var(--bg);font:inherit;font-weight:700;cursor:pointer;text-decoration:underline;text-underline-offset:2px}
.toast.out{opacity:0;transform:translateY(8px);transition:.3s}
@media(max-width:560px){.stats{gap:14px}}
</style>
</head>
<body>
<header><div class="wrap">
  <div class="head-top">
    <div>
      <div class="brandmark"><span class="dot">●</span> Your Wardrobe</div>
      <div class="tagline">your closet, quietly reconstructed from your inbox</div>
    </div>
    <button class="icon-btn" id="themeToggle" title="Toggle light / dark" aria-label="Toggle theme"></button>
  </div>
  <div class="stats" id="stats"></div>
  <div class="tabs">
    <button class="tab active" data-view="active" id="tabActive">My wardrobe <span class="count" id="cActive">0</span></button>
    <button class="tab" data-view="past" id="tabPast">Past items <span class="count" id="cPast">0</span></button>
  </div>
</div></header>

<main class="wrap">
  <div class="controls">
    <div class="field"><span id="searchIcon"></span><input type="search" id="q" placeholder="Search…"></div>
    <select id="brand"><option value="">All brands</option></select>
    <select id="year"><option value="">All years</option></select>
    <select id="retailer"><option value="">All shops</option><option>Zalando</option><option>Nike</option></select>
    <label class="toggle" id="hideRetWrap"><input type="checkbox" id="hideRet"><span class="switch"></span> Hide possibly-returned</label>
  </div>
  <div class="chips" id="chips"></div>
  <div class="grid" id="grid"></div>
  <div class="empty" id="empty" style="display:none"></div>
  <div class="legend" id="legend"></div>
</main>

<div class="backdrop" id="backdrop"><div class="modal" id="modal" role="dialog" aria-modal="true"></div></div>
<div class="toasts" id="toasts"></div>

<script>
const DATA = %(data_json)s;
const CAT_ICON = %(cat_icon)s;
const CAT_LABEL = {tops:'Tops',bottoms:'Bottoms',shoes:'Shoes',outerwear:'Outerwear',knitwear:'Knitwear',accessory:'Accessories',underwear:'Underwear',other:'Other'};
const S = p=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;
const SVG = {
  rev: S('<rect x="2.5" y="4.7" width="13" height="12.6" rx="2"/><circle cx="6.4" cy="8.4" r="1.05"/><path d="M3 14.4l3.2-3 2.6 2.4 1.9-1.7 2.8 2.6"/><circle cx="18.2" cy="6.2" r="3.5" fill="var(--surface)"/><path d="M18.2 4.7v2.1"/><circle cx="18.2" cy="8.7" r=".55" fill="currentColor" stroke="none"/>'),
  ret: S('<path d="M6.5 8H20"/><path d="M16.5 4.5 20 8l-3.5 3.5"/><path d="M17.5 16H4"/><path d="M7.5 12.5 4 16l3.5 3.5"/>'),
  archive: S('<rect x="3.5" y="4.2" width="17" height="4" rx="1"/><path d="M5.2 8.2v10.6a1 1 0 0 0 1 1h11.6a1 1 0 0 0 1-1V8.2"/><path d="M10 12h4"/>'),
  info: S('<circle cx="12" cy="12" r="9"/><path d="M12 11v5"/><circle cx="12" cy="7.6" r=".7" fill="currentColor" stroke="none"/>'),
  restore: S('<path d="M3.5 12a8.5 8.5 0 1 0 2.7-6.2"/><path d="M3 4.5v4h4"/>'),
  ext: S('<path d="M14 4h6v6"/><path d="M20 4l-8.5 8.5"/><path d="M19 13.5V19a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5.5"/>'),
  sun: S('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),
  moon: S('<path d="M20.5 13.2A8.3 8.3 0 1 1 10.8 3.5 6.5 6.5 0 0 0 20.5 13.2z"/>'),
  search: S('<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>'),
  close: S('<path d="M6 6l12 12M18 6 6 18"/>'),
};
const LS_STATE='wardrobe.state.v1', LS_THEME='wardrobe.theme.v1';
let state={}; try{state=JSON.parse(localStorage.getItem(LS_STATE)||'{}');}catch(e){}
const saveState=()=>{try{localStorage.setItem(LS_STATE,JSON.stringify(state));}catch(e){}};
const st=id=>state[id]||(state[id]={});
let view='active', cat='';
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const isArchived=r=>!!(state[r.id]&&state[r.id].archived);
const showRet=r=>{const s=state[r.id]||{};return r.returned_order&&!s.kept&&!s.archived;};
const byId=id=>DATA.find(r=>r.id===id);
const cssEsc=s=>(window.CSS&&CSS.escape)?CSS.escape(s):s.replace(/"/g,'\\"');

function applyTheme(t){document.documentElement.setAttribute('data-theme',t);try{localStorage.setItem(LS_THEME,t);}catch(e){}
  document.getElementById('themeToggle').innerHTML=(t==='dark'?SVG.sun:SVG.moon);}
applyTheme((()=>{try{return localStorage.getItem(LS_THEME);}catch(e){return null}})() || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
document.getElementById('themeToggle').onclick=()=>applyTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark');
document.getElementById('searchIcon').innerHTML=SVG.search;

/* CARD — photo + status/actions only (no private text) */
function card(r){
  const archived=isArchived(r), s=state[r.id]||{};
  const img=r.image_file?`<img loading="lazy" src="${esc(r.image_file)}" alt="">`:`<div class="noimg">${CAT_ICON[r.category]||'👕'}</div>`;
  const rev=(!archived&&r.image_origin==='reverse-search');
  let body='';
  if(archived){
    const label=s.reason==='returned'?'Returned to shop':'No longer owned';
    const when=s.archivedAt?new Date(s.archivedAt).toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'}):'';
    body=`<div class="past-foot"><span class="reason"><span class="pill">${label}</span>${when}</span>
      <button class="restore" data-act="restore">${SVG.restore} Restore</button></div>`;
  }else{
    let rows='';
    if(rev){
      rows+=`<div class="srow rev"><div class="sline">${SVG.rev}
        <span class="lab"><b>Reverse-searched</b> · photo may not be exact</span>
        <span class="info">${SVG.info}<span class="tip">Heads up: this photo was auto-found via reverse image search${r.image_credit?` (${esc(r.image_credit)})`:''} and may not be the exact item.</span></span>
      </div></div>`;
    }
    if(showRet(r)){
      rows+=`<div class="srow ret"><div class="sline">${SVG.ret}
        <span class="lab"><b>Possibly returned</b></span>
        <span class="info">${SVG.info}<span class="tip">This order included a return, so you may have sent this piece back. Let us know to keep your wardrobe accurate.</span></span>
      </div><div class="ctas">
        <button class="cta primary" data-act="returned">I returned it</button>
        <button class="cta ghost" data-act="keep">I have it</button>
      </div></div>`;
    }
    body=`${rows}${rows?'<div class="hr"></div>':''}
      <button class="nolonger" data-act="nolonger">${SVG.archive} I no longer have it</button>`;
  }
  return `<div class="card ${archived?'past':''}" data-id="${esc(r.id)}" ${rev?'data-rev="1"':''} ${(!archived&&showRet(r))?'data-ret="1"':''}>
    <div class="thumb">
      <div class="photo" data-act="detail">${img}</div>
      ${rev?`<span class="rev-glyph" title="Photo may be inexact">${SVG.rev}</span>`:''}
      <button class="info-btn" data-act="detail" aria-label="Details" title="Details">${SVG.info}</button>
    </div>
    <div class="body">${body}</div>
  </div>`;
}

/* DETAIL POPUP — the private purchase info */
function openDetail(id){
  const r=byId(id), s=state[id]||{}, archived=isArchived(r);
  const bd=document.getElementById('backdrop'), m=document.getElementById('modal');
  m.className='modal detail';
  const img=r.image_file?`<img src="${esc(r.image_file)}" alt="${esc(r.name)}">`:`<div class="noimg">${CAT_ICON[r.category]||'👕'}</div>`;
  const rows=[['Shop',esc(r.retailer)],['Price',r.price?`<span class="price">${esc(r.price)}</span>`:'—'],
    ['Size',esc(r.size)||'—'],['Ordered',esc(r.order_date)||'—'],
    ['Category',`${CAT_ICON[r.category]||''} ${CAT_LABEL[r.category]||r.category}`],['Order #',esc(r.order_no)||'—']];
  const grid=`<dl class="dt-grid">${rows.map(([k,v])=>`<dt>${k}</dt><dd${k==='Price'?' class="price"':''}>${v}</dd>`).join('')}</dl>`;
  const link=r.product_url?`<a class="btn" href="${esc(r.product_url)}" target="_blank" rel="noopener">${SVG.ext} Open product page</a>`:'';
  m.innerHTML=`<button class="dt-close" data-x>${SVG.close}</button>
    <div class="dt"><div class="dt-img">${img}</div>
    <div class="dt-info">
      <div class="dt-eyebrow">Purchase details</div>
      <div class="dt-brand">${esc(r.brand)||'Brand unknown'}</div>
      <div class="dt-name">${esc(r.name)}</div>
      ${grid}${link}
    </div></div>`;
  bd.classList.add('open');
  const close=()=>{bd.classList.remove('open');m.className='modal';};
  m.querySelector('[data-x]').onclick=close;
  bd.onclick=ev=>{if(ev.target===bd)close();};
  document.onkeydown=ev=>{if(ev.key==='Escape')close();};
}

/* init controls */
(function(){
  const brands=[...new Set(DATA.map(r=>r.brand).filter(Boolean))].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));
  const years=[...new Set(DATA.map(r=>r.year).filter(Boolean))].sort().reverse();
  document.getElementById('brand').insertAdjacentHTML('beforeend',brands.map(b=>`<option>${esc(b)}</option>`).join(''));
  document.getElementById('year').insertAdjacentHTML('beforeend',years.map(y=>`<option>${y}</option>`).join(''));
})();
function updateChips(active){
  const counts={};active.forEach(r=>counts[r.category]=(counts[r.category]||0)+1);
  const cats=Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
  document.getElementById('chips').innerHTML=
    `<span class="chip ${cat===''?'active':''}" data-cat="">All <span class="n">${active.length}</span></span>`+
    cats.map(c=>`<span class="chip ${cat===c?'active':''}" data-cat="${c}">${CAT_ICON[c]||''} ${CAT_LABEL[c]||c} <span class="n">${counts[c]}</span></span>`).join('');
}
function updateStats(active){
  const spend=active.reduce((a,r)=>a+(r.price_pln||0),0);
  const brands=new Set(active.map(r=>r.brand).filter(Boolean));
  const ds=active.map(r=>r.order_date).filter(Boolean).sort();
  const fmt=n=>Math.round(n).toLocaleString('fr-FR').replace(/ |,/g,' ');
  document.getElementById('stats').innerHTML=
    `<span><b id="shown">0</b> shown</span>`+
    `<span><b>${active.length}</b> items · <b>${active.filter(r=>r.image_file).length}</b> with photos</span>`+
    `<span>tracked value <b>${fmt(spend)} zł</b></span>`+
    (ds.length?`<span>${ds[0]} → ${ds[ds.length-1]}</span>`:'')+
    `<span><b>${brands.size}</b> brands</span>`;
}
function render(){
  const active=DATA.filter(r=>!isArchived(r)), past=DATA.filter(isArchived);
  document.getElementById('cActive').textContent=active.length;
  document.getElementById('cPast').textContent=past.length;
  document.getElementById('tabActive').classList.toggle('active',view==='active');
  document.getElementById('tabPast').classList.toggle('active',view==='past');
  document.getElementById('hideRetWrap').style.display=view==='active'?'':'none';
  updateStats(active); updateChips(active);
  const q=document.getElementById('q').value.toLowerCase().trim();
  const b=document.getElementById('brand').value,y=document.getElementById('year').value;
  const ret=document.getElementById('retailer').value,hideRet=document.getElementById('hideRet').checked;
  const list=(view==='active'?active:past).filter(r=>{
    if(cat&&r.category!==cat)return false;
    if(b&&r.brand!==b)return false;
    if(y&&r.year!==y)return false;
    if(ret&&r.retailer!==ret)return false;
    if(view==='active'&&hideRet&&showRet(r))return false;
    if(q){const h=(r.brand+' '+r.name+' '+r.category+' '+r.retailer).toLowerCase();if(!h.includes(q))return false;}
    return true;
  });
  document.getElementById('grid').innerHTML=list.map(card).join('');
  document.getElementById('shown').textContent=list.length;
  const e=document.getElementById('empty');
  if(list.length){e.style.display='none';}
  else{e.style.display='block';e.innerHTML=view==='past'
    ?`<div class="big">🧺</div><h3>No past items yet</h3><div>Anything you return or let go of lands here — and you can always bring it back.</div>`
    :`<div class="big">🔍</div><h3>Nothing matches</h3><div>Try clearing a filter or search term.</div>`;}
  document.getElementById('legend').innerHTML=
    `<span>${SVG.info} Tap for purchase details</span><span>${SVG.rev} Reverse-searched photo</span><span>${SVG.ret} Possibly returned</span>`;
}

/* interactions */
document.getElementById('grid').addEventListener('click',e=>{
  const cardEl=e.target.closest('.card'); if(!cardEl)return; const id=cardEl.dataset.id;
  const actEl=e.target.closest('[data-act]'); if(!actEl)return;
  const act=actEl.dataset.act;
  if(act==='detail'){openDetail(id);return;}
  if(act==='keep'){st(id).kept=true;saveState();leave(cardEl,render);toast(`Kept “${byId(id).name}” in your wardrobe`);return;}
  if(act==='returned'){confirmReturned(id);return;}
  if(act==='nolonger'){confirmNoLonger(id);return;}
  if(act==='restore'){restore(id);return;}
});
function leave(cardEl,cb){cardEl.classList.add('leaving');setTimeout(cb,360);}
function archive(id,reason){const s=st(id);s.archived=true;s.reason=reason;s.archivedAt=new Date().toISOString();delete s.kept;saveState();
  const c=document.querySelector(`.card[data-id="${cssEsc(id)}"]`),name=byId(id).name;
  const done=()=>{render();toast(`“${name}” moved to Past items`,'Undo',()=>unarchive(id));};
  c?leave(c,done):done();}
function unarchive(id){const s=state[id]||{};delete s.archived;delete s.reason;delete s.archivedAt;saveState();render();}
function restore(id){const name=byId(id).name,c=document.querySelector(`.card[data-id="${cssEsc(id)}"]`);
  const done=()=>{unarchive(id);toast(`“${name}” is back in your wardrobe`);};
  (c&&view==='past')?leave(c,done):(unarchive(id),toast(`“${name}” is back in your wardrobe`));}

function modal({icon,title,body,confirm,onConfirm}){
  const bd=document.getElementById('backdrop'),m=document.getElementById('modal');m.className='modal';
  m.innerHTML=`<div class="mi">${icon}</div><h2>${title}</h2><p>${body}</p>
    <div class="row"><button class="btn" data-x>Cancel</button><button class="btn primary" data-y>${confirm}</button></div>`;
  bd.classList.add('open');
  const close=()=>bd.classList.remove('open');
  m.querySelector('[data-x]').onclick=close;
  m.querySelector('[data-y]').onclick=()=>{close();onConfirm();};
  bd.onclick=ev=>{if(ev.target===bd)close();};
  document.onkeydown=ev=>{if(ev.key==='Escape')close();};
  m.querySelector('[data-y]').focus();
}
function confirmReturned(id){const r=byId(id);modal({icon:SVG.ret,title:'Mark as returned?',
  body:`We’ll move <b>this item</b> to your <b>Past items</b> as returned. You can restore it anytime.`,
  confirm:'Yes, I returned it',onConfirm:()=>archive(id,'returned')});}
function confirmNoLonger(id){modal({icon:SVG.archive,title:'Remove from your wardrobe?',
  body:`We’ll move <b>this item</b> to <b>Past items</b>. Sold it, gave it away, or wore it out — either way you can restore it anytime.`,
  confirm:'Move to Past items',onConfirm:()=>archive(id,'no_longer_owned')});}

function toast(msg,actionLabel,onAction){
  const wrap=document.getElementById('toasts'),t=document.createElement('div');t.className='toast';
  t.innerHTML=`<span>${msg}</span>`+(actionLabel?`<button>${actionLabel}</button>`:'');
  if(actionLabel)t.querySelector('button').onclick=()=>{onAction();dismiss();};
  wrap.appendChild(t);
  let killed=false;const dismiss=()=>{if(killed)return;killed=true;t.classList.add('out');setTimeout(()=>t.remove(),320);};
  setTimeout(dismiss,5000);
}

['q','brand','year','retailer','hideRet'].forEach(id=>document.getElementById(id).addEventListener('input',render));
document.getElementById('chips').addEventListener('click',e=>{const c=e.target.closest('.chip');if(!c)return;cat=c.dataset.cat;render();});
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{view=t.dataset.view;cat='';render();});
render();
</script>
</body>
</html>"""

out = DOC.replace("%(data_json)s", json.dumps(data, ensure_ascii=False))
out = out.replace("%(cat_icon)s", json.dumps(CAT_ICON, ensure_ascii=False))
open(os.path.join(ROOT, OUT_NAME), "w").write(out)
print(f"Wrote {OUT_NAME} — {len(data)} items")
