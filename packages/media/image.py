"""Image making with local PIL — no keys. (AI image generation needs
a local model on the user's PC or an API key; hooks in docs/media.md.)"""
from PIL import Image, ImageDraw, ImageFont


def _font(size: int):
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_poster(text: str, out: str, size: tuple = (720, 1280), bg: str = "#111827", fg: str = "white") -> str:
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    font = _font(56)
    # simple word wrap
    words, lines, cur = text.split(), [], ""
    for w in words:
        if d.textlength(cur + " " + w, font=font) > size[0] - 80 and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    y = size[1] // 2 - len(lines) * 35
    for ln in lines:
        d.text(((size[0] - d.textlength(ln, font=font)) / 2, y), ln, fill=fg, font=font)
        y += 70
    img.save(out)
    return f"made {out}"


def resize_image(src: str, out: str, size: tuple = (720, 1280)) -> str:
    img = Image.open(src).convert("RGB")
    img.thumbnail(size)
    canvas = Image.new("RGB", size, "black")
    canvas.paste(img, ((size[0] - img.width) // 2, (size[1] - img.height) // 2))
    canvas.save(out)
    return f"made {out}"


def make_thumbnail(text: str, out: str) -> str:
    return make_poster(text, out, size=(1280, 720), bg="#7f1d1d")
