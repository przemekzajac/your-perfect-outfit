# 👔 Your Digital Wardrobe

A visual catalog of the clothes & shoes you've bought online, reconstructed from
your Gmail order-confirmation emails (last ~5 years).

**Open [`index.html`](index.html)** in any browser — it's fully self-contained
(catalog data is embedded; images are local). Double-click works, no server needed.

## What's inside

- **`index.html`** — browsable gallery: responsive photo grid with filters by
  category, brand, year, and shop, plus free-text search and a "hide returned" toggle.
- **`images/`** — downloaded product packshots (one per item).
- **`data/wardrobe.json`** — the structured catalog (one record per item).
- **`build/parse.py`** — parses raw email dumps → `wardrobe.json` + downloads images.
- **`build/build_html.py`** — renders `wardrobe.json` → `index.html`.
- **`data/raw/`** — raw Gmail thread JSON (gitignored: contains your delivery address).

## Current snapshot

- **75 items** across **40 orders**, **30 brands**
- **75 items with photos** — 69 packshots pulled straight from the Zalando emails,
  plus **6 Nike items reverse-searched** from retailer sites by product name
  (Nike's shipping emails carry no product image). Reverse-searched photos are
  marked `↗ web img` in the gallery; the exact colourway may differ.
- Sources: **Zalando** (2021–2026) and **Nike** (2022)
- Tracked spend (where price was in the email): **~15,082 zł**

## Notes & caveats

- **Returns**: matched against Zalando "return received" emails at the *order* level.
  10 orders (22 items) belonged to an order that included a return — flagged with a
  `↩ returned?` badge. Because returns are order-level, a flagged item may still be
  owned (e.g. you returned only one item of a multi-item order).
- Brand, product name, colour, size and price come from the email body; the product
  image and link come from the embedded product thumbnail.
- **Nike images** were recovered by reverse-searching the product name on retailer
  sites (e-tennis, tennisnuts, tradeinn) and taking the product photo. See
  `build/recover_nike.py`. Because the emails don't record colour, these show a
  representative colourway (the navy "410" tennis polo/shorts are a matching set).
- Only retailers that emailed itemised order confirmations to this account are
  included. eobuwie / Answear / Modivo sent only newsletters, so no items from them.

## Rebuilding / updating

```bash
# 1. (re-)dump order emails into wardrobe/data/raw/<threadId>.json via Gmail
# 2. parse + download images
python3 wardrobe/build/parse.py
# 3. regenerate the gallery
python3 wardrobe/build/build_html.py
```
