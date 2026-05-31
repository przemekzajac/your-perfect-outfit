#!/usr/bin/env python3
"""Build the interactive wardrobe app from wardrobe.json.

Moodboard UX: cards are JUST the photo, with up to four corner icons —
  top-left  (i)        -> detail popup with private info (brand/name/price/shop…)
  top-right trash      -> confirm -> move to "My bin" (reversible)
  bottom-left caution  -> reverse-searched photo -> disclaimer popup
  bottom-right return  -> "Did you return this?" -> Returned (archive) / Kept (clear)
Claude-inspired warm light theme + dark toggle; archive to "My bin" with Undo +
Restore; all state persists in the browser (localStorage).
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
<title>Your Awesome Digital Wardrobe</title>
<style>
:root{
  --bg:#F7F4ED; --surface:#FFFFFF; --surface-2:#F2EEE4; --text:#23211C;
  --muted:#6E6A60; --faint:#9A958A; --border:#E7E1D4; --border-strong:#D8D0BF;
  --accent:#C2603F; --accent-ink:#fff; --accent-soft:#F3E3DB;
  --returned:#B5791C; --returned-soft:#F6EBD5;
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
.head-top{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:22px 0 8px}
.brandmark{font-family:var(--serif);font-size:26px;letter-spacing:.2px;display:flex;align-items:center;gap:10px}
.brandmark .dot{color:var(--accent)}
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
.field svg{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--faint);width:16px;height:16px;pointer-events:none}
input[type=search],select{font:inherit;font-size:13.5px;color:var(--text);background:var(--surface);
  border:1px solid var(--border-strong);border-radius:10px;padding:9px 12px}
input[type=search]{padding-left:35px;min-width:230px}
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
.card{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;
  aspect-ratio:3/4;box-shadow:var(--shadow);transition:transform .16s,box-shadow .16s,opacity .34s}
.card:hover{transform:translateY(-3px);box-shadow:0 2px 4px rgba(40,30,15,.06),0 14px 34px rgba(40,30,15,.12)}
.card.leaving{opacity:0;transform:scale(.94) translateY(6px);pointer-events:none}
.photo{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;background:var(--thumb);cursor:pointer}
.photo img{width:100%;height:100%;object-fit:contain}
.photo .noimg{font-size:46px;opacity:.5}
.card.past .photo img{filter:grayscale(.55) opacity(.82)}

.cbtn{position:absolute;width:33px;height:33px;border-radius:50%;border:0;cursor:pointer;display:grid;place-items:center;
  font-size:16px;background:color-mix(in srgb,var(--surface) 82%,transparent);color:var(--text);backdrop-filter:blur(6px);
  box-shadow:0 1px 5px rgba(0,0,0,.16);transition:transform .14s ease,color .14s,opacity .14s;opacity:.94;z-index:2}
.cbtn:hover{opacity:1;color:var(--accent);transform:scale(1.1)}
.cbtn:active{transform:scale(1.16)}
.cbtn.tl{top:9px;left:9px}.cbtn.tr{top:9px;right:9px}.cbtn.bl{bottom:9px;left:9px}.cbtn.br{bottom:9px;right:9px}

.empty{text-align:center;color:var(--muted);padding:80px 20px}
.empty .big{font-size:40px;opacity:.5;margin-bottom:12px}
.empty h3{margin:0 0 6px;font-family:var(--serif);font-weight:500;color:var(--text);font-size:20px}
.legend{color:var(--faint);font-size:12px;padding:0 0 60px;display:flex;gap:18px;flex-wrap:wrap;align-items:center}
.legend span{display:flex;align-items:center;gap:6px}
.legend svg{width:15px;height:15px}

.backdrop{position:fixed;inset:0;background:rgba(20,15,8,.46);backdrop-filter:blur(2px);z-index:60;display:none;
  align-items:center;justify-content:center;padding:20px}
.backdrop.open{display:flex;animation:fade .15s}
@keyframes fade{from{opacity:0}to{opacity:1}}
.modal{background:var(--surface);border:1px solid var(--border-strong);border-radius:18px;max-width:412px;width:100%;
  padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.3);animation:rise .18s ease-out}
@keyframes rise{from{opacity:0;transform:translateY(10px) scale(.98)}to{opacity:1;transform:none}}
.modal .mi{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;font-size:22px;margin-bottom:14px;background:var(--accent-soft);color:var(--accent)}
.modal .mi.warn{background:var(--returned-soft);color:var(--returned)}
.modal h2{margin:0 0 8px;font-family:var(--serif);font-weight:500;font-size:20px}
.modal p{margin:0 0 20px;color:var(--muted);font-size:14px;line-height:1.5}
.modal p b{color:var(--text)}
.modal .row{display:flex;gap:10px;justify-content:flex-end;flex-wrap:wrap}
.btn{appearance:none;font:inherit;font-size:14px;cursor:pointer;border-radius:10px;padding:10px 16px;border:1px solid var(--border-strong);
  background:var(--surface);color:var(--text);transition:.14s;display:inline-flex;align-items:center;gap:8px;text-decoration:none}
.btn:hover{background:var(--surface-2)}
.btn svg{width:16px;height:16px}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:600}
.btn.primary:hover{filter:brightness(1.05)}
.btn.warn{background:var(--returned);border-color:var(--returned);color:#fff;font-weight:600}
.btn.warn:hover{filter:brightness(1.05)}

.modal.detail{max-width:760px;padding:0;overflow:hidden}
.dt{display:grid;grid-template-columns:300px 1fr}
.dt-img{background:var(--thumb);display:grid;place-items:center;padding:18px;min-height:260px}
.dt-img img{max-width:100%;max-height:430px;object-fit:contain}
.dt-img .noimg{font-size:64px;opacity:.4}
.dt-info{padding:26px 26px 24px;position:relative}
.dt-close{position:absolute;top:14px;right:14px;width:32px;height:32px;border-radius:9px;border:1px solid var(--border);
  background:var(--surface);color:var(--muted);display:grid;place-items:center;cursor:pointer}
.dt-close:hover{color:var(--accent);border-color:var(--accent)}
.dt-eyebrow{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin-bottom:12px}
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
    <div class="brandmark"><span class="dot">●</span> Your Awesome Digital Wardrobe</div>
    <button class="icon-btn" id="themeToggle" title="Toggle light / dark" aria-label="Toggle theme"></button>
  </div>
  <div class="stats" id="stats"></div>
  <div class="tabs">
    <button class="tab active" data-view="active" id="tabActive">My wardrobe <span class="count" id="cActive">0</span></button>
    <button class="tab" data-view="past" id="tabPast">My bin <span class="count" id="cPast">0</span></button>
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
const CAT_LABEL = {tops:'Tops',bottoms:'Bottoms',shoes:'Shoes',outerwear:'Outerwear',knitwear:'Sweaters & Hoodies',accessory:'Accessories',underwear:'Underwear',other:'Other'};
const S = p=>`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${p}</svg>`;
const SVG = {
  rev: S('<rect x="2.5" y="4.7" width="13" height="12.6" rx="2"/><circle cx="6.4" cy="8.4" r="1.05"/><path d="M3 14.4l3.2-3 2.6 2.4 1.9-1.7 2.8 2.6"/><circle cx="18.2" cy="6.2" r="3.5" fill="var(--surface)"/><path d="M18.2 4.7v2.1"/><circle cx="18.2" cy="8.7" r=".55" fill="currentColor" stroke="none"/>'),
  ret: S('<path d="M6.5 8H20"/><path d="M16.5 4.5 20 8l-3.5 3.5"/><path d="M17.5 16H4"/><path d="M7.5 12.5 4 16l3.5 3.5"/>'),
  trash: S('<path d="M4 7h16"/><path d="M9.5 7V5.4a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1V7"/><path d="M6.2 7l.9 12.1a1.6 1.6 0 0 0 1.6 1.4h6.6a1.6 1.6 0 0 0 1.6-1.4L17.8 7"/><path d="M10 11v6M14 11v6"/>'),
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
const gid=id=>document.getElementById(id);
let view='active', cat='';
const esc=s=>(s||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const isArchived=r=>!!(state[r.id]&&state[r.id].archived);
const showRet=r=>{const s=state[r.id]||{};return r.returned_order&&!s.kept&&!s.archived;};
const byId=id=>DATA.find(r=>r.id===id);
const cssEsc=s=>(window.CSS&&CSS.escape)?CSS.escape(s):s.replace(/"/g,'\\"');

function applyTheme(t){document.documentElement.setAttribute('data-theme',t);try{localStorage.setItem(LS_THEME,t);}catch(e){}
  gid('themeToggle').innerHTML=(t==='dark'?SVG.sun:SVG.moon);}
applyTheme((()=>{try{return localStorage.getItem(LS_THEME);}catch(e){return null}})() || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'));
gid('themeToggle').onclick=()=>applyTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark');
gid('searchIcon').innerHTML=SVG.search;

/* CARD — photo only, controls in the four corners */
function card(r){
  const archived=isArchived(r);
  const img=r.image_file?`<img loading="lazy" src="${esc(r.image_file)}" alt="">`:`<div class="noimg">${CAT_ICON[r.category]||'👕'}</div>`;
  const rev=(!archived&&r.image_origin==='reverse-search');
  let icons=`<button class="cbtn tl" data-act="detail" title="Details" aria-label="Details">${SVG.info}</button>`;
  if(archived){
    icons+=`<button class="cbtn tr" data-act="restore" title="Restore to wardrobe" aria-label="Restore">${SVG.restore}</button>`;
  }else{
    icons+=`<button class="cbtn tr trash" data-act="trash" title="Remove from wardrobe" aria-label="Remove">${SVG.trash}</button>`;
    if(rev) icons+=`<button class="cbtn bl caution" data-act="disclaimer" title="About this photo" aria-label="About this photo">${SVG.rev}</button>`;
    if(showRet(r)) icons+=`<button class="cbtn br ret" data-act="returnq" title="Did you return this?" aria-label="Did you return this?">${SVG.ret}</button>`;
  }
  return `<div class="card ${archived?'past':''}" data-id="${esc(r.id)}" ${rev?'data-rev="1"':''} ${(!archived&&showRet(r))?'data-ret="1"':''}>
    <div class="photo" data-act="detail">${img}</div>${icons}</div>`;
}

/* DETAIL popup — the private purchase info */
function openDetail(id){
  const r=byId(id);
  const bd=gid('backdrop'), m=gid('modal'); m.className='modal detail';
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
  openBackdrop();
}

/* generic action sheet */
function sheet({icon,iconWarn,title,body,buttons}){
  const m=gid('modal'); m.className='modal';
  const btns=buttons.map((b,i)=>`<button class="btn ${b.kind||''}" data-i="${i}">${b.label}</button>`).join('');
  m.innerHTML=`<div class="mi ${iconWarn?'warn':''}">${icon}</div><h2>${title}</h2><p>${body}</p><div class="row">${btns}</div>`;
  buttons.forEach((b,i)=>{m.querySelector(`[data-i="${i}"]`).onclick=()=>{closeBackdrop();b.act&&b.act();};});
  openBackdrop();
  (m.querySelector('.btn.primary')||m.querySelector('.btn.warn')||m.querySelector('.btn')).focus();
}
function openBackdrop(){const bd=gid('backdrop');bd.classList.add('open');
  bd.onclick=ev=>{if(ev.target===bd)closeBackdrop();};
  document.onkeydown=ev=>{if(ev.key==='Escape')closeBackdrop();};
  const x=gid('modal').querySelector('[data-x]'); if(x)x.onclick=closeBackdrop;}
function closeBackdrop(){const bd=gid('backdrop');bd.classList.remove('open');gid('modal').className='modal';}

function confirmTrash(id){sheet({icon:SVG.trash,title:'Remove from your wardrobe?',
  body:`We’ll move this item to <b>My bin</b>. Sold, gifted, or worn out — you can restore it anytime.`,
  buttons:[{label:'Cancel'},{label:'Move to My bin',kind:'primary',act:()=>archive(id,'no_longer_owned')}]});}
function askReturn(id){sheet({icon:SVG.ret,iconWarn:true,title:'Did you return this item?',
  body:`If you sent it back, we’ll move it to <b>My bin</b>. If you kept it, we’ll just clear the flag.`,
  buttons:[{label:'I kept it',act:()=>{st(id).kept=true;saveState();render();toast('Kept in your wardrobe');}},
           {label:'I returned it',kind:'warn',act:()=>archive(id,'returned')}]});}
function showDisclaimer(id){const r=byId(id);sheet({icon:SVG.rev,iconWarn:true,title:'About this photo',
  body:`This photo was found by <b>reverse image search</b>${r.image_credit?` (${esc(r.image_credit)})`:''} because it wasn’t in your order email. The exact colour or version may differ from what you actually own.`,
  buttons:[{label:'Got it',kind:'primary'}]});}

/* init controls */
(function(){
  const brands=[...new Set(DATA.map(r=>r.brand).filter(Boolean))].sort((a,b)=>a.toLowerCase().localeCompare(b.toLowerCase()));
  const years=[...new Set(DATA.map(r=>r.year).filter(Boolean))].sort().reverse();
  gid('brand').insertAdjacentHTML('beforeend',brands.map(b=>`<option>${esc(b)}</option>`).join(''));
  gid('year').insertAdjacentHTML('beforeend',years.map(y=>`<option>${y}</option>`).join(''));
})();
function updateChips(active){
  const counts={};active.forEach(r=>counts[r.category]=(counts[r.category]||0)+1);
  const cats=Object.keys(counts).sort((a,b)=>counts[b]-counts[a]);
  gid('chips').innerHTML=`<span class="chip ${cat===''?'active':''}" data-cat="">All <span class="n">${active.length}</span></span>`+
    cats.map(c=>`<span class="chip ${cat===c?'active':''}" data-cat="${c}">${CAT_ICON[c]||''} ${CAT_LABEL[c]||c} <span class="n">${counts[c]}</span></span>`).join('');
}
function updateStats(active){
  const spend=active.reduce((a,r)=>a+(r.price_pln||0),0);
  const brands=new Set(active.map(r=>r.brand).filter(Boolean));
  const ds=active.map(r=>r.order_date).filter(Boolean).sort();
  const fmt=n=>Math.round(n).toLocaleString('fr-FR').replace(/ |,/g,' ');
  gid('stats').innerHTML=`<span><b id="shown">0</b> shown</span>`+
    `<span><b>${active.length}</b> items · <b>${active.filter(r=>r.image_file).length}</b> with photos</span>`+
    `<span>tracked value <b>${fmt(spend)} zł</b></span>`+(ds.length?`<span>${ds[0]} → ${ds[ds.length-1]}</span>`:'')+
    `<span><b>${brands.size}</b> brands</span>`;
}
function render(){
  const active=DATA.filter(r=>!isArchived(r)), past=DATA.filter(isArchived);
  gid('cActive').textContent=active.length; gid('cPast').textContent=past.length;
  gid('tabActive').classList.toggle('active',view==='active');
  gid('tabPast').classList.toggle('active',view==='past');
  gid('hideRetWrap').style.display=view==='active'?'':'none';
  updateStats(active); updateChips(active);
  const q=gid('q').value.toLowerCase().trim(), b=gid('brand').value, y=gid('year').value;
  const ret=gid('retailer').value, hideRet=gid('hideRet').checked;
  const list=(view==='active'?active:past).filter(r=>{
    if(cat&&r.category!==cat)return false;
    if(b&&r.brand!==b)return false;
    if(y&&r.year!==y)return false;
    if(ret&&r.retailer!==ret)return false;
    if(view==='active'&&hideRet&&showRet(r))return false;
    if(q){const h=(r.brand+' '+r.name+' '+r.category+' '+r.retailer).toLowerCase();if(!h.includes(q))return false;}
    return true;
  });
  gid('grid').innerHTML=list.map(card).join('');
  gid('shown').textContent=list.length;
  const e=gid('empty');
  if(list.length){e.style.display='none';}
  else{e.style.display='block';e.innerHTML=view==='past'
    ?`<div class="big">🗑️</div><h3>Your bin is empty</h3><div>Items you return or remove land here — restore them anytime.</div>`
    :`<div class="big">🔍</div><h3>Nothing matches</h3><div>Try clearing a filter or search term.</div>`;}
  gid('legend').innerHTML=`<span>${SVG.info} Details</span><span>${SVG.trash} Remove</span><span>${SVG.rev} Reverse-searched photo</span><span>${SVG.ret} Possibly returned</span>`;
}

/* interactions */
gid('grid').addEventListener('click',e=>{
  const cardEl=e.target.closest('.card'); if(!cardEl)return; const id=cardEl.dataset.id;
  const actEl=e.target.closest('[data-act]'); if(!actEl)return;
  const a=actEl.dataset.act;
  if(a==='detail')openDetail(id);
  else if(a==='trash')confirmTrash(id);
  else if(a==='returnq')askReturn(id);
  else if(a==='disclaimer')showDisclaimer(id);
  else if(a==='restore')restore(id);
});
function leave(cardEl,cb){if(!cardEl){cb();return;}cardEl.classList.add('leaving');setTimeout(cb,360);}
function archive(id,reason){const s=st(id);s.archived=true;s.reason=reason;s.archivedAt=new Date().toISOString();delete s.kept;saveState();
  const c=document.querySelector(`.card[data-id="${cssEsc(id)}"]`);
  leave(c,()=>{render();toast('Moved to My bin','Undo',()=>unarchive(id));});}
function unarchive(id){const s=state[id]||{};delete s.archived;delete s.reason;delete s.archivedAt;saveState();render();}
function restore(id){const c=document.querySelector(`.card[data-id="${cssEsc(id)}"]`);
  (c&&view==='past')?leave(c,()=>{unarchive(id);toast('Back in your wardrobe');}):(unarchive(id),toast('Back in your wardrobe'));}

function toast(msg,actionLabel,onAction){
  const wrap=gid('toasts'),t=document.createElement('div');t.className='toast';
  t.innerHTML=`<span>${msg}</span>`+(actionLabel?`<button>${actionLabel}</button>`:'');
  if(actionLabel)t.querySelector('button').onclick=()=>{onAction();dismiss();};
  wrap.appendChild(t);
  let killed=false;const dismiss=()=>{if(killed)return;killed=true;t.classList.add('out');setTimeout(()=>t.remove(),320);};
  setTimeout(dismiss,5000);
}

['q','brand','year','retailer','hideRet'].forEach(id=>gid(id).addEventListener('input',render));
gid('chips').addEventListener('click',e=>{const c=e.target.closest('.chip');if(!c)return;cat=c.dataset.cat;render();});
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{view=t.dataset.view;cat='';render();});
render();
</script>
</body>
</html>"""

out = DOC.replace("%(data_json)s", json.dumps(data, ensure_ascii=False))
out = out.replace("%(cat_icon)s", json.dumps(CAT_ICON, ensure_ascii=False))
open(os.path.join(ROOT, OUT_NAME), "w").write(out)
print(f"Wrote {OUT_NAME} — {len(data)} items")
