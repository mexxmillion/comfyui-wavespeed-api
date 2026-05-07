import io
import json
import os
import time

import requests
import numpy as np
import torch
from PIL import Image


BASE_URL = "https://api.wavespeed.ai"


def get_api_key():
    key = os.environ.get("WAVESPEED_API_KEY")
    if key:
        return key

    for config_path in [
        os.path.join(os.path.dirname(__file__), "config.json"),
        os.path.join(os.path.dirname(__file__), "..", "wavespeed-comfyui", "config.json"),
    ]:
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    data = json.load(f)
                    key = data.get("api_key") or data.get("wavespeed")
                    if key:
                        return key
            except Exception:
                pass

    # Parse ComfyUI root .env
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        k, v = line.split("=", 1)
                        if k.strip() in ("WAVESPEED_API_KEY", "wavespeed"):
                            return v.strip().strip("\"'")
        except Exception:
            pass

    return None


def _headers(api_key):
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def submit(model_path: str, payload: dict, api_key: str) -> str:
    url = f"{BASE_URL}/api/v3/{model_path}"
    resp = requests.post(url, headers=_headers(api_key), json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"WaveSpeed API error: {data.get('message', data)}")
    task_id = data["data"].get("id")
    if not task_id:
        raise RuntimeError("No task ID in response")
    return task_id


def poll(task_id: str, api_key: str, timeout: int = 600, interval: int = 3) -> list:
    url = f"{BASE_URL}/api/v2/predictions/{task_id}/result"
    headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 200:
            raise RuntimeError(f"Poll error: {data.get('message')}")
        result = data["data"]
        status = result.get("status")
        if status == "completed":
            return result.get("outputs", [])
        if status == "failed":
            raise RuntimeError(f"Task failed: {result.get('error', 'unknown')}")
        time.sleep(interval)
    raise RuntimeError(f"Task timed out after {timeout}s")


def upload_image(pil_image: Image.Image, api_key: str) -> str:
    url = f"{BASE_URL}/api/v2/media/upload/binary"
    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    buf.seek(0)
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("image.png", buf, "image/png")},
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"Upload failed: {data.get('message')}")
    return data["data"]["download_url"]


def upload_video_path(video_path: str, api_key: str) -> str:
    """Upload a local mp4 file to WaveSpeed media storage and return the public URL."""
    url = f"{BASE_URL}/api/v2/media/upload/binary"
    with open(video_path, "rb") as f:
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": ("video.mp4", f, "video/mp4")},
            timeout=600,
        )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"Video upload failed: {data.get('message')}")
    return data["data"]["download_url"]


def video_input_to_path(video) -> str:
    """Convert a ComfyUI VIDEO input (VideoFromFile or path string) to a local mp4 path.
    If the source is not already an mp4 on disk, save it to a temp mp4 first."""
    import tempfile
    # Plain string path
    if isinstance(video, str):
        return video
    # VideoFromFile-like object: try common attributes
    for attr in ("_file", "file", "path", "filepath"):
        val = getattr(video, attr, None)
        if isinstance(val, str) and os.path.exists(val):
            return val
    # Fallback: use save_to() to write a temp mp4
    if hasattr(video, "save_to"):
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.close()
        try:
            try:
                from comfy_api.latest._util import VideoContainer
                video.save_to(tmp.name, format=VideoContainer.MP4)
            except Exception:
                video.save_to(tmp.name)
            return tmp.name
        except Exception as e:
            raise RuntimeError(f"Failed to materialize video to file: {e}")
    raise RuntimeError(f"Unsupported video input type: {type(video)}")


def tensor_to_pil(image_tensor) -> Image.Image:
    # ComfyUI IMAGE: [B, H, W, C] float32 0-1. Returns the FIRST image only.
    if image_tensor.dim() == 4:
        image_tensor = image_tensor[0]
    arr = (image_tensor.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def tensor_batch_to_pils(image_tensor) -> list:
    """Convert a ComfyUI IMAGE tensor (possibly batched) into a list of PIL Images."""
    if image_tensor is None:
        return []
    if image_tensor.dim() == 3:
        image_tensor = image_tensor.unsqueeze(0)
    pils = []
    for i in range(image_tensor.shape[0]):
        arr = (image_tensor[i].cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
        pils.append(Image.fromarray(arr, "RGB"))
    return pils


def url_to_tensor(url: str):
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)  # [1, H, W, C]


def urls_to_tensor(urls: list):
    tensors = [url_to_tensor(u) for u in urls]
    return torch.cat(tensors, dim=0)  # [N, H, W, C]
