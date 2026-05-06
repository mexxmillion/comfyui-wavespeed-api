# USD costs per generation unit.
# Used both by Python nodes (cost string output) and mirrored in JS (badge display).

# Image: cost per image at each resolution
IMAGE_COSTS = {
    # ── Nano Banana 2 ──────────────────────────────────────────────────────────
    "google/nano-banana-2/text-to-image":  {"1k": 0.07,  "2k": 0.10,  "4k": 0.14},
    "google/nano-banana-2/edit":           {"1k": 0.07,  "2k": 0.10,  "4k": 0.14},
    "google/nano-banana-2/edit-fast":      {"1k": 0.045, "2k": 0.07,  "4k": 0.10},
    # ── Nano Banana Pro ───────────────────────────────────────────────────────
    "google/nano-banana-pro/text-to-image": {"1k": 0.14, "2k": 0.18,  "4k": 0.25},
    "google/nano-banana-pro/edit":          {"1k": 0.14, "2k": 0.18,  "4k": 0.25},
    "google/nano-banana-pro/edit-ultra":    {"1k": 0.15, "2k": 0.21,  "4k": 0.28},
    # ── Seedream 4.5 ──────────────────────────────────────────────────────────
    "bytedance/seedream-v4.5/text-to-image":      {"1k": 0.04,  "2k": 0.055, "4k": 0.08},
    "bytedance/seedream-v4.5/edit":               {"1k": 0.04,  "2k": 0.055, "4k": 0.08},
    "bytedance/seedream-v4.5/edit-sequential":    {"1k": 0.04,  "2k": 0.055, "4k": 0.08},
    # ── Seedream 5.0 Lite ─────────────────────────────────────────────────────
    "bytedance/seedream-v5.0-lite/text-to-image":   {"1k": 0.035, "2k": 0.05, "4k": 0.07},
    "bytedance/seedream-v5.0-lite/edit":            {"1k": 0.035, "2k": 0.05, "4k": 0.07},
    "bytedance/seedream-v5.0-lite/edit-sequential": {"1k": 0.035, "2k": 0.05, "4k": 0.07},
}

# GPT Image 2: cost depends on quality AND resolution (and edit costs more at "low").
# Indexed as (endpoint -> quality -> resolution -> $).
GPT_IMAGE_COSTS = {
    "openai/gpt-image-2/text-to-image": {
        "low":    {"1k": 0.010, "2k": 0.020, "4k": 0.030},
        "medium": {"1k": 0.060, "2k": 0.120, "4k": 0.180},
        "high":   {"1k": 0.220, "2k": 0.440, "4k": 0.660},
    },
    "openai/gpt-image-2/edit": {
        "low":    {"1k": 0.030, "2k": 0.060, "4k": 0.090},
        "medium": {"1k": 0.060, "2k": 0.120, "4k": 0.180},
        "high":   {"1k": 0.220, "2k": 0.440, "4k": 0.660},
    },
}

# Video: cost per second of output video
VIDEO_COSTS_PER_SEC = {
    # ── Seedance 2.0 ──────────────────────────────────────────────────────────
    "bytedance/seedance-2.0/text-to-video":        0.10,
    "bytedance/seedance-2.0/image-to-video":       0.10,
    "bytedance/seedance-2.0/text-to-video-turbo":  0.105,
    "bytedance/seedance-2.0/image-to-video-turbo": 0.105,
    "bytedance/seedance-2.0/video-edit":           0.125,
    "bytedance/seedance-2.0/video-edit-turbo":     0.143,
    # ── Seedance 2.0 Fast ─────────────────────────────────────────────────────
    "bytedance/seedance-2.0-fast/text-to-video":        0.075,
    "bytedance/seedance-2.0-fast/image-to-video":       0.075,
    "bytedance/seedance-2.0-fast/text-to-video-turbo":  0.09,
    "bytedance/seedance-2.0-fast/image-to-video-turbo": 0.09,
    "bytedance/seedance-2.0-fast/video-edit":           0.098,
    "bytedance/seedance-2.0-fast/video-edit-turbo":     0.128,
    # ── Kling v3.0 ────────────────────────────────────────────────────────────
    "kwaivgi/kling-v3.0-std/text-to-video":   0.084,
    "kwaivgi/kling-v3.0-std/image-to-video":  0.084,
    "kwaivgi/kling-v3.0-pro/text-to-video":   0.140,
    "kwaivgi/kling-v3.0-pro/image-to-video":  0.140,
    "kwaivgi/kling-v3.0-4k/text-to-video":    0.250,
    "kwaivgi/kling-v3.0-4k/image-to-video":   0.250,
    # ── Kling v2.6 ────────────────────────────────────────────────────────────
    "kwaivgi/kling-v2.6-std/text-to-video":   0.070,
    "kwaivgi/kling-v2.6-std/image-to-video":  0.070,
    "kwaivgi/kling-v2.6-pro/text-to-video":   0.120,
    "kwaivgi/kling-v2.6-pro/image-to-video":  0.120,
    # ── Kling v2.5 Turbo ──────────────────────────────────────────────────────
    "kwaivgi/kling-v2.5-turbo-std/image-to-video":  0.060,
    "kwaivgi/kling-v2.5-turbo-pro/text-to-video":   0.100,
    "kwaivgi/kling-v2.5-turbo-pro/image-to-video":  0.100,
    # ── Kling Motion Control ──────────────────────────────────────────────────
    # Billed per second (some variants round to 3-second chunks server-side).
    "kwaivgi/kling-v2.6-std/motion-control":  0.070,
    "kwaivgi/kling-v2.6-pro/motion-control":  0.112,
    "kwaivgi/kling-v3.0-std/motion-control":  0.126,
    "kwaivgi/kling-v3.0-pro/motion-control":  0.200,  # estimate (no public rate)
}


def image_cost_str(model_path: str, resolution: str, num_images: int = 1) -> str:
    res_costs = IMAGE_COSTS.get(model_path, {})
    unit = res_costs.get(resolution, 0.0)
    total = unit * num_images
    if num_images > 1:
        return f"${unit:.3f}/img × {num_images} = ${total:.3f}"
    return f"${unit:.3f}/image ({resolution})"


def video_cost_str(model_path: str, duration_sec: int) -> str:
    rate = VIDEO_COSTS_PER_SEC.get(model_path, 0.0)
    total = rate * duration_sec
    return f"${rate:.3f}/s × {duration_sec}s = ${total:.3f}"


def gpt_image_cost_str(endpoint: str, quality: str, resolution: str, num_images: int = 1) -> str:
    unit = GPT_IMAGE_COSTS.get(endpoint, {}).get(quality, {}).get(resolution, 0.0)
    total = unit * num_images
    if num_images > 1:
        return f"${unit:.3f}/img × {num_images} = ${total:.3f}  ({quality} {resolution})"
    return f"${unit:.3f}/image  ({quality} {resolution})"
