"""Static workspace templates and their player and timeline rectangles."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageOps

PRESETS = ("cut", "composite", "color")
PRESET_DIR = Path(__file__).resolve().parents[1] / "assets" / "workspaces"
LOCAL_PROFILE = Path.home() / ".config" / "swarm-video-skill" / "workspace.json"


def select_workspace(template, image, layout):
    """Explicit options override the optional per-user default profile."""
    if image:
        if not layout:
            raise ValueError("A custom workspace image needs --layout with player and timeline rectangles.")
        return "custom", image, json.loads(layout.read_text(encoding="utf-8-sig"))

    if template is None and layout is None and LOCAL_PROFILE.is_file():
        profile = json.loads(LOCAL_PROFILE.read_text(encoding="utf-8-sig"))
        image = LOCAL_PROFILE.parent / profile["image"]
        return "local", image, profile["layout"]

    name = template or "cut"
    layout_file = layout or PRESET_DIR / f"{name}.json"
    return name, PRESET_DIR / f"{name}.png", json.loads(layout_file.read_text(encoding="utf-8-sig"))


def load_workspace(path):
    with Image.open(path) as image:
        background = ImageOps.exif_transpose(image).convert("RGB")
    width, height = background.size
    if width < 640 or height < 360:
        raise ValueError("The workspace image must be at least 640x360.")
    if width % 2 or height % 2:
        canvas = Image.new("RGB", (width + width % 2, height + height % 2), "#101619")
        canvas.paste(background)
        background = canvas
    return background


def pixel_box(rect, width, height):
    """Round player edges to even pixels for YUV420 compositing."""
    def even(value):
        return 2 * round(value / 2)

    x = even(rect["x"] * width)
    y = even(rect["y"] * height)
    right = even((rect["x"] + rect["width"]) * width)
    bottom = even((rect["y"] + rect["height"]) * height)
    return x, y, right - x, bottom - y


def player_filter(box):
    _, _, width, height = box
    return (
        "scale=w=max(2\\,trunc(iw*sar/2)*2):h=ih,setsar=1,"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x10141a,setsar=1"
    )
