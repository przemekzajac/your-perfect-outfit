# Atelier bridge (Claude Max, no API key)

A tiny local server that powers Atelier's outfit recommendations using **your
Claude Max subscription** — no API key, no per-token billing. It uses the Claude
Agent SDK, which authenticates from your `claude login` credentials. Engine is
**text-only Opus** (`claude-opus-4-8`): the stylist reasons from each item's
name/colour/category, which is exactly what the Atelier prompt's Step-0
enrichment is designed for. The app still shows the real photos to you.

> Why text-only? The Agent SDK (the Max path) can't send local image files to
> the model. Sending photos would require the pay-per-token Messages API. Since
> the item *names* carry colour and cut, text-only on Max is free and works well.
> A future SaaS would switch to the API for true vision.

## Setup (one time)

```bash
cd wardrobe/atelier/bridge
npm install                 # installs @anthropic-ai/claude-agent-sdk
claude login                # authenticate with your Max account (opens browser)
unset ANTHROPIC_API_KEY     # IMPORTANT: if set, it bills the API instead of Max
```

## Run

```bash
npm start                   # -> http://localhost:8787
```

You should see `Atelier bridge → http://localhost:8787`. Leave it running.

## Connect the app

Open the wardrobe app, go to **Atelier ▸ Settings**, and set
**"Connect to local Atelier"** to `http://localhost:8787`. From then on, "Get
today's outfit" calls Opus on your Max plan. If the bridge isn't running, the app
silently falls back to its built-in offline sample stylist, so it never breaks.

## Endpoints

- `GET /health` → `{ ok, model, usingApiKey, ready }` — the app pings this to show
  a green "Connected (Max)" status. If `usingApiKey` is `true`, you forgot to
  unset `ANTHROPIC_API_KEY` and you'd be billing the API.
- `POST /atelier/outfits` with `{ profile, mood, weather, location, wardrobe }`
  → `{ intro, outfits:[ {name, itemIds, why} x3 ], engine }`.

## Guarantees baked in

- **Hard filters** re-applied server-side: items with `returned_order:true` and
  `category:"underwear"` are removed before the model sees anything.
- **No hallucinated clothes:** the reply is schema-validated and every `itemId` is
  checked against the wardrobe; unknown IDs are dropped.

## Notes / caveats

- As of mid-2026, Agent SDK usage on Max draws from a **separate monthly credit**
  on your plan (not your interactive chat limit). Opus uses more of it than
  Sonnet — set `ATELIER_MODEL=claude-sonnet-4-6` to stretch it further.
- Headless machines can't run `claude login` interactively; authenticate on a
  machine with a browser (creds are cached in `~/.claude`).
- Change the port with `ATELIER_PORT=9000 npm start`.
