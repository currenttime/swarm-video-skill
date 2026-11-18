"""Build the original, reusable raster backdrops shipped with the skill."""
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "workspaces"

DESIGNS = {
    "cut": ("CUT ROOM", "Media bin", "Clip properties", "#71dfc3", "#171e24", "#232c33", (396, 125, 1150, 484)),
    "composite": ("LAYER STUDIO", "Composition bin", "Layer controls", "#b6a7ff", "#1b1a25", "#292638", (354, 125, 1072, 484)),
    "color": ("COLOR SUITE", "Shot browser", "Color controls", "#ffbb79", "#201c20", "#302830", (428, 125, 1048, 484)),
}


def rectangle(x, y, width, height):
    return {"x": x / WIDTH, "y": y / HEIGHT, "width": width / WIDTH, "height": height / HEIGHT}


def build(name, design):
    title, library, inspector, accent, panel, raised, (px, py, pw, ph) = design
    image = Image.new("RGB", (WIDTH, HEIGHT), "#11161c")
    draw = ImageDraw.Draw(image)
    def label(x, y, value, size=16, fill="#c8cfd8"):
        draw.text((x, y), value, font=ImageFont.load_default(size=size), fill=fill)

    def tile(x, y, width, height, color=panel, radius=11):
        draw.rounded_rectangle((x, y, x + width, y + height), radius, fill=color, outline="#343d48")

    draw.rectangle((0, 0, 1920, 66), fill="#191f27")
    draw.line((0, 65, 1920, 65), fill="#36404b")
    draw.rounded_rectangle((23, 18, 52, 47), 8, fill=accent)
    draw.line((31, 34, 37, 26, 44, 39), width=3, fill="#161c23")
    label(68, 19, title, 23, "#f0f3f6")
    label(262, 23, "Workspace  /  Sequence 01", 17, "#9fa9b6")
    for i, tab in enumerate(("Library", "Viewer", "Properties")):
        label(1437 + i * 141, 25, tab, 15, accent if i == 1 else "#9da8b6")

    right = px + pw + 20
    left_width = px - 42
    right_width = WIDTH - right - 20
    tile(20, 81, left_width, 575)
    tile(px - 10, 81, pw + 20, 575)
    tile(right, 81, right_width, 575)
    label(38, 97, library, 18, accent)
    label(px + 8, 96, "Sequence preview", 18)
    label(right + 16, 97, inspector, 18, accent)
    draw.rectangle((px, py, px + pw - 1, py + ph - 1), fill="#10141a")
    draw.line((px, 615, px + pw, 615), fill="#303945")
    center = px + pw / 2
    draw.polygon(((center - 5, 625), (center - 5, 644), (center + 10, 634)), fill=accent)
    label(px + 8, 626, "SEQ 01", 13, "#8290a0")
    label(px + pw - 87, 626, "PREVIEW", 13, "#8290a0")

    for i, text in enumerate(("Sequence 01", "Source clip", "Output preview")):
        y = 148 + i * 49
        tile(37, y, left_width - 34, 36, raised, 5)
        draw.rounded_rectangle((48, y + 9, 65, y + 26), 4, fill=accent if i == 0 else "#596673")
        label(78, y + 8, text, 15)
    label(39, 332, "Workspace bin", 14, "#81909f")
    for i in range(4):
        x = 38 + i % 2 * ((left_width - 32) // 2)
        y = 364 + i // 2 * 100
        tw = (left_width - 56) // 2
        tile(x, y, tw, 73, raised, 7)
        draw.line((x + 12, y + 51, x + tw - 13, y + 51), fill="#536273")
        draw.ellipse((x + 13, y + 13, x + 22, y + 22), fill=accent)
        label(x + 31, y + 10, f"Lane {i + 1:02}", 12)

    settings = {
        "cut": ("Frame", "Scale", "Position", "Opacity", "Blend"),
        "composite": ("Transform", "Anchor", "Rotation", "Opacity", "Matte"),
        "color": ("Exposure", "Contrast", "Saturation", "Temperature", "Tint"),
    }[name]
    for i, text in enumerate(settings):
        y = 147 + i * 42
        label(right + 17, y, text, 15)
        start = right + right_width * .40
        end = right + right_width - 26
        draw.line((start, y + 10, end, y + 10), fill="#5f6a76", width=2)
        ratio = [.43, .58, .67, .51, .38][i]
        point = start + (end - start) * ratio
        draw.line((start, y + 10, point, y + 10), fill=accent, width=2)
        draw.ellipse((point - 4, y + 6, point + 4, y + 14), fill=accent)
    label(right + 17, 377, "Sequence monitor", 15, "#9faab8")
    tile(right + 16, 408, right_width - 32, 211, raised, 7)
    plot_left = right + 36
    plot_right = right + right_width - 36
    for j in range(6):
        y = 425 + j * 34
        draw.line((plot_left, y, plot_right, y), fill="#404a57")
    if name == "color":
        for j, tint in enumerate(("#f99486", accent, "#85caf4")):
            points = [(plot_left + i * (plot_right - plot_left) / 16,
                       593 - 9 * i + ((i + j * 2) % 4) * 5 - j * 12) for i in range(17)]
            draw.line(points, fill=tint, width=2)
    else:
        points = [(plot_left + i * (plot_right - plot_left) / 12, 575 - i * 10 + (i % 3) * 9) for i in range(13)]
        draw.line(points, fill=accent, width=3)

    timeline = (0, 670, 1920, 410) if name != "composite" else (0, 670, 1436, 410)
    if name == "composite":
        tile(1456, 676, 444, 380)
        label(1475, 698, "Layer stack", 18, accent)
        for i in range(6):
            tile(1475, 738 + i * 44, 404, 32, raised, 5)
            label(1490, 744 + i * 44, f"Layer {i + 1:02}", 15)
    else:
        draw.rectangle((0, 670, 1920, 1080), fill="#10171b")

    image.save(OUTPUT / f"{name}.png", optimize=True)
    layout = {"player": rectangle(px, py, pw, ph), "timeline": rectangle(*timeline)}
    (OUTPUT / f"{name}.json").write_text(json.dumps(layout, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, design in DESIGNS.items():
        build(name, design)
