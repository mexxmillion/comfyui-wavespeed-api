import random
from . import api, pricing

# ── Shared ─────────────────────────────────────────────────────────────────────

def _resolve_seed(seed):
    return random.randint(0, 2**31 - 1) if seed == -1 else seed


# ── Kling Video ────────────────────────────────────────────────────────────────

KLING_VERSIONS = [
    "kling-v3.0-pro",
    "kling-v3.0-std",
    "kling-v3.0-4k",
    "kling-v2.6-pro",
    "kling-v2.6-std",
    "kling-v2.5-turbo-pro",
    "kling-v2.5-turbo-std",
]

KLING_ASPECT_RATIOS = ["16:9", "9:16", "1:1"]
KLING_DURATIONS     = [3, 5, 6, 8, 10, 12, 15]


class WS_KlingVideo:
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "cost")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":          ("STRING", {"multiline": True, "default": ""}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "model":           (KLING_VERSIONS,),
                "aspect_ratio":    (KLING_ASPECT_RATIOS,),
                "duration":        (["5", "10", "3", "6", "8", "12", "15"],),
                "cfg_scale":       ("FLOAT",  {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.05}),
                "seed":            ("INT",    {"default": -1, "min": -1, "max": 2**31 - 1}),
            },
            "optional": {
                "start_frame": ("IMAGE",),
            },
        }

    def generate(self, prompt, negative_prompt, model, aspect_ratio, duration,
                 cfg_scale, seed, start_frame=None):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found.")

        resolved_seed = _resolve_seed(seed)
        duration_int = int(duration)

        if start_frame is not None:
            pil = api.tensor_to_pil(start_frame)
            frame_url = api.upload_image(pil, key)
            task_type = "image-to-video"
            payload = {
                "image":           frame_url,
                "prompt":          prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio":    aspect_ratio,
                "duration":        duration_int,
                "cfg_scale":       cfg_scale,
                "seed":            resolved_seed,
            }
        else:
            task_type = "text-to-video"
            payload = {
                "prompt":          prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio":    aspect_ratio,
                "duration":        duration_int,
                "cfg_scale":       cfg_scale,
                "seed":            resolved_seed,
            }

        endpoint = f"kwaivgi/{model}/{task_type}"
        task_id = api.submit(endpoint, payload, key)
        urls = api.poll(task_id, key)
        if not urls:
            raise RuntimeError("No video URL returned")

        video_url = urls[0]
        full_model = f"kwaivgi/{model}/{task_type}"
        cost_str = pricing.video_cost_str(full_model, duration_int)
        return (video_url, cost_str)


# ── Seedance Video ─────────────────────────────────────────────────────────────

SEEDANCE_MODELS = [
    "seedance-2.0",
    "seedance-2.0-fast",
]

SEEDANCE_RESOLUTIONS = ["1080p", "720p", "480p"]


class WS_SeedanceVideo:
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_url", "cost")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":      ("STRING", {"multiline": True, "default": ""}),
                "model":       (SEEDANCE_MODELS,),
                "resolution":  (SEEDANCE_RESOLUTIONS,),
                "duration":    (["5", "10", "3", "7"],),
                "turbo":       ("BOOLEAN", {"default": False, "label_on": "Turbo", "label_off": "Standard"}),
                "seed":        ("INT",    {"default": -1, "min": -1, "max": 2**31 - 1}),
            },
            "optional": {
                "image": ("IMAGE",),
            },
        }

    def generate(self, prompt, model, resolution, duration, turbo, seed, image=None):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found.")

        resolved_seed = _resolve_seed(seed)
        duration_int = int(duration)
        suffix = "-turbo" if turbo else ""

        if image is not None:
            pil = api.tensor_to_pil(image)
            img_url = api.upload_image(pil, key)
            task_type = f"image-to-video{suffix}"
            payload = {
                "image":      img_url,
                "prompt":     prompt,
                "resolution": resolution,
                "duration":   duration_int,
                "seed":       resolved_seed,
            }
        else:
            task_type = f"text-to-video{suffix}"
            payload = {
                "prompt":     prompt,
                "resolution": resolution,
                "duration":   duration_int,
                "seed":       resolved_seed,
            }

        endpoint = f"bytedance/{model}/{task_type}"
        task_id = api.submit(endpoint, payload, key)
        urls = api.poll(task_id, key)
        if not urls:
            raise RuntimeError("No video URL returned")

        video_url = urls[0]
        full_model = f"bytedance/{model}/{task_type}"
        cost_str = pricing.video_cost_str(full_model, duration_int)
        return (video_url, cost_str)


# ── Load Video URL ─────────────────────────────────────────────────────────────
# Saves a remote video URL to ComfyUI's output dir and returns the filepath.

import os
import urllib.request
import folder_paths  # type: ignore – available at ComfyUI runtime


class WS_LoadVideoURL:
    CATEGORY = "WaveSpeed API"
    FUNCTION = "load"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("video_path",)
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url": ("STRING", {"default": ""}),
                "filename_prefix": ("STRING", {"default": "wavespeed_video"}),
            }
        }

    def load(self, video_url, filename_prefix):
        if not video_url:
            raise RuntimeError("No video URL provided")

        output_dir = folder_paths.get_output_directory()
        ext = ".mp4"
        # find next available filename
        idx = 1
        while True:
            fname = f"{filename_prefix}_{idx:04d}{ext}"
            fpath = os.path.join(output_dir, fname)
            if not os.path.exists(fpath):
                break
            idx += 1

        print(f"[WaveSpeed] Downloading video → {fpath}")
        import requests as _req
        resp = _req.get(video_url, timeout=120, stream=True)
        resp.raise_for_status()
        with open(fpath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)

        print(f"[WaveSpeed] Saved: {fpath}")
        return (fpath,)
