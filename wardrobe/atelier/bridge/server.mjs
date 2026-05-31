#!/usr/bin/env node
/**
 * Atelier bridge — runs the personal stylist on your Claude Max plan.
 *
 * It uses the Claude Agent SDK, which authenticates from your `claude login`
 * (Max) credentials — NO API key, NO per-token billing. Engine is TEXT-ONLY
 * Opus: the model reasons from each item's name/colour/category/fields (the
 * Atelier prompt's Step-0 enrichment is built for exactly this). The app still
 * shows the real photos to the user; only the model works from text.
 *
 * POST /atelier/outfits  { profile, mood, weather, location, wardrobe:[...] }
 *   -> { intro, outfits:[ { name, itemIds:[], why } x3 ], engine:"max-opus" }
 * GET  /health           -> { ok, model, usingApiKey, ready }
 *
 * Run:  npm install && claude login && unset ANTHROPIC_API_KEY && npm start
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = process.env.ATELIER_PORT || 8787;
const MODEL = process.env.ATELIER_MODEL || "claude-opus-4-8";
const SYSTEM_PROMPT = fs.readFileSync(path.join(__dirname, "..", "atelier.system.md"), "utf8");

// strict JSON contract for the model's reply
const SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    intro: { type: "string" },
    outfits: {
      type: "array",
      minItems: 3,
      maxItems: 3,
      items: {
        type: "object",
        additionalProperties: false,
        properties: {
          name: { type: "string" },
          itemIds: { type: "array", items: { type: "string" } },
          why: { type: "string" },
        },
        required: ["name", "itemIds", "why"],
      },
    },
  },
  required: ["intro", "outfits"],
};

// ---- Agent SDK (lazy import so /health works even before npm install) ----
let _query = null;
async function getQuery() {
  if (_query) return _query;
  const mod = await import("@anthropic-ai/claude-agent-sdk");
  _query = mod.query;
  return _query;
}

// ---- helpers ----
const VISIBLE = (it) => it && !it.returned_order && it.category !== "underwear";

function buildUserText({ profile, mood, weather, location, wardrobe }) {
  const items = (wardrobe || []).filter(VISIBLE);
  const lines = items.map((it) => {
    const bits = [
      `id=${it.id}`,
      it.brand && `brand=${it.brand}`,
      it.name && `name="${it.name}"`,
      it.category && `category=${it.category}`,
      it.color && `colour=${it.color}`,
      it.formality && `formality=${it.formality}`,
      it.season && `season=${it.season}`,
    ].filter(Boolean);
    return "- " + bits.join("  ");
  });
  const w = weather || {};
  const profileLines = Object.entries(profile || {})
    .map(([k, v]) => `- ${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
    .join("\n");
  return [
    `TODAY'S OUTFIT REQUEST`,
    ``,
    `Location: ${location || "Warsaw"}`,
    `Weather: ${w.summary || "(unknown)"}${w.tempC != null ? ` — ${w.tempC}°C` : ""}${w.condition ? ` (${w.condition})` : ""}${w.windKph != null ? `, wind ${w.windKph} km/h` : ""}`,
    `Mood for today: ${mood || "(not set)"}`,
    ``,
    `HER STYLE PROFILE:`,
    profileLines || "(no profile provided)",
    ``,
    `HER KEPT WARDROBE (returned items and underwear already removed — style only from these IDs):`,
    ...lines,
    ``,
    `Build exactly three complete, genuinely different outfits for today's mood and weather, honouring her Style Profile. Return strict JSON per the OUTPUT CONTRACT — itemIds must come from the list above.`,
  ].join("\n");
}

function validate(parsed, wardrobe) {
  const ok = new Set((wardrobe || []).filter(VISIBLE).map((i) => i.id));
  const outfits = (parsed.outfits || [])
    .map((o) => ({
      name: String(o.name || "Look"),
      why: String(o.why || ""),
      itemIds: (o.itemIds || []).filter((id) => ok.has(id)),
    }))
    .filter((o) => o.itemIds.length >= 2); // drop empties / hallucinations
  return { intro: String(parsed.intro || ""), outfits };
}

async function styleOutfits(payload) {
  const query = await getQuery();
  const prompt = buildUserText(payload);
  let structured = null;
  let textBuf = "";
  let errSubtype = null;

  for await (const message of query({
    prompt,
    options: {
      model: MODEL,
      systemPrompt: SYSTEM_PROMPT,
      allowedTools: [],
      maxTurns: 1,
      outputFormat: { type: "json_schema", schema: SCHEMA },
    },
  })) {
    if (message.type === "assistant" && message.message?.content) {
      for (const block of message.message.content) {
        if (block && typeof block === "object" && "text" in block) textBuf += block.text;
      }
    } else if (message.type === "result") {
      if (message.subtype === "success" && message.structured_output) {
        structured = message.structured_output;
      } else if (message.subtype && String(message.subtype).startsWith("error")) {
        errSubtype = message.subtype;
      }
    }
  }

  if (!structured && textBuf) {
    // fallback: pull JSON out of the text
    const m = textBuf.match(/```(?:json)?\s*([\s\S]*?)```/) || [null, textBuf];
    try {
      structured = JSON.parse((m[1] || textBuf).trim());
    } catch (_) {
      /* ignore */
    }
  }
  if (!structured) {
    throw new Error(`Model returned no structured output${errSubtype ? ` (${errSubtype})` : ""}.`);
  }
  return { ...validate(structured, payload.wardrobe), engine: "max-opus-text" };
}

// ---- http plumbing ----
function send(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  if (req.method === "OPTIONS") return send(res, 204, {});
  if (req.method === "GET" && req.url === "/health") {
    return send(res, 200, {
      ok: true,
      model: MODEL,
      usingApiKey: !!process.env.ANTHROPIC_API_KEY,
      ready: true,
    });
  }
  if (req.method === "POST" && req.url === "/atelier/outfits") {
    let raw = "";
    req.on("data", (c) => {
      raw += c;
      if (raw.length > 2_000_000) req.destroy();
    });
    req.on("end", async () => {
      try {
        const payload = JSON.parse(raw || "{}");
        const result = await styleOutfits(payload);
        send(res, 200, result);
      } catch (err) {
        console.error("[atelier] error:", err?.message || err);
        send(res, 500, { error: String(err?.message || err) });
      }
    });
    return;
  }
  send(res, 404, { error: "not found" });
});

server.listen(PORT, () => {
  console.log(`\n  Atelier bridge → http://localhost:${PORT}`);
  console.log(`  model: ${MODEL}  ·  engine: Max (Agent SDK), text-only`);
  if (process.env.ANTHROPIC_API_KEY) {
    console.log(
      `  ⚠  ANTHROPIC_API_KEY is set — this will bill the pay-per-token API, NOT your Max plan.\n     Unset it ( unset ANTHROPIC_API_KEY ) to use Max.`
    );
  }
  console.log(`  In the app: Atelier ▸ Settings ▸ "Connect to local Atelier" → http://localhost:${PORT}\n`);
});
