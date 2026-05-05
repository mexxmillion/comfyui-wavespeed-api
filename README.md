# ComfyUI-WaveSpeed-API

Native ComfyUI nodes for the [WaveSpeed AI](https://wavespeed.ai) API. Pay-per-use access to Nano Banana, Seedream, Kling, and Seedance models — no monthly subscription required.

Designed to feel like native ComfyUI nodes (not a custom panel). Includes a live **gold cost badge** on every node that updates as you change model / resolution / duration.

## Nodes

| Node | Models | Modes |
|---|---|---|
| **Nano Banana Image** | NB Pro (edit, edit-ultra), NB2 (edit, edit-fast) | T2I + I2I |
| **Seedream Image** | v5.0 Lite, v4.5 (edit + sequential) | T2I + I2I |
| **Kling Video** | v3.0 / v2.6 / v2.5-turbo (std + pro) + 4K | T2V + I2V |
| **Seedance Video** | 2.0, 2.0 Fast (+ turbo) | T2V + I2V |
| **Load Video URL** | — | downloads video URL to ComfyUI output dir |

Image nodes return `IMAGE` tensors directly (works with Save Image, Preview Image, etc). Video nodes return a URL string — pipe it into **Load Video URL** to save locally, or use VHS Load Video.

If an `image` input is connected, the node automatically uses the image-to-image (or image-to-video) endpoint. If not, it uses text-to-image (or text-to-video).

## Installation

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/mexxmillion/comfyui-wavespeed-api
cd comfyui-wavespeed-api
pip install -r requirements.txt
```

Restart ComfyUI. Nodes appear under the `WaveSpeed API` category.

## Setting your API key

Get a key at [wavespeed.ai/accesskey](https://wavespeed.ai/accesskey). The plugin looks for it in this order — set it **any one** of these ways:

### Option 1 — `config.json` (recommended)

Inside the plugin folder (`custom_nodes/comfyui-wavespeed-api/`), create `config.json`:

```json
{
  "api_key": "your-wavespeed-api-key-here"
}
```

There's a `config.example.json` you can copy. `config.json` is gitignored.

### Option 2 — Environment variable

```bash
# Linux/Mac
export WAVESPEED_API_KEY="your-key-here"

# Windows (PowerShell)
$env:WAVESPEED_API_KEY = "your-key-here"
```

Set it before launching ComfyUI.

### Option 3 — `.env` file in ComfyUI root

Create `ComfyUI/.env` with either of these lines:

```
WAVESPEED_API_KEY=your-key-here
```
or (lowercase also accepted):
```
wavespeed=your-key-here
```

## Cost badge

The gold pill at the top-right of each node shows the live cost estimate based on your current settings. Pricing data is hardcoded in `pricing.py` (Python) and `web/wavespeed_api.js` (frontend) — pulled from [wavespeed.ai/pricing](https://wavespeed.ai/pricing). Update those two files if WaveSpeed changes prices.

## License

MIT
