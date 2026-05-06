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
    """Nano Banana 2/Pro. Connect any of image_1..image_5 to switch to multi-ref edit mode
    (Nano Banana 2 supports up to 5 consistent characters in one call).
    Each output costs full price; multi-ref input is ONE call, ONE cost."""
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "cost")

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
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
                "image_5": ("IMAGE",),
            },
        }

    def generate(self, prompt, model, resolution, aspect_ratio, num_images,
                 seed, output_format,
                 image_1=None, image_2=None, image_3=None, image_4=None, image_5=None):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found. Add it to .env as wavespeed= or WAVESPEED_API_KEY=")

        # Collect reference images (any subset of the 5 inputs)
        ref_tensors = [t for t in (image_1, image_2, image_3, image_4, image_5) if t is not None]

        # Upload references ONCE, reuse URLs across all variations
        ref_urls = []
        for tensor in ref_tensors:
            pil = api.tensor_to_pil(tensor)
            ref_urls.append(api.upload_image(pil, key))

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
    """OpenAI GPT Image 2 — text-to-image (no image input) or edit (one+ image inputs).
    Up to 4 reference images can be supplied to the edit endpoint."""
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "cost")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":       ("STRING", {"multiline": True, "default": ""}),
                "quality":      (GPT_QUALITIES,),
                "resolution":   (GPT_RESOLUTIONS,),
                "aspect_ratio": (ASPECT_RATIOS,),
                "num_images":   ("INT", {"default": 1, "min": 1, "max": 4, "step": 1}),
                "seed":         ("INT", {"default": -1, "min": -1, "max": 2**31 - 1}),
            },
            "optional": {
                "image_1": ("IMAGE",),
                "image_2": ("IMAGE",),
                "image_3": ("IMAGE",),
                "image_4": ("IMAGE",),
            },
        }

    def generate(self, prompt, quality, resolution, aspect_ratio, num_images, seed,
                 image_1=None, image_2=None, image_3=None, image_4=None):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found.")

        # Collect any provided reference images
        ref_imgs = [t for t in (image_1, image_2, image_3, image_4) if t is not None]

        # Upload references once (reuse URLs across all num_images)
        ref_urls = []
        if ref_imgs:
            for tensor in ref_imgs:
                pil = api.tensor_to_pil(tensor)
                ref_urls.append(api.upload_image(pil, key))

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
