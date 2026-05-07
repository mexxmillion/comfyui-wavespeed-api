import random
from . import api, pricing

# ── Shared helpers ─────────────────────────────────────────────────────────────

ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "4:5", "5:4", "21:9"]

SEEDREAM_SIZES = [
    "1024×1024 (1:1)",
    "1280×720 (16:9)",
    "720×1280 (9:16)",
    "1024×1536 (2:3)",
    "1536×1024 (3:2)",
    "2048×2048 (1:1)",
    "1920×1080 (16:9)",
    "1080×1920 (9:16)",
    "2048×1152 (16:9)",
    "1152×2048 (9:16)",
]

SEEDREAM_SIZE_MAP = {
    "1024×1024 (1:1)":  (1024, 1024),
    "1280×720 (16:9)":  (1280, 720),
    "720×1280 (9:16)":  (720,  1280),
    "1024×1536 (2:3)":  (1024, 1536),
    "1536×1024 (3:2)":  (1536, 1024),
    "2048×2048 (1:1)":  (2048, 2048),
    "1920×1080 (16:9)": (1920, 1080),
    "1080×1920 (9:16)": (1080, 1920),
    "2048×1152 (16:9)": (2048, 1152),
    "1152×2048 (9:16)": (1152, 2048),
}

def _resolve_seed(seed):
    return random.randint(0, 2**31 - 1) if seed == -1 else seed

def _run(model_path, payload, api_key):
    task_id = api.submit(model_path, payload, api_key)
    urls = api.poll(task_id, api_key)
    if not urls:
        raise RuntimeError("No outputs returned")
    return urls


# ── Nano Banana Image ──────────────────────────────────────────────────────────

NANO_MODELS = [
    "nano-banana-pro/edit-ultra",
    "nano-banana-pro/edit",
    "nano-banana-2/edit",
    "nano-banana-2/edit-fast",
]

NANO_MODELS_T2I = [m.replace("/edit-ultra", "/text-to-image")
                    .replace("/edit-fast", "/text-to-image")
                    .replace("/edit", "/text-to-image")
                   for m in NANO_MODELS]


class WS_NanaBananaImage:
    """Nano Banana 2/Pro. Connect a (batched) IMAGE to `images` for multi-ref edit mode.
    Use `Image Batch Multi` (kjnodes) or any node that combines images to send multiple refs.
    NB2 supports up to 8 reference images; NB Pro up to 14.
    Multi-ref input = ONE call, ONE cost. num_images = N separate calls (Nx cost)."""
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images_out", "cost")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":       ("STRING",  {"multiline": True, "default": ""}),
                "model":        (NANO_MODELS,),
                "resolution":   (["1k", "2k", "4k"],),
                "aspect_ratio": (ASPECT_RATIOS,),
                "num_images":   ("INT",    {"default": 1, "min": 1, "max": 8, "step": 1,
                                             "tooltip": "Number of variations — each is a separate API call (Nx cost)"}),
                "seed":         ("INT",    {"default": -1, "min": -1, "max": 2**31 - 1}),
                "output_format":(["png", "jpeg"],),
            },
            "optional": {
                "images": ("IMAGE", {"tooltip": "Reference image(s). Can be a batch — feed multiple refs via Image Batch Multi."}),
            },
        }

    def generate(self, prompt, model, resolution, aspect_ratio, num_images,
                 seed, output_format, images=None):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found. Add it to .env as wavespeed= or WAVESPEED_API_KEY=")

        ref_pils = api.tensor_batch_to_pils(images)
        if "nano-banana-2" in model and len(ref_pils) > 8:
            print(f"[WaveSpeed] WARNING: Nano Banana 2 supports up to 8 reference images; you provided {len(ref_pils)}. The API may reject or truncate.")
        if "nano-banana-pro" in model and len(ref_pils) > 14:
            print(f"[WaveSpeed] WARNING: Nano Banana Pro supports up to 14 reference images; you provided {len(ref_pils)}.")

        # Upload references ONCE, reuse URLs across all variations
        ref_urls = [api.upload_image(p, key) for p in ref_pils]

        is_edit = len(ref_urls) > 0
        if is_edit:
            endpoint = f"google/{model}"
        else:
            t2i_model = (model.replace("/edit-ultra", "/text-to-image")
                              .replace("/edit-fast", "/text-to-image")
                              .replace("/edit", "/text-to-image"))
            endpoint = f"google/{t2i_model}"

        resolved_seed = _resolve_seed(seed)
        all_urls = []
        for _ in range(num_images):
            if is_edit:
                payload = {
                    "images":        ref_urls,
                    "prompt":        prompt,
                    "resolution":    resolution,
                    "output_format": output_format,
                    "seed":          resolved_seed,
                }
            else:
                payload = {
                    "prompt":        prompt,
                    "aspect_ratio":  aspect_ratio,
                    "resolution":    resolution,
                    "output_format": output_format,
                    "seed":          resolved_seed,
                }
            urls = _run(endpoint, payload, key)
            all_urls.extend(urls)
            resolved_seed += 1

        img_tensor = api.urls_to_tensor(all_urls)
        full_model = f"google/{model}"
        cost_str = pricing.image_cost_str(full_model, resolution, num_images)
        return (img_tensor, cost_str)


# ── Seedream Image ─────────────────────────────────────────────────────────────

SEEDREAM_MODELS = [
    "seedream-v5.0-lite/edit",
    "seedream-v5.0-lite/edit-sequential",
    "seedream-v4.5/edit",
    "seedream-v4.5/edit-sequential",
]

def _seedream_res_tag(size_preset: str) -> str:
    w, h = SEEDREAM_SIZE_MAP[size_preset]
    if max(w, h) >= 2000:
        return "4k"
    if max(w, h) >= 1400:
        return "2k"
    return "1k"


class WS_SeedreamImage:
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "cost")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":      ("STRING",       {"multiline": True, "default": ""}),
                "model":       (SEEDREAM_MODELS,),
                "size_preset": (SEEDREAM_SIZES,),
                "num_images":  ("INT",          {"default": 1, "min": 1, "max": 4, "step": 1}),
                "seed":        ("INT",          {"default": 0, "min": 0, "max": 2**31 - 1}),
                "watermark":   ("BOOLEAN",      {"default": False}),
            },
            "optional": {
                "image": ("IMAGE",),
            },
        }

    def generate(self, prompt, model, size_preset, num_images, seed, watermark, image=None):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found.")

        w, h = SEEDREAM_SIZE_MAP[size_preset]

        all_urls = []
        for i in range(num_images):
            if image is not None:
                pil = api.tensor_to_pil(image)
                img_url = api.upload_image(pil, key)
                payload = {
                    "image":     img_url,
                    "prompt":    prompt,
                    "width":     w,
                    "height":    h,
                    "seed":      seed + i,
                    "watermark": watermark,
                }
            else:
                t2i_model = model.replace("/edit-sequential", "/text-to-image").replace("/edit", "/text-to-image")
                model = t2i_model  # use t2i path when no image
                payload = {
                    "prompt":    prompt,
                    "width":     w,
                    "height":    h,
                    "seed":      seed + i,
                    "watermark": watermark,
                }

            endpoint = f"bytedance/{model}"
            urls = _run(endpoint, payload, key)
            all_urls.extend(urls)

        img_tensor = api.urls_to_tensor(all_urls)

        res_tag = _seedream_res_tag(size_preset)
        full_model = f"bytedance/{model}"
        cost_str = pricing.image_cost_str(full_model, res_tag, num_images)
        return (img_tensor, cost_str)


# ── GPT Image 2 ────────────────────────────────────────────────────────────────

GPT_QUALITIES = ["medium", "low", "high"]
GPT_RESOLUTIONS = ["1k", "2k", "4k"]


class WS_GPTImage2:
    """OpenAI GPT Image 2 — text-to-image (no images) or edit (batched IMAGE input).
    Connect multiple refs via Image Batch Multi (kjnodes) for multi-image edit."""
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images_out", "cost")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":       ("STRING", {"multiline": True, "default": ""}),
                "quality":      (GPT_QUALITIES,),
                "resolution":   (GPT_RESOLUTIONS,),
                "aspect_ratio": (ASPECT_RATIOS,),
                "num_images":   ("INT", {"default": 1, "min": 1, "max": 4, "step": 1,
                                          "tooltip": "Number of variations — each is a separate API call (Nx cost)"}),
                "seed":         ("INT", {"default": -1, "min": -1, "max": 2**31 - 1}),
            },
            "optional": {
                "images": ("IMAGE", {"tooltip": "Reference image(s). Can be a batch — feed multiple refs via Image Batch Multi."}),
            },
        }

    def generate(self, prompt, quality, resolution, aspect_ratio, num_images, seed, images=None):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found.")

        ref_pils = api.tensor_batch_to_pils(images)
        ref_urls = [api.upload_image(p, key) for p in ref_pils]

        is_edit = len(ref_urls) > 0
        endpoint = "openai/gpt-image-2/edit" if is_edit else "openai/gpt-image-2/text-to-image"

        resolved_seed = _resolve_seed(seed)
        all_urls = []
        for i in range(num_images):
            payload = {
                "prompt":       prompt,
                "aspect_ratio": aspect_ratio,
                "resolution":   resolution,
                "quality":      quality,
            }
            if is_edit:
                payload["images"] = ref_urls
            urls = _run(endpoint, payload, key)
            all_urls.extend(urls)
            resolved_seed += 1

        img_tensor = api.urls_to_tensor(all_urls)
        cost_str = pricing.gpt_image_cost_str(endpoint, quality, resolution, num_images)
        return (img_tensor, cost_str)
