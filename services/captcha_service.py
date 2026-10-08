import io
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CHARACTERS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"

def _apply_advanced_warp(image: Image.Image) -> Image.Image:
    """اعمال اعوجاج و پیچش سینوسی دو محوره بر روی تصویر"""
    width, height = image.size
    distorted = Image.new("RGB", (width, height), (242, 244, 248))
    pixels_in = image.load()
    pixels_out = distorted.load()

    amp_x = random.uniform(3.5, 6.0)
    freq_x = random.uniform(0.04, 0.07)
    phase_x = random.uniform(0, 2 * math.pi)

    amp_y = random.uniform(3.0, 5.0)
    freq_y = random.uniform(0.03, 0.06)
    phase_y = random.uniform(0, 2 * math.pi)

    for y in range(height):
        for x in range(width):
            src_x = int(x + amp_x * math.sin(freq_x * y + phase_x))
            src_y = int(y + amp_y * math.cos(freq_y * x + phase_y))

            if 0 <= src_x < width and 0 <= src_y < height:
                pixels_out[x, y] = pixels_in[src_x, src_y]
            else:
                pixels_out[x, y] = (242, 244, 248)

    return distorted


def generate_hard_captcha(length: int = 5) -> tuple[str, bytes]:
    """تولید کد کپچا همراه با تصویر با امنیت بالا (الگوبرداری از Senfi)"""
    code = "".join(random.choices(CHARACTERS, k=length))
    width, height = 260, 95

    base = Image.new("RGB", (width, height), color=(245, 247, 250))
    draw = ImageDraw.Draw(base)

    for x in range(0, width, random.randint(18, 25)):
        draw.line([(x, 0), (x + random.randint(-15, 15), height)], fill=(215, 222, 230), width=1)
    for y in range(0, height, random.randint(15, 20)):
        draw.line([(0, y), (width, y + random.randint(-10, 10))], fill=(215, 222, 230), width=1)

    try:
        font = ImageFont.load_default(size=40)
    except Exception:
        font = ImageFont.load_default()

    char_spacing = (width - 50) // length
    for i, char in enumerate(code):
        char_canvas = Image.new("RGBA", (75, 75), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_canvas)

        char_color = (
            random.randint(10, 90),
            random.randint(10, 90),
            random.randint(30, 130),
            255
        )
        char_draw.text((18, 10), char, fill=char_color, font=font)

        rot = random.uniform(-35, 35)
        rotated_char = char_canvas.rotate(rot, resample=Image.Resampling.BILINEAR, expand=0)

        paste_x = 18 + i * char_spacing + random.randint(-4, 4)
        paste_y = 10 + random.randint(-6, 6)
        base.paste(rotated_char, (paste_x, paste_y), rotated_char)

    for _ in range(3):
        color = (random.randint(60, 140), random.randint(60, 140), random.randint(60, 140))
        points = []
        phase = random.uniform(0, math.pi)
        amp = random.uniform(10, 20)
        base_y = random.randint(25, 70)
        for x in range(0, width, 8):
            y = int(base_y + amp * math.sin(x * 0.03 + phase))
            points.append((x, y))
        draw.line(points, fill=color, width=2)

    for _ in range(300):
        xy = (random.randint(0, width - 1), random.randint(0, height - 1))
        color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        draw.point(xy, fill=color)

    warped = _apply_advanced_warp(base)
    final_img = warped.filter(ImageFilter.SMOOTH_MORE)

    buf = io.BytesIO()
    final_img.save(buf, format="PNG")
    return code, buf.getvalue()
