# 👔 Your Wardrobe

Your closet, quietly reconstructed from your inbox. A visual catalog of the clothes
& shoes you've bought online, mined from your Gmail order-confirmation emails
(last ~5 years), with an interactive, privacy-first UI for keeping it true to what
you actually own.

**Open [`index.html`](index.html)** in a browser (with the `images/` folder next to
it), or open the single-file **`wardrobe_standalone.html`** anywhere — it has every
photo embedded, so it works on its own.

## The app (UX)

**Privacy-first cards.** The grid is a clean moodboard of your clothes — the card
front shows **only the photo** plus status & actions. Nothing identifying (what you
bought or what you paid) is on screen until you ask for it.

- **(i) detail popup** holds the **private info**: brand, product name, price,
  shop/marketplace, size, order date, category, order #, and the product link.
- **Visible on the card front** (status + actions):
  - **Reverse-searched** marker (photo-with-caution icon) — "photo may not be exact";
    hover the ⓘ for the source/caveat. Flags photos sourced from the web, not your email.
  - **Possibly returned** (round-trip-arrows icon) with two inline choices:
    **I returned it** / **I have it**.
  - **I no longer have it** — for things sold, gifted, or worn out.
- **Actions**
  - *I have it* → clears the returned flag, keeps the item.
  - *I returned it* / *I no longer have it* → confirm → animate out → move to **Past
    items** (reason tracked). Each shows an **Undo** toast and is **reversible**
    (Restore). Nothing is ever truly deleted.
- **Light / dark** — Claude-inspired warm light theme with a dark toggle (remembered).
- **Two views** — *My wardrobe* and *Past items*; live stats; category chips,
  brand / year / shop filters, search, and a "hide possibly-returned" toggle.
- **Persistence** — all choices (kept / returned / removed / theme) are saved in the
  browser via `localStorage`. No backend yet.

Verified with a jsdom harness (21/21 interaction + privacy assertions passing).

## Files

- **`index.html`** / **`wardrobe_standalone.html`** — the app (linked vs. embedded images).
- **`images/`** — downloaded product photos (one per item).
- **`data/wardrobe.json`** — the structured catalog (one record per item).
- **`build/parse.py`** — raw email dumps → `wardrobe.json` + downloads images.
- **`build/recover_nike.py`** — reverse-searches images for items with none in-email.
- **`build/build_html.py`** — renders `wardrobe.json` → the app (`WARDROBE_EMBED=1`
  for the single-file build).
- **`data/raw/`** — raw Gmail thread JSON (gitignored: contains your delivery address).

## Current snapshot

- **75 items** across **40 orders**, **30 brands**, **2021–2026**
- **75 items with photos** — 69 packshots straight from the Zalando emails, plus
  **6 Nike items reverse-searched** from retailer sites (Nike's emails carry no
  product image). Reverse-searched photos are marked and may differ in colourway.
- Tracked value (where price was in the email): **~15,082 zł**

## Notes & caveats

- **Returns are order-level.** 10 orders (22 items) belonged to an order that
  included a return, so they're flagged *Possibly returned* — confirm per item with
  the inline CTAs to make the wardrobe exact.
- Brand, product name, colour, size and price come from the email body; the product
  image and link come from the embedded thumbnail.
- **Nike images** were recovered by reverse-searching the product name (e-tennis,
  tennisnuts, tradeinn). Since emails don't record colour, these show a representative
  colourway (the navy "410" tennis polo/shorts are a matching set).

## Rebuild

```bash
python3 wardrobe/build/parse.py          # parse emails + download images
python3 wardrobe/build/recover_nike.py   # backfill image-less items
python3 wardrobe/build/build_html.py      # -> index.html
WARDROBE_EMBED=1 python3 wardrobe/build/build_html.py   # -> wardrobe_standalone.html
```

## Roadmap (SaaS)

Multi-user accounts + per-user Gmail OAuth, a real database behind the wardrobe
state, item-level return detection (parse return emails to pin the exact article),
and an "outfits" view grouping items bought together. Cost-per-wear & return-rate
stats fall out of the tracked removal reasons.
