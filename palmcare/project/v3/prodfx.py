"""Premium product finishing for the real cutouts: removes the dark office fringe, lifts the
dim phone exposure to studio white, adds a glossy vertical specular band, soft rim light and bloom."""
import numpy as np
from PIL import Image, ImageChops, ImageFilter


def clean_edges(img, erode=3, feather=1.6):
    """Shave the dark fringe left from the original background and feather the edge."""
    a = img.split()[-1]
    a = a.filter(ImageFilter.MinFilter(erode * 2 + 1)).filter(ImageFilter.GaussianBlur(feather))
    rgb = img.convert("RGB")
    # pull colour from inside the object outwards so semi-transparent edge pixels are not dark
    inner = rgb.filter(ImageFilter.MaxFilter(5))
    edge = ImageChops.subtract(img.split()[-1], a.filter(ImageFilter.MinFilter(9)))
    rgb = Image.composite(inner, rgb, edge)
    out = rgb.convert("RGBA")
    out.putalpha(a)
    return out


def studio_exposure(img, white=246.0):
    """Map the bright plastic to clean studio white and neutralise the warm/grey office cast."""
    a = np.asarray(img).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    m = al > 200
    lum = rgb.mean(axis=2)
    p95 = np.percentile(lum[m], 95)
    gain = white / max(p95, 1)
    bright = m & (lum > np.percentile(lum[m], 60))
    wb = rgb[bright].mean(axis=0)
    wb = wb.mean() / wb  # neutralise the cast of the white plastic
    rgb = rgb * gain * wb[None, None, :]
    # gentle S-curve for crisp, premium contrast
    x = np.clip(rgb / 255, 0, 1)
    x = x + 0.10 * np.sin(np.pi * x) * (x - 0.5) * 2
    return Image.fromarray(np.dstack([np.clip(x * 255, 0, 255), al]).astype(np.uint8), "RGBA")


def specular(img, pos=0.30, width=0.07, strength=0.55, soft=0.22, soft_strength=0.18):
    """Glossy vertical highlight band(s) as if a strip softbox reflects in the pack."""
    a = np.asarray(img).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3:] / 255
    w = rgb.shape[1]
    x = np.linspace(0, 1, w, dtype=np.float32)
    band = strength * np.exp(-((x - pos) / width) ** 2) + soft_strength * np.exp(-((x - (1 - pos * 0.6)) / soft) ** 2)
    glow = band[None, :, None] * 255
    rgb = 255 - (255 - rgb) * (255 - glow * al) / 255
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), a[..., 3]]).astype(np.uint8), "RGBA")


def rim(img, strength=0.65, from_right=True):
    al = img.split()[-1]
    edge = np.asarray(ImageChops.subtract(al, al.filter(ImageFilter.MinFilter(11)))).astype(np.float32) / 255
    edge = np.asarray(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255
    w = edge.shape[1]
    side = (np.linspace(0.35, 1, w) if from_right else np.linspace(1, 0.35, w)).astype(np.float32)[None, :]
    a = np.asarray(img).astype(np.float32)
    glow = (edge * side)[..., None] * np.array([255, 244, 226], np.float32) * strength
    a[..., :3] = 255 - (255 - a[..., :3]) * (255 - glow) / 255
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def premium(img, spec_pos=0.30, from_right=True):
    img = clean_edges(img)
    img = studio_exposure(img)
    img = specular(img, pos=spec_pos)
    img = rim(img, from_right=from_right)
    return img.filter(ImageFilter.UnsharpMask(2, 70, 2))


def bloom(arr, threshold=232, radius=26, amount=0.35):
    """Soft highlight bloom on the final frame (float RGB array)."""
    hi = np.clip(arr - threshold, 0, None) * (255 / (255 - threshold))
    b = np.asarray(Image.fromarray(np.clip(hi, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius))).astype(np.float32)
    return 255 - (255 - arr) * (255 - b * amount) / 255
