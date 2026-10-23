import io
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CHARACTERS = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _apply_advanced_warp(image: Image.Image, amp_scale: float = 1.0) -> Image.Image:
    """Apply dual-axis sinusoidal distortion warp to captcha image."""
    width, height = image.size
    distorted = Image.new("RGB", (width, height), (242, 244, 248))
    pixels_in = image.load()
    pixels_out = distorted.load()

    amp_x = random.uniform(3.5, 6.0) * amp_scale
    freq_x = random.uniform(0.04, 0.07)
    phase_x = random.uniform(0, 2 * math.pi)

    amp_y = random.uniform(3.0, 5.0) * amp_scale
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


def generate_captcha(difficulty: int = 3, length: int = 5) -> tuple[str, bytes]:
    """
    Generate dynamic image captcha with 5 difficulty levels and custom length (4-10).
    Difficulty levels:
        1: Very Easy (Clean background, no noise, minimal rotation, zero warp)
        2: Easy (Subtle grid, 1 wave line, 40 dots, gentle rotation)
        3: Medium (Default - Balanced grid, 2 lines, 120 dots, light warp)
        4: Hard (Dense grid, 3 lines, 250 dots, strong rotation, noticeable warp)
        5: Very Hard (Complex grid, 4 lines, 400 dots, aggressive rotation, heavy warp)
    """
    difficulty = max(1, min(5, int(difficulty)))
    length = max(4, min(10, int(length)))

    code = "".join(random.choices(CHARACTERS, k=length))
    width = max(260, 40 + length * 36)
    height = 95

    base = Image.new("RGB", (width, height), color=(245, 247, 250))
    draw = ImageDraw.Draw(base)

    # 1. Background Grid Lines based on difficulty
    if difficulty >= 2:
        grid_step_x = 35 if difficulty == 2 else (22 if difficulty <= 3 else 16)
        grid_step_y = 30 if difficulty == 2 else (18 if difficulty <= 3 else 14)
        for x in range(0, width, grid_step_x):
            draw.line([(x, 0), (x + random.randint(-8, 8), height)], fill=(225, 230, 236), width=1)
        for y in range(0, height, grid_step_y):
            draw.line([(0, y), (width, y + random.randint(-8, 8))], fill=(225, 230, 236), width=1)

    # Font sizing
    font_size = 42 if length <= 5 else (36 if length <= 7 else 32)
    try:
        font = ImageFont.load_default(size=font_size)
    except Exception:
        font = ImageFont.load_default()

    # 2. Render and Rotate Characters
    char_spacing = (width - 40) // length
    rot_limits = {
        1: 6,
        2: 14,
        3: 22,
        4: 32,
        5: 40,
    }
    max_rot = rot_limits.get(difficulty, 22)

    for i, char in enumerate(code):
        char_canvas = Image.new("RGBA", (75, 75), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_canvas)

        if difficulty == 1:
            char_color = (20, 25, 80, 255)
        else:
            char_color = (
                random.randint(10, 90),
                random.randint(10, 90),
                random.randint(30, 130),
                255
            )

        char_draw.text((16, 8), char, fill=char_color, font=font)

        rot = random.uniform(-max_rot, max_rot) if max_rot > 0 else 0
        rotated_char = char_canvas.rotate(rot, resample=Image.Resampling.BILINEAR, expand=0)

        jitter = 0 if difficulty == 1 else random.randint(-3, 3)
        paste_x = 15 + i * char_spacing + jitter
        paste_y = 10 + jitter
        base.paste(rotated_char, (paste_x, paste_y), rotated_char)

    # 3. Curved Sine Wave Lines
    line_counts = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}
    num_lines = line_counts.get(difficulty, 2)
    for _ in range(num_lines):
        color = (random.randint(60, 140), random.randint(60, 140), random.randint(60, 140))
        points = []
        phase = random.uniform(0, math.pi)
        amp = random.uniform(8, 18)
        base_y = random.randint(25, 70)
        for x in range(0, width, 8):
            y = int(base_y + amp * math.sin(x * 0.03 + phase))
            points.append((x, y))
        draw.line(points, fill=color, width=2)

    # 4. Noise Dots
    dot_counts = {1: 0, 2: 40, 3: 120, 4: 250, 5: 400}
    num_dots = dot_counts.get(difficulty, 120)
    for _ in range(num_dots):
        xy = (random.randint(0, width - 1), random.randint(0, height - 1))
        color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
        draw.point(xy, fill=color)

    # 5. Sinusoidal Distortion Warp
    if difficulty >= 3:
        amp_scale = 0.5 if difficulty == 3 else (0.85 if difficulty == 4 else 1.2)
        warped = _apply_advanced_warp(base, amp_scale=amp_scale)
        final_img = warped.filter(ImageFilter.SMOOTH_MORE)
    else:
        final_img = base

    buf = io.BytesIO()
    final_img.save(buf, format="PNG")
    return code, buf.getvalue()


# Backward compatibility alias
def generate_hard_captcha(length: int = 5) -> tuple[str, bytes]:
    return generate_captcha(difficulty=3, length=length)
