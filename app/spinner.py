import io
import math
import random

from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_INDEX = 3  # Noto Sans CJK TC

CANVAS = 512
RADIUS = 230
CENTER = (CANVAS // 2, CANVAS // 2 + 12)
SUPERSAMPLE = 2

FPS = 30
SPIN_SECONDS = 5
FINAL_FRAME_MS = 3000

PALETTE = [
    (239, 71, 111),
    (255, 159, 28),
    (255, 209, 102),
    (6, 214, 160),
    (17, 138, 178),
    (115, 103, 240),
    (199, 125, 255),
    (46, 196, 182),
]


def _slice_colors(count: int) -> list[tuple[int, int, int]]:
    colors = [PALETTE[i % len(PALETTE)] for i in range(count)]
    if count > 1 and colors[-1] == colors[0]:
        colors[-1] = PALETTE[1]
    return colors


def _fit_text(text: str, font: ImageFont.FreeTypeFont, max_width: float) -> str:
    if font.getlength(text) <= max_width:
        return text
    while text and font.getlength(text + "…") > max_width:
        text = text[:-1]
    return text + "…"


def _draw_label(text: str, font: ImageFont.FreeTypeFont, angle: float, *, dim: bool) -> Image.Image:
    stroke = max(1, int(font.size) // 12)
    left, top, right, bottom = (int(v) for v in font.getbbox(text, stroke_width=stroke))
    label = Image.new("RGBA", (right - left, bottom - top))
    ImageDraw.Draw(label).text(
        (-left, -top), text, font=font, fill="white", stroke_width=stroke, stroke_fill="black"
    )
    if dim:
        label.putalpha(label.getchannel("A").point([a // 3 for a in range(256)]))
    return label.rotate(-angle, expand=True, resample=Image.Resampling.BICUBIC)


def _draw_wheel(items: list[str], highlight: int | None = None) -> Image.Image:
    r = RADIUS * SUPERSAMPLE
    wheel = Image.new("RGBA", (r * 2, r * 2))
    draw = ImageDraw.Draw(wheel)
    step = 360 / len(items)

    for idx, color in enumerate(_slice_colors(len(items))):
        dim = highlight is not None and idx != highlight
        # PIL measures angles clockwise from 3 o'clock; slice 0 starts at 12 o'clock.
        start = -90 + idx * step
        draw.pieslice(
            (0, 0, r * 2, r * 2),
            start,
            start + step,
            fill=tuple(c // 3 for c in color) if dim else color,
        )

    draw.ellipse((0, 0, r * 2, r * 2), outline="white", width=4 * SUPERSAMPLE)

    # Labels sit between the hub and the rim, centered at text_radius.
    text_radius, max_width = r * 0.56, r * 0.72
    arc_height = 2 * text_radius * math.sin(math.radians(min(step, 90) / 2))
    font = ImageFont.truetype(
        FONT_PATH,
        int(max(10 * SUPERSAMPLE, min(28 * SUPERSAMPLE, arc_height * 0.6))),
        index=FONT_INDEX,
    )

    for idx, item in enumerate(items):
        mid = -90 + (idx + 0.5) * step
        label = _draw_label(
            _fit_text(item, font, max_width),
            font,
            mid,
            dim=highlight is not None and idx != highlight,
        )
        x = r + text_radius * math.cos(math.radians(mid)) - label.width / 2
        y = r + text_radius * math.sin(math.radians(mid)) - label.height / 2
        wheel.alpha_composite(label, (round(x), round(y)))

    return wheel.resize((RADIUS * 2, RADIUS * 2), Image.Resampling.LANCZOS)


def _draw_overlay() -> Image.Image:
    overlay = Image.new("RGBA", (CANVAS, CANVAS))
    draw = ImageDraw.Draw(overlay)
    cx, cy = CENTER

    hub = 26
    draw.ellipse(
        (cx - hub, cy - hub, cx + hub, cy + hub), fill="white", outline=(40, 40, 40), width=4
    )

    top = cy - RADIUS
    draw.polygon(
        [(cx - 22, top - 26), (cx + 22, top - 26), (cx, top + 22)],
        fill=(230, 57, 70),
        outline="white",
        width=3,
    )
    return overlay


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def render_spin(items: list[str], winner: int) -> io.BytesIO:
    step = 360 / len(items)

    # Rotating the wheel clockwise by θ moves wheel angle a to a + θ, so the pointer (0°)
    # lands on a when θ ≡ -a (mod 360).
    landing = (winner + random.uniform(0.1, 0.9)) * step
    total = 360 * random.randint(5, 7) + (-landing % 360)

    wheel = _draw_wheel(items)
    overlay = _draw_overlay()
    wheel_pos = (CENTER[0] - RADIUS, CENTER[1] - RADIUS)

    def frame(wheel_img: Image.Image, angle: float) -> Image.Image:
        canvas = Image.new("RGBA", (CANVAS, CANVAS))
        canvas.alpha_composite(
            wheel_img.rotate(-angle, resample=Image.Resampling.BICUBIC), wheel_pos
        )
        canvas.alpha_composite(overlay)
        return canvas

    frame_count = FPS * SPIN_SECONDS
    frames = [frame(wheel, total * _ease_out_cubic(n / frame_count)) for n in range(frame_count)]
    frames.append(frame(_draw_wheel(items, highlight=winner), total))
    durations = [1000 // FPS] * frame_count + [FINAL_FRAME_MS]

    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=1,
        quality=80,
    )
    buf.seek(0)
    return buf
