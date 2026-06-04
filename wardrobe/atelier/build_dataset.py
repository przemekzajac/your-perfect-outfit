#!/usr/bin/env python3
"""Curate exactly 200 women's demo items from the CC0 clothing-dataset-small.

Per chosen photo: compute dominant colour (Pillow), resize for embedding, and
synthesize rich Polish metadata. Tops up accessories from DummyJSON (best-effort,
with SSL-fallback + retry). Backfills from the dataset to land on exactly 200.
Includes a few returned + underwear items (filter tests). Output -> demo200/.
"""
import os, json, glob, random, io, ssl, time, urllib.request
from PIL import Image, ImageOps

random.seed(7)
SRC = "/tmp/cds/clothing-dataset-small-master"
HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "demo200"); IMG = os.path.join(OUTDIR, "images")
os.makedirs(IMG, exist_ok=True)
TARGET = 200
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
_NOVERIFY = ssl.create_default_context(); _NOVERIFY.check_hostname = False; _NOVERIFY.verify_mode = ssl.CERT_NONE

def fetch(url, tries=3):
    last = None
    for i in range(tries):
        for ctx in (None, _NOVERIFY):   # fall back to unverified on clock-skew SSL errors
            try:
                return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25, context=ctx).read()
            except Exception as e:
                last = e
        time.sleep(1)
    raise last

PALETTE = [
    ("black","czarny",(28,28,28),True),("white","biały",(244,244,242),True),
    ("grey","szary",(150,150,150),True),("charcoal","grafitowy",(70,72,76),True),
    ("navy","granatowy",(38,52,84),True),("blue","niebieski",(60,95,165),False),
    ("light blue","błękitny",(170,200,226),False),("denim","denimowy",(62,92,132),True),
    ("red","czerwony",(178,52,52),False),("burgundy","bordowy",(112,32,46),False),
    ("pink","różowy",(222,150,172),False),("blush","pudrowy róż",(232,200,200),False),
    ("green","zielony",(72,112,72),False),("olive","oliwkowy",(112,112,62),False),
    ("khaki","khaki",(150,140,100),True),("beige","beżowy",(214,198,168),True),
    ("cream","kremowy",(240,232,212),True),("brown","brązowy",(110,76,54),True),
    ("camel","karmelowy",(193,154,107),True),("tan","jasnobrązowy",(200,160,112),True),
    ("yellow","żółty",(222,190,84),False),("mustard","musztardowy",(190,150,50),False),
    ("orange","pomarańczowy",(210,130,60),False),("purple","fioletowy",(112,70,140),False),
    ("lilac","liliowy",(196,178,216),False),("teal","morski",(40,120,128),False),
]
def _idx(rgb):
    best=0;bd=1e9
    for i,(en,pl,p,neu) in enumerate(PALETTE):
        d=sum((rgb[k]-p[k])**2 for k in range(3))
        if d<bd:bd=d;best=i
    return best
def nearest_colour(rgb):
    en,pl,p,neu=PALETTE[_idx(rgb)]; return (en,pl,neu)
def colour_of(im):
    # mode over a tight centre crop -> robust for prints / multi-colour garments
    w,h=im.size; cw,ch=int(w*0.45),int(h*0.45); l=(w-cw)//2; t=(h-ch)//2
    c=im.crop((l,t,l+cw,t+ch)).resize((46,46),Image.BILINEAR)
    votes={}
    for px in c.getdata():
        i=_idx(px); votes[i]=votes.get(i,0)+1
    en,pl,p,neu=PALETTE[max(votes,key=votes.get)]
    return (en,pl,neu)
def save_img(im,dest):
    im=im.copy(); im.thumbnail((520,520),Image.LANCZOS); im.save(dest,"JPEG",quality=82,optimize=True)

BRANDS=["Reserved","Mohito","Sinsay","Cropp","House","Mango","Zara","H&M","COS","Massimo Dutti",
        "& Other Stories","Stradivarius","Bershka","Medicine","Answear Lab","Levi's","Wrangler",
        "Vagabond","Veja","adidas Originals","Nike","Tommy Hilfiger","Calvin Klein","Guess","Pinko"]
def variants(cls):
    if cls=="dress": return ("dresses", random.choice(["Sukienka midi","Sukienka mini","Sukienka maxi","Sukienka koszulowa","Sukienka kopertowa"]),"Dress",3,"all","wiskoza")
    if cls=="skirt": return ("bottoms", random.choice(["Spódnica midi","Spódnica mini","Spódnica plisowana","Spódnica ołówkowa"]),"Skirt",3,"all","tkanina")
    if cls=="pants": return ("bottoms", random.choice(["Spodnie","Jeansy","Spodnie szerokie","Spodnie cygaretki","Chinosy"]),"Trousers",2,"all","bawełna")
    if cls=="shorts": return ("bottoms", random.choice(["Szorty","Szorty lniane","Szorty jeansowe"]),"Shorts",2,"warm","len")
    if cls=="t-shirt": return ("tops", random.choice(["T-shirt","Top","Koszulka"]),"T-shirt",2,"all","bawełna")
    if cls=="shirt": return ("tops", random.choice(["Koszula","Bluzka","Koszula oversize"]),"Shirt",3,"all","bawełna")
    if cls=="longsleeve_top": return ("tops", random.choice(["Bluzka z długim rękawem","Longsleeve","Golf prążkowany"]),"Long-sleeve top",2,"all","bawełna")
    if cls=="longsleeve_knit": return ("knitwear", random.choice(["Sweter","Kardigan","Golf","Sweter oversize","Bluza"]),"Knit",3,"cold","dzianina")
    if cls=="outwear": return ("outerwear", random.choice(["Kurtka","Płaszcz","Marynarka","Trencz","Ramoneska","Płaszcz wełniany"]),"Outerwear",3,"cold","tkanina")
    if cls=="shoes": return ("shoes", random.choice(["Sneakersy","Botki","Czółenka","Baleriny","Sandały","Mokasyny","Kozaki"]),"Shoes",2,"all","skóra")
    if cls=="hat": return ("accessory", random.choice(["Czapka","Kapelusz","Beret"]),"Hat",2,"all","tkanina")
    return ("tops","Top","Top",2,"all","bawełna")
PATTERNS=[("gładki","solid",0.72),("w paski","striped",0.1),("w kwiaty","floral",0.07),("krata","checked",0.05),("groszki","polka dot",0.03),("z nadrukiem","printed",0.03)]
def pick_pattern():
    r=random.random();acc=0
    for pl,en,p in PATTERNS:
        acc+=p
        if r<=acc:return pl,en
    return "gładki","solid"
def price_for(cat):
    return {"dresses":(119,399),"bottoms":(89,299),"tops":(49,179),"knitwear":(99,329),
            "outerwear":(199,699),"shoes":(149,499),"accessory":(39,259)}.get(cat,(49,199))
def size_for(cat):
    if cat=="shoes": return str(random.choice([36,37,38,39,40,41]))
    if cat=="accessory": return "one size"
    return random.choice(["XS","S","S","M","M","L","XL","36","38","40"])
def season_adjust(noun,base):
    n=noun.lower()
    if any(k in n for k in ["wełnian","golf","sweter","kardigan","płaszcz","kozaki","trencz"]): return "cold"
    if any(k in n for k in ["lnian","sandały","szorty","maxi"]): return "warm"
    return base
def formality_adjust(noun,base):
    n=noun.lower(); f=base
    if any(k in n for k in ["czółenka","marynarka","płaszcz","ołówkowa","kopertowa","trencz"]): f+=1
    if any(k in n for k in ["sneakersy","szorty","jeansy","t-shirt","bluza","baleriny"]): f-=1
    return max(1,min(5,f+random.choice([0,0,0,1])))

n=0; items=[]; used=set()
def mint(f,cls,prefix="d"):
    global n
    try: im=ImageOps.exif_transpose(Image.open(f)).convert("RGB")
    except Exception: return False
    n+=1; iid=f"{prefix}{n:03d}"; dest=os.path.join(IMG,iid+".jpg")
    en,pl,neu=colour_of(im); save_img(im,dest); used.add(f)
    cat,noun_pl,noun_en,bF,bS,fabric=variants(cls); pat_pl,pat_en=pick_pattern()
    lo,hi=price_for(cat); price=random.randint(lo,hi)//10*10+9
    nm=f"{noun_pl} - {pl}" + ("" if pat_pl=="gładki" else f", {pat_pl}")
    items.append({"id":iid,"brand":random.choice(BRANDS),"name":nm,"name_en":f"{noun_en} - {en}",
        "category":cat,"color":en,"color_pl":pl,"neutral":neu,"pattern":pat_en,
        "formality":formality_adjust(noun_pl,bF),"season":season_adjust(noun_pl,bS),"fabric":fabric,
        "price":f"{price} zł","size":size_for(cat),"returned_order":False})
    return True

def class_files(cls):
    base="longsleeve" if cls.startswith("longsleeve") else cls
    fs=sorted(glob.glob(os.path.join(SRC,"*",base,"*.jpg")))
    random.Random(hash(cls)&0xffff).shuffle(fs); return fs

PLAN={"dress":24,"skirt":10,"pants":24,"shorts":6,"t-shirt":22,"shirt":14,
      "longsleeve_top":8,"longsleeve_knit":18,"outwear":21,"shoes":28,"hat":4}
for cls,count in PLAN.items():
    taken=0
    for f in class_files(cls):
        if taken>=count: break
        if f in used: continue
        if mint(f,cls): taken+=1
print(f"dataset items: {len(items)}")

def dummy(cat,noun_pl,noun_en,want):
    global n
    try: data=json.loads(fetch(f"https://dummyjson.com/products/category/{cat}?limit=30&select=title,images,thumbnail").decode())
    except Exception as e: print(f"  dummyjson {cat} failed: {e}"); return
    got=0
    for p in data.get("products",[]):
        if got>=want: break
        u=(p.get("images") or [p.get("thumbnail")])[0]
        if not u: continue
        try:
            im=ImageOps.exif_transpose(Image.open(io.BytesIO(fetch(u)))).convert("RGB")
        except Exception: continue
        n+=1; iid=f"a{n:03d}"; en,pl,neu=colour_of(im); save_img(im,os.path.join(IMG,iid+".jpg")); got+=1
        lo,hi=price_for("accessory"); price=random.randint(lo,hi)//10*10+9
        items.append({"id":iid,"brand":random.choice(BRANDS),"name":f"{noun_pl} - {pl}","name_en":f"{noun_en} - {en}",
            "category":"accessory","color":en,"color_pl":pl,"neutral":neu,"pattern":"solid","formality":3,
            "season":"all","fabric":"—","price":f"{price} zł","size":"one size","returned_order":False})
    print(f"  +{got} {cat}")
dummy("womens-bags","Torebka","Bag",6); dummy("womens-watches","Zegarek","Watch",5)
dummy("sunglasses","Okulary przeciwsłoneczne","Sunglasses",5); dummy("womens-jewellery","Biżuteria","Jewellery",4)

# backfill from dataset to hit exactly TARGET-3 (leaving room for 3 underwear)
backfill_order=["t-shirt","pants","dress","shoes","shirt","outwear","longsleeve_knit","skirt","longsleeve_top","shorts","hat"]
pools={c:[f for f in class_files(c if not c.startswith('longsleeve') else c) if f not in used] for c in backfill_order}
gi=0
while len(items) < TARGET-3:
    cls=backfill_order[gi%len(backfill_order)]; gi+=1
    pool=pools[cls]
    if not pool: continue
    f=pool.pop()
    if f in used: continue
    mint(f,cls)
    if gi>4000: break
# trim if somehow over
items=items[:TARGET-3]

# underwear (tiles in app) + returned flags
for nm_pl,nm_en,col,colpl in [("Biustonosz","Bra","black","czarny"),("Komplet bielizny","Lingerie set","nude","cielisty"),("Body","Bodysuit","white","biały")]:
    n+=1
    items.append({"id":f"u{n:03d}","brand":random.choice(["Calvin Klein","Intimissimi","Hunkemöller"]),
        "name":f"{nm_pl} - {colpl}","name_en":f"{nm_en} - {col}","category":"underwear","color":col,"color_pl":colpl,
        "neutral":True,"pattern":"solid","formality":1,"season":"all","fabric":"bawełna","price":"79 zł",
        "size":random.choice(["S","M","L"]),"returned_order":False})
for it in random.sample([i for i in items if i["category"]!="underwear"],6): it["returned_order"]=True

random.shuffle(items)
json.dump({"items":items},open(os.path.join(OUTDIR,"wardrobe_women.json"),"w"),ensure_ascii=False,indent=1)
cats={}
for it in items: cats[it["category"]]=cats.get(it["category"],0)+1
print(f"\nTOTAL {len(items)} | returned={sum(1 for i in items if i['returned_order'])} underwear={cats.get('underwear',0)} | images={len(glob.glob(os.path.join(IMG,'*.jpg')))}")
print("by category:",cats)
