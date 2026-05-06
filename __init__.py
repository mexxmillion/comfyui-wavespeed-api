import os

from .nodes_image import WS_NanaBananaImage, WS_SeedreamImage, WS_GPTImage2
from .nodes_video import (
    WS_KlingVideo,
    WS_KlingMotionControl,
    WS_SeedanceVideo,
    WS_LoadVideoURL,
)

NODE_CLASS_MAPPINGS = {
    "WS_NanaBananaImage":    WS_NanaBananaImage,
    "WS_SeedreamImage":      WS_SeedreamImage,
    "WS_GPTImage2":          WS_GPTImage2,
    "WS_KlingVideo":         WS_KlingVideo,
    "WS_KlingMotionControl": WS_KlingMotionControl,
    "WS_SeedanceVideo":      WS_SeedanceVideo,
    "WS_LoadVideoURL":       WS_LoadVideoURL,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WS_NanaBananaImage":    "Nano Banana Image (WaveSpeed)",
    "WS_SeedreamImage":      "Seedream Image (WaveSpeed)",
    "WS_GPTImage2":          "GPT Image 2 (WaveSpeed)",
    "WS_KlingVideo":         "Kling Video (WaveSpeed)",
    "WS_KlingMotionControl": "Kling Motion Control (WaveSpeed)",
    "WS_SeedanceVideo":      "Seedance Video (WaveSpeed)",
    "WS_LoadVideoURL":       "Load Video URL (WaveSpeed)",
}

WEB_DIRECTORY = os.path.join(os.path.dirname(__file__), "web")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

print("[WaveSpeed API] Nodes loaded: NanaBanana, Seedream, GPTImage2, Kling, Kling Motion Control, Seedance, LoadVideoURL")
