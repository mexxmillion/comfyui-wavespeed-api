import { app } from "../../scripts/app.js";

// ── Pricing (mirrors pricing.py) ───────────────────────────────────────────────

const IMAGE_COSTS = {
  "google/nano-banana-pro/edit-ultra": { "1k": 0.15,  "2k": 0.21,  "4k": 0.28  },
  "google/nano-banana-pro/edit":       { "1k": 0.14,  "2k": 0.18,  "4k": 0.25  },
  "google/nano-banana-2/edit":         { "1k": 0.07,  "2k": 0.10,  "4k": 0.14  },
  "google/nano-banana-2/edit-fast":    { "1k": 0.045, "2k": 0.07,  "4k": 0.10  },
  "bytedance/seedream-v5.0-lite/edit":            { "1k": 0.035, "2k": 0.05, "4k": 0.07 },
  "bytedance/seedream-v5.0-lite/edit-sequential": { "1k": 0.035, "2k": 0.05, "4k": 0.07 },
  "bytedance/seedream-v4.5/edit":                 { "1k": 0.04,  "2k": 0.055,"4k": 0.08 },
  "bytedance/seedream-v4.5/edit-sequential":      { "1k": 0.04,  "2k": 0.055,"4k": 0.08 },
};

const VIDEO_COSTS = {
  "kwaivgi/kling-v3.0-pro":       0.140,
  "kwaivgi/kling-v3.0-std":       0.084,
  "kwaivgi/kling-v3.0-4k":        0.250,
  "kwaivgi/kling-v2.6-pro":       0.120,
  "kwaivgi/kling-v2.6-std":       0.070,
  "kwaivgi/kling-v2.5-turbo-pro": 0.100,
  "kwaivgi/kling-v2.5-turbo-std": 0.060,
  "bytedance/seedance-2.0":       0.100,
  "bytedance/seedance-2.0-fast":  0.075,
};

// ── Node colours ───────────────────────────────────────────────────────────────

const NODE_COLORS = {
  WS_NanaBananaImage: { color: "#1a2b1a", bgcolor: "#253525" },
  WS_SeedreamImage:   { color: "#1a1a2e", bgcolor: "#252540" },
  WS_KlingVideo:      { color: "#2b1a1a", bgcolor: "#3d2525" },
  WS_SeedanceVideo:   { color: "#2b1f0f", bgcolor: "#3d2d10" },
  WS_LoadVideoURL:    { color: "#1a1f2b", bgcolor: "#252d3d" },
};

// ── Badge drawing ──────────────────────────────────────────────────────────────

function drawBadge(node, ctx, text) {
  if (!text) return;
  const pad  = 8;
  const h    = 20;
  ctx.save();
  ctx.font = "bold 11px 'Arial', sans-serif";
  const tw = ctx.measureText(text).width;
  const bw = tw + pad * 2;
  const x  = node.size[0] - bw - 6;
  const y  = -h - 2;

  // Shadow
  ctx.shadowColor   = "rgba(0,0,0,0.5)";
  ctx.shadowBlur    = 4;
  ctx.shadowOffsetY = 2;

  // Pill
  ctx.fillStyle = "#e8920a";
  ctx.beginPath();
  ctx.roundRect(x, y, bw, h, 5);
  ctx.fill();

  ctx.shadowColor = "transparent";

  // Text
  ctx.fillStyle    = "#111";
  ctx.textAlign    = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, x + bw / 2, y + h / 2);
  ctx.restore();
}

function getW(node, name) {
  return node.widgets?.find(w => w.name === name)?.value;
}

// ── Cost computers ─────────────────────────────────────────────────────────────

function nanaBananaCost(node) {
  const model   = getW(node, "model")      ?? "";
  const res     = getW(node, "resolution") ?? "1k";
  const n       = getW(node, "num_images") ?? 1;
  const fullKey = `google/${model}`;
  const unit    = IMAGE_COSTS[fullKey]?.[res] ?? 0;
  const total   = unit * n;
  if (n > 1) return `$${unit.toFixed(3)}/img × ${n} = $${total.toFixed(3)}`;
  return `$${unit.toFixed(3)}/image (${res})`;
}

function seedreamCost(node) {
  const model    = getW(node, "model")       ?? "";
  const preset   = getW(node, "size_preset") ?? "";
  const n        = getW(node, "num_images")  ?? 1;
  const fullKey  = `bytedance/${model}`;
  const mx       = Math.max(...(preset.match(/\d+/g) ?? [0]).map(Number));
  const res      = mx >= 2000 ? "4k" : mx >= 1400 ? "2k" : "1k";
  const unit     = IMAGE_COSTS[fullKey]?.[res] ?? 0;
  const total    = unit * n;
  if (n > 1) return `$${unit.toFixed(3)}/img × ${n} = $${total.toFixed(3)}`;
  return `$${unit.toFixed(3)}/image (${res})`;
}

function klingCost(node) {
  const model    = getW(node, "model")    ?? "";
  const duration = parseInt(getW(node, "duration") ?? "5");
  const hasImage = node.inputs?.find(i => i.name === "start_frame")?.link != null;
  const taskType = hasImage ? "image-to-video" : "text-to-video";
  const rate     = VIDEO_COSTS[`kwaivgi/${model}`] ?? 0;
  const total    = rate * duration;
  return `$${rate.toFixed(3)}/s × ${duration}s = $${total.toFixed(3)}`;
}

function seedanceCost(node) {
  const model    = getW(node, "model")    ?? "";
  const duration = parseInt(getW(node, "duration") ?? "5");
  const turbo    = getW(node, "turbo")    ?? false;
  const rate     = VIDEO_COSTS[`bytedance/${model}`] ?? 0;
  const adjusted = turbo ? rate * 1.2 : rate;
  const total    = adjusted * duration;
  return `$${adjusted.toFixed(3)}/s × ${duration}s = $${total.toFixed(3)}`;
}

// ── Register extension ─────────────────────────────────────────────────────────

const COST_FN = {
  WS_NanaBananaImage: nanaBananaCost,
  WS_SeedreamImage:   seedreamCost,
  WS_KlingVideo:      klingCost,
  WS_SeedanceVideo:   seedanceCost,
};

app.registerExtension({
  name: "WaveSpeedAPI.Nodes",

  async nodeCreated(node) {
    const cls = node.comfyClass;
    if (!NODE_COLORS[cls]) return;

    // Apply colour theme
    const theme = NODE_COLORS[cls];
    node.color   = theme.color;
    node.bgcolor = theme.bgcolor;

    // Attach cost badge drawing
    const costFn = COST_FN[cls];
    if (costFn) {
      const origDraw = node.onDrawForeground?.bind(node);
      node.onDrawForeground = function (ctx) {
        origDraw?.(ctx);
        try {
          const label = costFn(this);
          drawBadge(this, ctx, label);
        } catch (_) {}
      };

      // Redraw on any widget change so badge updates live
      for (const w of node.widgets ?? []) {
        const origCb = w.callback?.bind(w);
        w.callback = function (...args) {
          origCb?.(...args);
          node.setDirtyCanvas(true, false);
        };
      }
    }
  },
});
