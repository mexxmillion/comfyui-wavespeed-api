import os
import random
import time

import requests
import folder_paths  # type: ignore - provided by ComfyUI runtime

from . import api, pricing


# ── Shared ─────────────────────────────────────────────────────────────────────

def _resolve_seed(seed):
    return random.randint(0, 2**31 - 1) if seed == -1 else seed


def _download_video(url: str, prefix: str = "wavespeed") -> tuple[str, str, str]:
    """Download a video URL into ComfyUI's output dir.
    Returns (full_path, filename, subfolder)."""
    out_dir = folder_paths.get_output_directory()
    subfolder = "wavespeed"
    target_dir = os.path.join(out_dir, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    timestamp = int(time.time() * 1000)
    filename = f"{prefix}_{timestamp}.mp4"
    full_path = os.path.join(target_dir, filename)

    print(f"[WaveSpeed] Downloading video → {full_path}")
    resp = requests.get(url, stream=True, timeout=300)
    resp.raise_for_status()
    with open(full_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
    print(f"[WaveSpeed] Saved video ({os.path.getsize(full_path) / 1024 / 1024:.1f} MB)")
    return full_path, filename, subfolder


def _wrap_video(filepath: str):
    """Wrap a path as a ComfyUI VIDEO object if available, else None."""
    try:
        from comfy_api.input_impl import VideoFromFile
        return VideoFromFile(filepath)
    except Exception as e:
        print(f"[WaveSpeed] VideoFromFile unavailable: {e}")
        return None


def _video_node_output(filepath: str, filename: str, subfolder: str,
                       cost_str: str, url: str):
    """Return the standard (ui+result) dict for a video-producing node."""
    video_obj = _wrap_video(filepath)
    return {
        "ui": {
            "images": [{
                "filename": filename,
                "subfolder": subfolder,
                "type": "output",
            }]
        },
        "result": (video_obj, filepath, cost_str, url),
    }


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


class WS_KlingVideo:
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("VIDEO", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("video", "video_path", "cost", "url")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":          ("STRING", {"multiline": True, "default": ""}),
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "model":           (KLING_VERSIONS,),
                "aspect_ratio":    (KLING_ASPECT_RATIOS,),
                "duration":        (["5", "10", "3", "6", "8", "12", "15"],),
                "cfg_scale":       ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.05}),
                "seed":            ("INT",   {"default": -1, "min": -1, "max": 2**31 - 1}),
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
        full_path, filename, subfolder = _download_video(video_url, prefix=f"kling_{model.replace('.', '_')}")
        cost_str = pricing.video_cost_str(f"kwaivgi/{model}/{task_type}", duration_int)

        return _video_node_output(full_path, filename, subfolder, cost_str, video_url)


# ── Seedance Video ─────────────────────────────────────────────────────────────

SEEDANCE_MODELS = ["seedance-2.0", "seedance-2.0-fast"]
SEEDANCE_RESOLUTIONS = ["1080p", "720p", "480p"]


class WS_SeedanceVideo:
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("VIDEO", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("video", "video_path", "cost", "url")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt":     ("STRING", {"multiline": True, "default": ""}),
                "model":      (SEEDANCE_MODELS,),
                "resolution": (SEEDANCE_RESOLUTIONS,),
                "duration":   (["5", "10", "3", "7"],),
                "turbo":      ("BOOLEAN", {"default": False, "label_on": "Turbo", "label_off": "Standard"}),
                "seed":       ("INT",     {"default": -1, "min": -1, "max": 2**31 - 1}),
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
        full_path, filename, subfolder = _download_video(video_url, prefix=f"seedance_{model.replace('.', '_')}")
        cost_str = pricing.video_cost_str(f"bytedance/{model}/{task_type}", duration_int)

        return _video_node_output(full_path, filename, subfolder, cost_str, video_url)


# ── Kling Motion Control ───────────────────────────────────────────────────────

KLING_MOTION_MODELS = [
    "kling-v2.6-std",
    "kling-v2.6-pro",
    "kling-v3.0-std",
    "kling-v3.0-pro",
]

KLING_MOTION_ORIENTATIONS = ["front", "side", "back"]


class WS_KlingMotionControl:
    """Transfer motion from a driving video onto a character image (Kling motion-control)."""
    CATEGORY = "WaveSpeed API"
    FUNCTION = "generate"
    RETURN_TYPES = ("VIDEO", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("video", "video_path", "cost", "url")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_image":      ("IMAGE",),
                "motion_video":         ("VIDEO",),
                "model":                (KLING_MOTION_MODELS,),
                "character_orientation": (KLING_MOTION_ORIENTATIONS,),
                "duration":             ("INT", {"default": 5, "min": 3, "max": 30, "step": 1,
                                                  "tooltip": "Estimated output length in seconds — used for cost display only; actual length is set by motion video"}),
                "keep_original_sound":  ("BOOLEAN", {"default": True}),
                "prompt":               ("STRING", {"multiline": True, "default": ""}),
                "negative_prompt":      ("STRING", {"multiline": True, "default": ""}),
            },
        }

    def generate(self, character_image, motion_video, model, character_orientation,
                 duration, keep_original_sound, prompt, negative_prompt):
        key = api.get_api_key()
        if not key:
            raise RuntimeError("No WaveSpeed API key found.")

        # Upload character image
        pil = api.tensor_to_pil(character_image)
        image_url = api.upload_image(pil, key)

        # Upload motion video
        video_path_local = api.video_input_to_path(motion_video)
        print(f"[WaveSpeed] Uploading motion video: {video_path_local}")
        video_url_in = api.upload_video_path(video_path_local, key)

        endpoint = f"kwaivgi/{model}/motion-control"
        payload = {
            "image":                 image_url,
            "video":                 video_url_in,
            "character_orientation": character_orientation,
            "keep_original_sound":   keep_original_sound,
        }
        if prompt:
            payload["prompt"] = prompt
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        task_id = api.submit(endpoint, payload, key)
        urls = api.poll(task_id, key, timeout=900)
        if not urls:
            raise RuntimeError("No video URL returned")

        out_url = urls[0]
        full_path, filename, subfolder = _download_video(
            out_url, prefix=f"klingmotion_{model.replace('.', '_')}"
        )
        cost_str = pricing.video_cost_str(endpoint, int(duration))
        return _video_node_output(full_path, filename, subfolder, cost_str, out_url)


# ── Load Video URL (kept for manual use / chaining) ────────────────────────────

class WS_LoadVideoURL:
    CATEGORY = "WaveSpeed API"
    FUNCTION = "load"
    RETURN_TYPES = ("VIDEO", "STRING")
    RETURN_NAMES = ("video", "video_path")
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_url":       ("STRING", {"default": "", "multiline": False}),
                "filename_prefix": ("STRING", {"default": "wavespeed_video"}),
            }
        }

    def load(self, video_url, filename_prefix):
        if not video_url:
            raise RuntimeError("No video URL provided")

        full_path, filename, subfolder = _download_video(video_url, prefix=filename_prefix)
        video_obj = _wrap_video(full_path)
        return {
            "ui": {
                "images": [{"filename": filename, "subfolder": subfolder, "type": "output"}]
            },
            "result": (video_obj, full_path),
        }
