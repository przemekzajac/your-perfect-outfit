# 👔 Your Awesome Digital Wardrobe

Your closet, reconstructed from your inbox. A visual catalog of the clothes & shoes
you've bought online, mined from your Gmail order-confirmation emails (last ~5 years),
with an interactive, privacy-first moodboard for keeping it true to what you own.

**Open [`index.html`](index.html)** in a browser (with the `images/` folder next to
it), or open the single-file **`wardrobe_standalone.html`** anywhere — it has every
photo embedded, so it works on its own.

## The app (UX)

**Moodboard cards = just the photo.** Nothing identifying is on screen at a glance.
Each card carries up to four corner controls:

- **(i) top-left** → detail popup with the **private info**: brand, product name,
  price, shop, size, order date, category, order #, and the product link.
- **🗑 trash, top-right** → confirm → move to **My bin** (reversible).
- **return, bottom-right** (only if possibly returned) → "Did you return this?" →
  **I returned it** (animates out to My bin) / **I kept it** (just clears the icon).
- **caution, bottom-left** (only if the photo was reverse-searched) → a disclaimer
  popup explaining the photo was found on the web and may not be exact.

Other bits:
- **My wardrobe** & **My bin** views; **Undo** toast on removal; **Restore** from My
  bin. Removal reason is tracked (returned vs. no longer owned). Nothing is truly deleted.
- **Light / dark** — Claude-inspired warm light theme with a dark toggle (remembered).
- Live stats; category chips, brand / year / shop filters, search, "hide
  possibly-returned" toggle.
- **Persistence** — all choices saved in the browser via `localStorage`. No backend yet.

Verified with a jsdom harness (22/22 interaction + privacy assertions passing).

## Files

- **`index.html`** / **`wardrobe_standalone.html`** — the app (linked vs. embedded images).
- **`images/`** — downloaded product photos.
- **`data/wardrobe.json`** — the structured catalog (one record per item).
- **`build/parse.py`** — raw email dumps → `wardrobe.json` + downloads images.
- **`build/recover_nike.py`** — reverse-searches images for items with none in-email.
- **`build/build_html.py`** — renders the app (`WARDROBE_EMBED=1` → single file).
- **`data/raw/`** — raw Gmail thread JSON (gitignored: contains your delivery address).

## Current snapshot

- **75 items** across **40 orders**, **30 brands**, **2021–2026**
- Categories: Tops 23 · Bottoms 19 · Accessories 14 · Shoes 9 · Sweaters & Hoodies 6 · Underwear 4
- **75 items with photos** — 69 packshots straight from the Zalando emails, plus
  **6 Nike items reverse-searched** (Nike's emails carry no product image). These show
  a representative colourway and are flagged with the caution icon.
- Tracked value (where price was in the email): **~15,082 zł**

## Notes & caveats

- **Returns are order-level.** Items from an order that included a return are flagged
  *possibly returned* — confirm each via the return icon to make the wardrobe exact.
- Brand, product name, colour, size and price come from the email body; the product
  image and link come from the embedded thumbnail.
- **Nike images** were recovered by reverse-searching the product name (e-tennis,
  tennisnuts, tradeinn). Emails don't record colour, so the navy "410" tennis polo/
  shorts are shown as a representative matching set.

## Rebuild

```bash
python3 wardrobe/build/parse.py          # parse emails + download images
python3 wardrobe/build/recover_nike.py   # backfill image-less items
python3 wardrobe/build/build_html.py      # -> index.html
WARDROBE_EMBED=1 python3 wardrobe/build/build_html.py   # -> wardrobe_standalone.html
```

## Roadmap (SaaS)

Multi-user accounts + per-user Gmail OAuth, a database behind the wardrobe state,
item-level return detection (parse return emails to pin the exact article), and an
"outfits" view grouping items bought together. Cost-per-wear & return-rate stats fall
out of the tracked removal reasons.
